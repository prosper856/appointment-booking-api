from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema  # <-- Added imports
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import StandardPagination

from . import services
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        parameters=[
            OpenApiParameter(
                name="unread",
                description="Filter by unread status (true/1 for unread only)",
                required=False,
                type=bool,
            )
        ],
        responses={200: NotificationSerializer(many=True)},
    )
    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        if request.query_params.get("unread", "").lower() in ("1", "true"):
            qs = qs.filter(is_read=False)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(NotificationSerializer(page, many=True).data)


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        responses={
            200: OpenApiResponse(
                description="Returns the total count of unread notifications.",
            )
        },
    )
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread": count})


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        responses={
            200: NotificationSerializer,
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    def post(self, request, pk):
        notification = Notification.objects.filter(user=request.user, pk=pk).first()
        if notification is None:
            return Response({"detail": "Not found."}, status=404)
        services.mark_read(user=request.user, pk=pk)
        notification.refresh_from_db()
        return Response(NotificationSerializer(notification).data)


class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        responses={
            200: OpenApiResponse(
                description="Returns the count of how many notifications were marked as read.",
            )
        },
    )
    def post(self, request):
        return Response({"marked_read": services.mark_all_read(user=request.user)})