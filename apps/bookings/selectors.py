from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.base.permissions import is_admin
from apps.providers.models import WorkingHours  # not built yet

from .choices import BookingStatus
from .models import Booking

SLOT_INTERVAL_MINUTES = getattr(settings, "BOOKING_SLOT_INTERVAL_MINUTES", 30)
ACTIVE_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]


# ---------- bookings a user is allowed to see ----------

def get_bookings_for_user(user, *, status=None):
    """Customers see their own, providers see bookings made with them,
    admins see everything."""
    qs = Booking.objects.select_related("customer", "provider", "service")

    if not is_admin(user):
        qs = qs.filter(Q(customer=user) | Q(provider__user=user))
    if status:
        qs = qs.filter(status=status)
    return qs


def get_booking_for_user(user, pk):
    """Fetch one booking from the user's own visible set.
    Strangers get a 404, so they can't tell whether a booking exists."""
    return get_object_or_404(get_bookings_for_user(user), pk=pk)


# ---------- availability (draft) ----------

def get_available_slots(*, provider, service, date):
    """Return a list of start datetimes that are free for this service on `date`.

    Assumes WorkingHours has: provider (FK), weekday (0=Monday ... 6=Sunday),
    start_time and end_time (TimeFields).
    """
    tz = timezone.get_current_timezone()
    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=SLOT_INTERVAL_MINUTES)
    now = timezone.now()

    day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()), tz)
    day_end = day_start + timedelta(days=1)

    windows = WorkingHours.objects.filter(provider=provider, weekday=date.weekday())

    booked = list(
        Booking.objects.filter(
            provider=provider,
            status__in=ACTIVE_STATUSES,
            start_time__lt=day_end,
            end_time__gt=day_start,
        ).values_list("start_time", "end_time")
    )

    slots = []
    for window in windows:
        cursor = timezone.make_aware(datetime.combine(date, window.start_time), tz)
        window_end = timezone.make_aware(datetime.combine(date, window.end_time), tz)

        while cursor + duration <= window_end:
            candidate_end = cursor + duration
            is_future = cursor > now
            is_free = not any(b_start < candidate_end and b_end > cursor for b_start, b_end in booked)
            if is_future and is_free:
                slots.append(cursor)
            cursor += step

    return sorted(slots)

def is_within_working_hours(provider, start, end) -> bool:
    """True if the whole appointment fits inside one working window."""
    tz = timezone.get_current_timezone()
    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)

    if local_start.date() != local_end.date():
        return False
    return WorkingHours.objects.filter(
        provider=provider,
        weekday=local_start.weekday(),
        start_time__lte=local_start.time(),
        end_time__gte=local_end.time(),
    ).exists()