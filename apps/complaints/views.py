from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema  # <-- Added import
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import StandardPagination
from apps.base.permissions import IsAdmin, IsCustomer

from . import services
from .choices import ComplaintCategory, ComplaintStatus
from .models import Complaint
from .permissions import IsComplaintOwner, IsComplaintOwnerOrAdmin
from .selectors import get_complaint_for_user, get_complaints_for_user
from .serializers import (
    ComplaintCreateSerializer,
    ComplaintReviewSerializer,
    ComplaintSerializer,
    ComplaintUpdateSerializer,
)


def _choice_param(request, name, valid):
    value = request.query_params.get(name)
    if not value:
        return None
    value = value.upper()
    if value not in valid:
        raise ValidationError({name: f"Invalid {name}."})
    return value


class ComplaintListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Complaints"],
        responses={200: ComplaintSerializer(many=True)},
    )
    def get(self, request):
        complaints = get_complaints_for_user(
            request.user,
            status=_choice_param(request, "status", ComplaintStatus.values),
            category=_choice_param(request, "category", ComplaintCategory.values),
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(complaints, request, view=self)
        return paginator.get_paginated_response(ComplaintSerializer(page, many=True).data)

    @extend_schema(
        tags=["Complaints"],
        request=ComplaintCreateSerializer,
        responses={201: ComplaintSerializer},
    )
    def post(self, request):
        serializer = ComplaintCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        complaint = services.submit_complaint(customer=request.user, **serializer.validated_data)
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_201_CREATED)


class ComplaintDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsComplaintOwner()]
        return [IsAuthenticated(), IsComplaintOwnerOrAdmin()]

    def _get(self, request, pk):
        complaint = get_complaint_for_user(request.user, pk)  # 404 for strangers
        self.check_object_permissions(request, complaint)
        return complaint

    @extend_schema(
        tags=["Complaints"],
        responses={200: ComplaintSerializer},
    )
    def get(self, request, pk):
        return Response(ComplaintSerializer(self._get(request, pk)).data)

    @extend_schema(
        tags=["Complaints"],
        request=ComplaintUpdateSerializer,
        responses={200: ComplaintSerializer},
    )
    def patch(self, request, pk):
        serializer = ComplaintUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = services.update_complaint(
            complaint=self._get(request, pk), **serializer.validated_data
        )
        return Response(ComplaintSerializer(complaint).data)


class ComplaintWithdrawView(APIView):
    permission_classes = [IsAuthenticated, IsComplaintOwner]

    @extend_schema(
        tags=["Complaints"],
        responses={200: ComplaintSerializer},
    )
    def post(self, request, pk):
        complaint = get_complaint_for_user(request.user, pk)
        self.check_object_permissions(request, complaint)
        complaint = services.withdraw_complaint(complaint=complaint)
        return Response(ComplaintSerializer(complaint).data)


class ComplaintReviewView(APIView):
    """Admin only: move a complaint through review and write the response."""

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        tags=["Complaints"],
        request=ComplaintReviewSerializer,
        responses={200: ComplaintSerializer},
    )
    def post(self, request, pk):
        serializer = ComplaintReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = get_object_or_404(Complaint, pk=pk)
        complaint = services.review_complaint(
            complaint=complaint,
            admin=request.user,
            new_status=serializer.validated_data["status"],
            response=serializer.validated_data.get("admin_response", ""),
        )
        return Response(ComplaintSerializer(complaint).data)