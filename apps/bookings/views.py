from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import StandardPagination
from apps.base.permissions import IsCustomer

from . import services
from .choices import BookingStatus
from .permissions import IsBookingCustomer, IsBookingParticipant, IsBookingProvider
from .selectors import get_available_slots, get_booking_for_user, get_bookings_for_user
from .serializers import (
    AvailabilityQuerySerializer,
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingRescheduleSerializer,
    BookingSerializer,
)


class BookingObjectMixin:
    """Fetch a booking from the user's visible set (404 for strangers),
    then run the object-level permission check."""

    def get_booking(self, request, pk):
        booking = get_booking_for_user(request.user, pk)
        self.check_object_permissions(request, booking)
        return booking


class BookingListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Bookings"],
        responses={200: BookingSerializer(many=True)},
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        if status_filter:
            status_filter = status_filter.upper()
            if status_filter not in BookingStatus.values:
                raise ValidationError({"status": "Invalid status."})

        bookings = get_bookings_for_user(request.user, status=status_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(bookings, request, view=self)
        return paginator.get_paginated_response(
            BookingSerializer(page, many=True).data
        )

    @extend_schema(
        tags=["Bookings"],
        request=BookingCreateSerializer,
        responses={201: BookingSerializer},
    )
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = services.create_booking(
            customer=request.user, **serializer.validated_data
        )
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(BookingObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsBookingParticipant]

    @extend_schema(
        tags=["Bookings"],
        responses={200: BookingSerializer},
    )
    def get(self, request, pk):
        booking = self.get_booking(request, pk)
        return Response(BookingSerializer(booking).data)


class BookingCancelView(BookingObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsBookingParticipant]

    @extend_schema(
        tags=["Bookings"],
        request=BookingCancelSerializer,
        responses={200: BookingSerializer},
    )
    def post(self, request, pk):
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = self.get_booking(request, pk)
        booking = services.cancel_booking(
            booking=booking,
            cancelled_by=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(BookingSerializer(booking).data)


class BookingRescheduleView(BookingObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsBookingCustomer]

    @extend_schema(
        tags=["Bookings"],
        request=BookingRescheduleSerializer,
        responses={200: BookingSerializer},
    )
    def post(self, request, pk):
        serializer = BookingRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = self.get_booking(request, pk)
        booking = services.reschedule_booking(
            booking=booking,
            new_start_time=serializer.validated_data["new_start_time"],
            rescheduled_by=request.user,
        )
        return Response(BookingSerializer(booking).data)


class BookingConfirmView(BookingObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsBookingProvider]

    @extend_schema(
        tags=["Bookings"],
        responses={200: BookingSerializer},
    )
    def post(self, request, pk):
        booking = self.get_booking(request, pk)
        booking = services.confirm_booking(booking=booking, confirmed_by=request.user)
        return Response(BookingSerializer(booking).data)


class AvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Availability"],
        parameters=[AvailabilityQuerySerializer],
        responses={
            200: OpenApiResponse(
                description="Returns available time slots for the provider and service."
            )
        },
    )
    def get(self, request):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        slots = get_available_slots(
            provider=data["provider"], service=data["service"], date=data["date"]
        )
        return Response(
            {
                "provider": str(data["provider"].id),
                "service": str(data["service"].id),
                "date": data["date"],
                "slots": [slot.isoformat() for slot in slots],
            }
        )