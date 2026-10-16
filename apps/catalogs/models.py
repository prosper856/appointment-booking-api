from django.core.validators import MinValueValidator
from django.db import models

from apps.base.models import BaseModel


class Service(BaseModel):
    provider = models.ForeignKey(
        "providers.Provider", on_delete=models.CASCADE, related_name="services"
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(5)]
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "name"], name="unique_service_name_per_provider"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider})"