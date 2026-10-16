from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.base.models import BaseModel

from .choices import Weekday


class Provider(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_profile"
    )
    business_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["business_name"]

    def __str__(self):
        return self.business_name


class WorkingHours(BaseModel):
    """One working window on one weekday. A provider can have several windows
    on the same day (for example 09:00-12:00 and 14:00-18:00)."""

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="working_hours_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.provider} - {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"