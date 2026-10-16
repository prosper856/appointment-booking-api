from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "duration_minutes", "price", "is_active", "created_at"]
    list_filter = ["is_active", "provider"]
    search_fields = ["name", "provider__business_name"]
    list_select_related = ["provider"]
    readonly_fields = ["id", "created_at", "updated_at"]