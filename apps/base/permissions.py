from rest_framework import permissions

from apps.base.choices import UserRole


def is_admin(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or getattr(user, "role", None) == UserRole.ADMIN)
    )


class IsAdmin(permissions.BasePermission):
    """Only admins."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsCustomer(permissions.BasePermission):
    """Customers (and admins)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == UserRole.CUSTOMER or is_admin(user))
        )


class IsProvider(permissions.BasePermission):
    """Providers (and admins)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == UserRole.PROVIDER or is_admin(user))
        )


class IsAdminOrOwner(permissions.BasePermission):
    """Admins, or the user who owns the object."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        return obj == request.user or getattr(obj, "user", None) == request.user


class IsUnverified(permissions.BasePermission):
    """Logged-in users who haven't verified their OTP yet."""

    message = "Your account is already verified."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and not getattr(user, "otp_verified", False)
        )