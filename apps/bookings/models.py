from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    DateTimeRangeField,
    RangeBoundary,
    RangeOperators,
)
from django.db import models
from django.db.models import F, Func, Q

from apps.base.models import BaseModel
from apps.base.utils import generate_reference_code

from .choices import BookingStatus


class TsTzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


def booking_reference():
    return generate_reference_code(prefix="BK")


class Booking(BaseModel):
    reference = models.CharField(max_length=20, unique=True, default=booking_reference, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    provider = models.ForeignKey("providers.Provider", on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey("catalogs.Service", on_delete=models.PROTECT, related_name="bookings")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    notes = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="+",)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["provider", "start_time"]),
            models.Index(fields=["customer", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="booking_end_after_start",
            ),
            ExclusionConstraint(
                name="booking_no_provider_overlap",
                expressions=[
                    (
                        TsTzRange("start_time", "end_time", RangeBoundary()),
                        RangeOperators.OVERLAPS,
                    ),
                    ("provider", RangeOperators.EQUAL),
                ],
                condition=Q(
                    status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
            ),
        ]

    def __str__(self):
        return f"{self.reference} ({self.status})"