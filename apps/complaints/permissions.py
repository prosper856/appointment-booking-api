from rest_framework import permissions

from apps.base.permissions import is_admin


class IsComplaintOwner(permissions.BasePermission):
    """Only the customer who filed it."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, complaint):
        return complaint.customer_id == request.user.id


class IsComplaintOwnerOrAdmin(IsComplaintOwner):
    def has_object_permission(self, request, view, complaint):
        return is_admin(request.user) or complaint.customer_id == request.user.id