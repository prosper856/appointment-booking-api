from django.db import models


class ComplaintStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    RESOLVED = "RESOLVED", "Resolved"
    REJECTED = "REJECTED", "Rejected"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class ComplaintCategory(models.TextChoices):
    LATE_OR_NO_SHOW = "LATE_OR_NO_SHOW", "Late or no-show"
    POOR_SERVICE = "POOR_SERVICE", "Poor service"
    WRONG_CHARGE = "WRONG_CHARGE", "Wrong charge"
    RUDE_BEHAVIOR = "RUDE_BEHAVIOR", "Rude behavior"
    OTHER = "OTHER", "Other"