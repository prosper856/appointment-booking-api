from django.db import models


class NotificationKind(models.TextChoices):
    BOOKING_CREATED = "BOOKING_CREATED", "New booking"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED", "Booking confirmed"
    BOOKING_CANCELLED = "BOOKING_CANCELLED", "Booking cancelled"
    BOOKING_RESCHEDULED = "BOOKING_RESCHEDULED", "Booking rescheduled"
    COMPLAINT_SUBMITTED = "COMPLAINT_SUBMITTED", "New complaint"
    COMPLAINT_UPDATED = "COMPLAINT_UPDATED", "Complaint update"