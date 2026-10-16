from rest_framework import serializers

from apps.bookings.models import Booking

from .choices import ComplaintCategory, ComplaintStatus
from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source="booking.reference", read_only=True)
    provider_name = serializers.CharField(source="booking.provider.business_name", read_only=True)
    service_name = serializers.CharField(source="booking.service.name", read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id", "reference", "booking", "booking_reference", "provider_name",
            "service_name", "customer_name", "category", "subject", "description",
            "status", "admin_response", "resolved_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class ComplaintCreateSerializer(serializers.Serializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.none())
    category = serializers.ChoiceField(choices=ComplaintCategory.choices)
    subject = serializers.CharField(max_length=150)
    description = serializers.CharField(min_length=20, max_length=2000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            # Only the user's own bookings are valid choices, so other
            # people's booking IDs look the same as nonexistent ones.
            self.fields["booking"].queryset = Booking.objects.filter(customer=request.user)


class ComplaintUpdateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(min_length=20, max_length=2000, required=False)


class ComplaintReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            (ComplaintStatus.UNDER_REVIEW, "Under review"),
            (ComplaintStatus.RESOLVED, "Resolved"),
            (ComplaintStatus.REJECTED, "Rejected"),
        ]
    )
    admin_response = serializers.CharField(required=False, allow_blank=True, max_length=2000)