from django.contrib import admin, messages
from rest_framework.exceptions import APIException

from . import services
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "customer", "provider", "service",
        "start_time", "end_time", "status", "created_at",
    ]
    list_filter = ["status", "provider", "start_time"]
    search_fields = [
        "reference", "customer__email", "customer__first_name",
        "customer__last_name", "provider__business_name",
    ]
    date_hierarchy = "start_time"
    list_select_related = ["customer", "provider", "service"]
    ordering = ["-start_time"]
    actions = ["confirm_selected", "cancel_selected"]

    def get_readonly_fields(self, request, obj=None):
        # Only the internal notes can be edited by hand.
        return [f.name for f in self.model._meta.fields if f.name != "notes"]

    def has_add_permission(self, request):
        return False  # bookings are created through the API, where the rules live

    def has_delete_permission(self, request, obj=None):
        return False  # keep booking history intact

    # ---------- actions (they go through services.py, so the rules still apply) ----------

    def _run(self, request, queryset, action, verb, **kwargs):
        done = 0
        for booking in queryset:
            try:
                action(booking=booking, **kwargs)
                done += 1
            except APIException as exc:
                self.message_user(
                    request, f"{booking.reference}: {exc.detail}", level=messages.WARNING
                )
        if done:
            self.message_user(request, f"{done} booking(s) {verb}.", level=messages.SUCCESS)

    @admin.action(description="Confirm selected bookings")
    def confirm_selected(self, request, queryset):
        self._run(
            request, queryset, services.confirm_booking, "confirmed",
            confirmed_by=request.user,
        )

    @admin.action(description="Cancel selected bookings")
    def cancel_selected(self, request, queryset):
        self._run(
            request, queryset, services.cancel_booking, "cancelled",
            cancelled_by=request.user, reason="Cancelled by admin",
        )