from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.bookings.choices import BookingStatus
from apps.notifications import events

from .choices import ComplaintStatus
from .exceptions import ComplaintConflict, ComplaintRuleViolation
from .models import Complaint

COMPLAINT_WINDOW_DAYS = getattr(settings, "COMPLAINT_WINDOW_DAYS", 14)
ACTIVE = [ComplaintStatus.OPEN, ComplaintStatus.UNDER_REVIEW]
FINAL = [ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]
TRANSITIONS = {
    ComplaintStatus.OPEN: {ComplaintStatus.UNDER_REVIEW, ComplaintStatus.REJECTED},
    ComplaintStatus.UNDER_REVIEW: {ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED},
}


def submit_complaint(*, customer, booking, category, subject, description) -> Complaint:
    if booking.customer_id != customer.id:
        raise ComplaintRuleViolation("You can only complain about your own bookings.")
    if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED):
        raise ComplaintRuleViolation("Only confirmed or completed bookings can be complained about.")

    now = timezone.now()
    if booking.start_time > now:
        raise ComplaintRuleViolation("You can complain once the appointment time has passed.")
    if now > booking.end_time + timedelta(days=COMPLAINT_WINDOW_DAYS):
        raise ComplaintRuleViolation(
            f"Complaints must be filed within {COMPLAINT_WINDOW_DAYS} days of the appointment."
        )
    if Complaint.objects.filter(booking=booking, status__in=ACTIVE).exists():
        raise ComplaintConflict()

    try:
        with transaction.atomic():
            complaint = Complaint.objects.create(
                booking=booking, customer=customer, category=category,
                subject=subject, description=description,
            )
            transaction.on_commit(partial(events.complaint_submitted, complaint), robust=True)
    except IntegrityError:
        raise ComplaintConflict()
    return complaint


def update_complaint(*, complaint, **fields) -> Complaint:
    """Customer adds details. Only allowed before an admin starts reviewing."""
    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.status != ComplaintStatus.OPEN:
            raise ComplaintRuleViolation("This complaint is already being reviewed and can't be edited.")
        for name, value in fields.items():
            setattr(complaint, name, value)
        complaint.save(update_fields=[*fields, "updated_at"])
    return complaint


def withdraw_complaint(*, complaint) -> Complaint:
    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.status != ComplaintStatus.OPEN:
            raise ComplaintRuleViolation("Only open complaints can be withdrawn.")
        complaint.status = ComplaintStatus.WITHDRAWN
        complaint.save(update_fields=["status", "updated_at"])
    return complaint


def review_complaint(*, complaint, admin, new_status, response="") -> Complaint:
    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)

        if new_status not in TRANSITIONS.get(complaint.status, set()):
            raise ComplaintRuleViolation(
                f"A {complaint.get_status_display().lower()} complaint can't be moved to "
                f"{ComplaintStatus(new_status).label.lower()}."
            )
        if new_status in FINAL and not response.strip():
            raise ComplaintRuleViolation("A response is required to resolve or reject a complaint.")

        complaint.status = new_status
        if response.strip():
            complaint.admin_response = response.strip()
        complaint.reviewed_by = admin
        if new_status in FINAL:
            complaint.resolved_at = timezone.now()
        complaint.save(
            update_fields=["status", "admin_response", "reviewed_by", "resolved_at", "updated_at"]
        )
        transaction.on_commit(partial(events.complaint_updated, complaint), robust=True)
    return complaint