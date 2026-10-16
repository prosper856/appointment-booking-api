from django.utils import timezone
from rest_framework import serializers

from apps.catalogs.models import Service
from apps.providers.models import Provider

from .models import Booking


# ---------- Output ----------

class BookingProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ["id", "business_name"]


class BookingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "duration_minutes", "price"]


class BookingSerializer(serializers.ModelSerializer):
    """What the API returns for a booking. Everything is read-only."""

    provider = BookingProviderSerializer(read_only=True)
    service = BookingServiceSerializer(read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "customer_name",
            "provider",
            "service",
            "start_time",
            "end_time",
            "status",
            "notes",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = fields


# ---------- Input ----------

class BookingCreateSerializer(serializers.Serializer):
    provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.filter(is_active=True)
    )
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True)
    )
    start_time = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Start time must be in the future.")
        return value

    def validate(self, attrs):
        if attrs["service"].provider_id != attrs["provider"].id:
            raise serializers.ValidationError(
                {"service": "This service is not offered by the selected provider."}
            )
        return attrs


class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class BookingRescheduleSerializer(serializers.Serializer):
    new_start_time = serializers.DateTimeField()

    def validate_new_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("New start time must be in the future.")
        return value


class AvailabilityQuerySerializer(serializers.Serializer):
    """Validates the query string of GET /availability/?provider=&service=&date="""

    provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.filter(is_active=True)
    )
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True)
    )
    date = serializers.DateField()

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Date cannot be in the past.")
        return value

    def validate(self, attrs):
        if attrs["service"].provider_id != attrs["provider"].id:
            raise serializers.ValidationError(
                {"service": "This service is not offered by the selected provider."}
            )
        return attrs