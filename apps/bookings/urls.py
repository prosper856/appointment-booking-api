from django.urls import path

from .views import (
    AvailabilityView,
    BookingCancelView,
    BookingConfirmView,
    BookingDetailView,
    BookingListCreateView,
    BookingRescheduleView,
)

urlpatterns = [
    path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
    path("bookings/<uuid:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<uuid:pk>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
    path("bookings/<uuid:pk>/reschedule/", BookingRescheduleView.as_view(), name="booking-reschedule"),
    path("bookings/<uuid:pk>/confirm/", BookingConfirmView.as_view(), name="booking-confirm"),
    path("availability/", AvailabilityView.as_view(), name="availability"),
]