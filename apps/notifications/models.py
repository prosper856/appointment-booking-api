from django.conf import settings
from django.db import models

from apps.base.models import BaseModel

from .choices import NotificationKind


class Notification(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=30, choices=NotificationKind.choices)
    title = models.CharField(max_length=150)
    message = models.TextField()
    # Loose link (no foreign key), so this app doesn't depend on bookings or complaints.
    related_model = models.CharField(max_length=30, blank=True)
    related_id = models.UUIDField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.kind} -> {self.user}"