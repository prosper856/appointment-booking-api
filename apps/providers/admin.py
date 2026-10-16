from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Provider, WorkingHours


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 0


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["business_name", "user", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["business_name", "user__email"]
    list_select_related = ["user"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [WorkingHoursInline]