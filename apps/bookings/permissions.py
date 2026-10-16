from rest_framework import permissions

from apps.base.permissions import is_admin


class _BookingObjectPermission(permissions.BasePermission):
    """Shared base: user must be logged in, then the object rule decides."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsBookingParticipant(_BookingObjectPermission):
    """Customer who made it, the booked provider, or an admin.
    Used for: view, cancel."""

    def has_object_permission(self, request, view, booking):
        user = request.user
        return (
            is_admin(user)
            or booking.customer_id == user.id
            or booking.provider.user_id == user.id
        )


class IsBookingCustomer(_BookingObjectPermission):
    """Only the customer who made it, or an admin.
    Used for: reschedule."""

    def has_object_permission(self, request, view, booking):
        user = request.user
        return is_admin(user) or booking.customer_id == user.id


class IsBookingProvider(_BookingObjectPermission):
    """Only the booked provider, or an admin.
    Used for: confirm."""

    def has_object_permission(self, request, view, booking):
        user = request.user
        return is_admin(user) or booking.provider.user_id == user.id