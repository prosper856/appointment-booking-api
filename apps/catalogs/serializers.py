from rest_framework import serializers

from .models import Service

MAX_DURATION_MINUTES = 720  # 12 hours


class ServiceSerializer(serializers.ModelSerializer):
    """What customers see."""

    provider = serializers.PrimaryKeyRelatedField(read_only=True)
    provider_name = serializers.CharField(source="provider.business_name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "provider", "provider_name", "name",
            "description", "duration_minutes", "price",
        ]
        read_only_fields = fields


class MyServiceSerializer(serializers.ModelSerializer):
    """A provider's own services (create, edit, view)."""

    class Meta:
        model = Service
        fields = [
            "id", "name", "description", "duration_minutes",
            "price", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        return value.strip()

    def validate_duration_minutes(self, value):
        if value > MAX_DURATION_MINUTES:
            raise serializers.ValidationError(
                f"A service can't be longer than {MAX_DURATION_MINUTES} minutes."
            )
        return value

    def validate(self, attrs):
        provider = self.context["provider"]
        name = attrs.get("name", getattr(self.instance, "name", None))

        if name:
            duplicates = Service.objects.filter(provider=provider, name__iexact=name)
            if self.instance:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError(
                    {"name": "You already have a service with this name."}
                )
        return attrs


class ServiceQuerySerializer(serializers.Serializer):
    """Validates ?provider= and ?search= on the public list."""

    provider = serializers.UUIDField(required=False)
    search = serializers.CharField(required=False, max_length=100)