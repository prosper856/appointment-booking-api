from django.shortcuts import get_object_or_404

from apps.base.permissions import is_admin

from .models import Complaint


def get_complaints_for_user(user, *, status=None, category=None):
    qs = Complaint.objects.select_related("booking__provider", "booking__service", "customer")
    if not is_admin(user):
        qs = qs.filter(customer=user)
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    return qs


def get_complaint_for_user(user, pk):
    return get_object_or_404(get_complaints_for_user(user), pk=pk)