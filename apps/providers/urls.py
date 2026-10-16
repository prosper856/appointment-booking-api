from django.urls import path

from .views import (
    MyProviderView,
    MyWorkingHoursDetailView,
    MyWorkingHoursListCreateView,
    ProviderDetailView,
    ProviderListView,
)

urlpatterns = [
    path("providers/", ProviderListView.as_view(), name="provider-list"),
    path("providers/me/", MyProviderView.as_view(), name="provider-me"),
    path("providers/me/working-hours/", MyWorkingHoursListCreateView.as_view(), name="my-working-hours"),
    path("providers/me/working-hours/<uuid:pk>/", MyWorkingHoursDetailView.as_view(), name="my-working-hours-detail"),
    path("providers/<uuid:pk>/", ProviderDetailView.as_view(), name="provider-detail"),
]