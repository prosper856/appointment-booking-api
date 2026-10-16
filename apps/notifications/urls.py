from django.urls import path

from .views import MarkAllReadView, MarkReadView, NotificationListView, UnreadCountView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/", UnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/read-all/", MarkAllReadView.as_view(), name="notification-read-all"),
    path("notifications/<uuid:pk>/read/", MarkReadView.as_view(), name="notification-read"),
]