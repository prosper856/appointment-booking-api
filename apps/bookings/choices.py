from django.db import models


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"          # created, waiting for provider
    CONFIRMED = "CONFIRMED", "Confirmed"    # provider accepted
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"