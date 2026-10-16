from django.urls import path

from .views import (
    ComplaintDetailView,
    ComplaintListCreateView,
    ComplaintReviewView,
    ComplaintWithdrawView,
)

urlpatterns = [
    path("complaints/", ComplaintListCreateView.as_view(), name="complaint-list-create"),
    path("complaints/<uuid:pk>/", ComplaintDetailView.as_view(), name="complaint-detail"),
    path("complaints/<uuid:pk>/withdraw/", ComplaintWithdrawView.as_view(), name="complaint-withdraw"),
    path("complaints/<uuid:pk>/review/", ComplaintReviewView.as_view(), name="complaint-review"),
]