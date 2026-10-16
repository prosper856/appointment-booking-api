from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.base.models import BaseModel
from apps.base.utils import generate_reference_code

from .choices import ComplaintCategory, ComplaintStatus


def complaint_reference():
    return generate_reference_code(prefix="CP")


class Complaint(BaseModel):
    reference = models.CharField( max_length=20, unique=True, default=complaint_reference, editable=False)
    booking = models.ForeignKey("bookings.Booking", on_delete=models.PROTECT, related_name="complaints")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="complaints")
    category = models.CharField(max_length=30, choices=ComplaintCategory.choices)
    subject = models.CharField(max_length=150)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ComplaintStatus.choices, default=ComplaintStatus.OPEN)
    admin_response = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, blank=True, on_delete=models.SET_NULL, related_name="+",)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["customer", "status"])]
        constraints = [
            # Backstop: one active complaint per booking, enforced by the database.
            models.UniqueConstraint(
                fields=["booking"],
                condition=Q(status__in=[ComplaintStatus.OPEN, ComplaintStatus.UNDER_REVIEW]),
                name="one_active_complaint_per_booking",
            ),
        ]

    def __str__(self):
        return f"{self.reference} ({self.status})"