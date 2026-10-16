from rest_framework import serializers

from .models import Provider, WorkingHours


class ProviderSerializer(serializers.ModelSerializer):
    """Public view of a provider. No email or user details."""

    class Meta:
        model = Provider
        fields = ["id", "business_name", "bio", "address"]
        read_only_fields = fields


class MyProviderSerializer(serializers.ModelSerializer):
    """The provider's own profile."""

    class Meta:
        model = Provider
        fields = ["id", "business_name", "bio", "address", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class WorkingHoursSerializer(serializers.ModelSerializer):
    weekday_name = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorkingHours
        fields = ["id", "weekday", "weekday_name", "start_time", "end_time"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        weekday = attrs.get("weekday", getattr(self.instance, "weekday", None))

        if start >= end:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        overlapping = WorkingHours.objects.filter(
            provider=self.context["provider"],
            weekday=weekday,
            start_time__lt=end,
            end_time__gt=start,
        )
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError("This overlaps with another working window on that day.")
        return attrs