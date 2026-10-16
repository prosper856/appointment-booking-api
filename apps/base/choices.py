from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    PROVIDER = "PROVIDER", "Provider"
    ADMIN = "ADMIN", "Admin"


class AccountStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"      # registered, OTP not verified yet
    ACTIVE = "ACTIVE", "Active"         # verified and can use the app
    SUSPENDED = "SUSPENDED", "Suspended"  # temporarily restricted
    BLOCKED = "BLOCKED", "Blocked"      # permanently restricted