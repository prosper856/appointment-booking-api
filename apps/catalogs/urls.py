from django.urls import path

from .views import (
    MyServiceDetailView,
    MyServiceListCreateView,
    ServiceDetailView,
    ServiceListView,
)

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/<uuid:pk>/", ServiceDetailView.as_view(), name="service-detail"),
    path("providers/me/services/", MyServiceListCreateView.as_view(), name="my-service-list-create"),
    path("providers/me/services/<uuid:pk>/", MyServiceDetailView.as_view(), name="my-service-detail"),
]