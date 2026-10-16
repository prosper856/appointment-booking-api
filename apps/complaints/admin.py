from django.contrib import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ["reference", "customer", "booking", "category", "status", "created_at"]
    list_filter = ["status", "category"]
    search_fields = ["reference", "subject", "customer__email", "booking__reference"]
    list_select_related = ["customer", "booking"]
    readonly_fields = [f.name for f in Complaint._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False