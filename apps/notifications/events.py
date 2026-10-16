from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.base.choices import UserRole

from .choices import NotificationKind
from .services import notify


def _when(dt) -> str:
    return timezone.localtime(dt).strftime("%a %d %b %Y, %I:%M %p")


# ---------- bookings ----------

def booking_created(booking):
    notify(
        user=booking.provider.user,
        kind=NotificationKind.BOOKING_CREATED,
        title="New booking request",
        message=(
            f"{booking.customer.get_full_name() or booking.customer.email} booked "
            f"{booking.service.name} for {_when(booking.start_time)}. "
            f"Reference: {booking.reference}. Please confirm or cancel it."
        ),
        related_model="booking", related_id=booking.id,
    )


def booking_confirmed(booking):
    notify(
        user=booking.customer,
        kind=NotificationKind.BOOKING_CONFIRMED,
        title="Your booking is confirmed",
        message=(
            f"{booking.provider.business_name} confirmed your {booking.service.name} "
            f"appointment on {_when(booking.start_time)}. Reference: {booking.reference}."
        ),
        related_model="booking", related_id=booking.id,
    )


def booking_cancelled(booking, cancelled_by):
    recipients = {booking.customer, booking.provider.user}
    recipients.discard(cancelled_by)  # no need to tell the person who did it
    for user in recipients:
        notify(
            user=user,
            kind=NotificationKind.BOOKING_CANCELLED,
            title="Booking cancelled",
            message=(
                f"Booking {booking.reference} for {_when(booking.start_time)} was cancelled."
                + (f" Reason: {booking.cancellation_reason}" if booking.cancellation_reason else "")
            ),
            related_model="booking", related_id=booking.id,
        )


def booking_rescheduled(booking):
    notify(
        user=booking.provider.user,
        kind=NotificationKind.BOOKING_RESCHEDULED,
        title="Booking rescheduled",
        message=(
            f"Booking {booking.reference} was moved to {_when(booking.start_time)}. "
            "Please confirm the new time."
        ),
        related_model="booking", related_id=booking.id,
    )


# ---------- complaints ----------

def complaint_submitted(complaint):
    User = get_user_model()
    admins = User.objects.filter(is_active=True).filter(Q(role=UserRole.ADMIN) | Q(is_staff=True))
    for admin in admins:
        notify(
            user=admin,
            kind=NotificationKind.COMPLAINT_SUBMITTED,
            title="New complaint",
            message=f"{complaint.reference}: {complaint.subject} (booking {complaint.booking.reference}).",
            related_model="complaint", related_id=complaint.id,
        )


def complaint_updated(complaint):
    message = f"Your complaint {complaint.reference} is now {complaint.get_status_display().lower()}."
    if complaint.admin_response:
        message += f" Response: {complaint.admin_response}"
    notify(
        user=complaint.customer,
        kind=NotificationKind.COMPLAINT_UPDATED,
        title="Update on your complaint",
        message=message,
        related_model="complaint", related_id=complaint.id,
    )