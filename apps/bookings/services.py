from datetime import timedelta
from functools import partial  # NEW

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.base.permissions import is_admin
from apps.notifications import events  # NEW
from apps.providers.models import Provider

from .choices import BookingStatus
from .exceptions import BookingConflict, BookingRuleViolation
from .models import Booking
from .selectors import is_within_working_hours

CANCELLATION_CUTOFF_HOURS = getattr(settings, "BOOKING_CANCELLATION_CUTOFF_HOURS", 24)
ACTIVE_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]


# ---------- helpers ----------

def _has_overlap(provider_id, start, end, exclude_id=None) -> bool:
    qs = Booking.objects.filter(
        provider_id=provider_id,
        status__in=ACTIVE_STATUSES,
        start_time__lt=end,
        end_time__gt=start,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def _lock_provider(provider_id):
    # Locking the provider row makes concurrent bookings for the same
    # provider wait their turn, even when the slot is currently empty.
    return Provider.objects.select_for_update().get(pk=provider_id)


def _lock_booking(booking_id) -> Booking:
    return (
        Booking.objects.select_for_update(of=("self",))
        .select_related("provider", "service")
        .get(pk=booking_id)
    )


def _is_booking_provider(user, booking) -> bool:
    return booking.provider.user_id == user.id


def _enforce_cutoff(booking, user):
    """Customers can't change a booking too close to its start time.
    Providers and admins are exempt."""
    if is_admin(user) or _is_booking_provider(user, booking):
        return
    if booking.start_time - timezone.now() < timedelta(hours=CANCELLATION_CUTOFF_HOURS):
        raise BookingRuleViolation(
            f"Bookings can't be changed within {CANCELLATION_CUTOFF_HOURS} hours of the start time."
        )


# ---------- create ----------

def create_booking(*, customer, provider, service, start_time, notes="") -> Booking:
    if not provider.is_active or not service.is_active:
        raise BookingRuleViolation("This provider or service is not available.")
    if service.provider_id != provider.id:
        raise BookingRuleViolation("This service is not offered by the selected provider.")
    if provider.user_id == customer.id:
        raise BookingRuleViolation("You can't book your own service.")
    if start_time <= timezone.now():
        raise BookingRuleViolation("Start time must be in the future.")

    end_time = start_time + timedelta(minutes=service.duration_minutes)

    if not is_within_working_hours(provider, start_time, end_time):
        raise BookingRuleViolation("This time is outside the provider's working hours.")

    try:
        with transaction.atomic():
            _lock_provider(provider.id)
            if _has_overlap(provider.id, start_time, end_time):
                raise BookingConflict()
            booking = Booking.objects.create(  # CHANGED: now stored in a variable
                customer=customer,
                provider=provider,
                service=service,
                start_time=start_time,
                end_time=end_time,
                notes=notes,
            )
            transaction.on_commit(partial(events.booking_created, booking), robust=True)  # NEW
            return booking
    except IntegrityError:
        # The database constraint caught a race the check missed.
        raise BookingConflict()


# ---------- cancel ----------

def cancel_booking(*, booking, cancelled_by, reason="") -> Booking:
    with transaction.atomic():
        booking = _lock_booking(booking.pk)

        if booking.status not in ACTIVE_STATUSES:
            raise BookingRuleViolation(
                f"A {booking.status.lower()} booking can't be cancelled."
            )
        _enforce_cutoff(booking, cancelled_by)

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancelled_by = cancelled_by
        booking.cancellation_reason = reason
        booking.save(
            update_fields=[
                "status", "cancelled_at", "cancelled_by",
                "cancellation_reason", "updated_at",
            ]
        )
        transaction.on_commit(partial(events.booking_cancelled, booking, cancelled_by), robust=True)  # NEW
    return booking


# ---------- reschedule ----------

def reschedule_booking(*, booking, new_start_time, rescheduled_by) -> Booking:
    if new_start_time <= timezone.now():
        raise BookingRuleViolation("New start time must be in the future.")

    try:
        with transaction.atomic():
            # Always lock the provider first, then the booking (avoids deadlocks).
            _lock_provider(booking.provider_id)
            booking = _lock_booking(booking.pk)

            if booking.status not in ACTIVE_STATUSES:
                raise BookingRuleViolation(
                    f"A {booking.status.lower()} booking can't be rescheduled."
                )
            _enforce_cutoff(booking, rescheduled_by)

            new_end_time = new_start_time + timedelta(minutes=booking.service.duration_minutes)

            if not is_within_working_hours(booking.provider, new_start_time, new_end_time):
                raise BookingRuleViolation("This time is outside the provider's working hours.")

            if _has_overlap(booking.provider_id, new_start_time, new_end_time, exclude_id=booking.pk):
                raise BookingConflict()

            booking.start_time = new_start_time
            booking.end_time = new_end_time
            booking.status = BookingStatus.PENDING  # provider must re-confirm
            booking.save(update_fields=["start_time", "end_time", "status", "updated_at"])
            transaction.on_commit(partial(events.booking_rescheduled, booking), robust=True)  # NEW
    except IntegrityError:
        raise BookingConflict()
    return booking


# ---------- confirm ----------

def confirm_booking(*, booking, confirmed_by) -> Booking:
    with transaction.atomic():
        booking = _lock_booking(booking.pk)

        if booking.status != BookingStatus.PENDING:
            raise BookingRuleViolation("Only pending bookings can be confirmed.")
        if booking.start_time <= timezone.now():
            raise BookingRuleViolation("This booking's start time has already passed.")

        booking.status = BookingStatus.CONFIRMED
        booking.save(update_fields=["status", "updated_at"])
        transaction.on_commit(partial(events.booking_confirmed, booking), robust=True)  # NEW
    return booking