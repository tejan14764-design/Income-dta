"""
INCOME – Payment views.
"""

import os
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend

from .models import Payment, PaymentAllocation, PaymentEvidence, PaymentStatus
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    VerifyPaymentSerializer, RejectPaymentSerializer, ReversePaymentSerializer,
    PaymentEvidenceSerializer, PaymentReversalSerializer,
)
from .services import confirm_payment, reject_payment, reverse_payment, allocate_payment
from accounts.permissions import CanRecordPayments, CanVerifyPayments
from audit.utils import log_action

ALLOWED_EVIDENCE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["school", "student", "academic_year", "status", "payment_method"]
    search_fields = ["student__first_name", "student__last_name", "student__admission_number", "transaction_reference"]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date", "-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return Payment.objects.filter(school_id=school_id).select_related(
                "student", "academic_year", "recorded_by", "verified_by"
            ).prefetch_related("allocations__charge", "evidence_files")
        return Payment.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return the full payment serializer (not the create serializer)
        payment = serializer.instance
        output = PaymentSerializer(payment, context={"request": request})
        from rest_framework import status as drf_status
        from rest_framework.response import Response
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=drf_status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        payment_method = serializer.validated_data.get("payment_method")
        allocations_data = serializer.validated_data.pop("allocations", [])

        # Cash payments may be auto-confirmed by cashier
        initial_status = PaymentStatus.CONFIRMED if payment_method == "cash" else PaymentStatus.PENDING

        payment = serializer.save(
            recorded_by=self.request.user,
            status=initial_status,
        )

        if payment_method == "cash":
            payment.verified_by = self.request.user
            payment.verified_at = timezone.now()
            payment.save(update_fields=["verified_by", "verified_at"])

        # Allocate if data provided and payment is confirmed
        if allocations_data and payment.status == PaymentStatus.CONFIRMED:
            try:
                allocate_payment(payment, allocations_data)
            except ValueError as e:
                # Allocation failed; payment still recorded but not allocated
                pass

        log_action(
            actor=self.request.user,
            action="PAYMENT_RECORDED",
            obj=payment,
            school_id=payment.school_id,
        )

    @action(detail=True, methods=["post"], url_path="upload-evidence",
            parser_classes=[MultiPartParser, FormParser])
    def upload_evidence(self, request, pk=None):
        payment = self.get_object()
        file = request.FILES.get("file")
        evidence_type = request.data.get("evidence_type", "other")

        if not file:
            return Response({"success": False, "error": "No file provided."}, status=400)

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Response({"success": False, "error": f"File type not allowed: {ext}"}, status=400)

        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
        if file.size > max_size:
            return Response({"success": False, "error": "File too large."}, status=400)

        evidence = PaymentEvidence.objects.create(
            payment=payment,
            evidence_type=evidence_type,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=request.user,
        )
        log_action(actor=request.user, action="EVIDENCE_UPLOADED", obj=payment, school_id=payment.school_id)
        return Response({
            "success": True,
            "data": PaymentEvidenceSerializer(evidence, context={"request": request}).data
        })


class PaymentVerificationViewSet(viewsets.GenericViewSet):
    """Dedicated endpoints for financial officer payment verification."""
    permission_classes = [IsAuthenticated, CanVerifyPayments]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return Payment.objects.filter(
                school_id=school_id, status=PaymentStatus.PENDING
            ).select_related("student", "academic_year", "recorded_by")
        return Payment.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PaymentSerializer(queryset, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data, "count": queryset.count()})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        payment = Payment.objects.get(pk=pk)

        # Separation of duties check
        if payment.recorded_by == request.user:
            return Response(
                {"success": False, "error": "You cannot verify your own payment submission."},
                status=status.HTTP_403_FORBIDDEN,
            )

        s = VerifyPaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        payment = confirm_payment(payment, request.user)

        # Allocate
        if s.validated_data.get("allocations"):
            try:
                allocate_payment(payment, s.validated_data["allocations"])
            except ValueError as e:
                return Response({"success": False, "error": str(e)}, status=400)

        log_action(actor=request.user, action="PAYMENT_VERIFIED", obj=payment, school_id=payment.school_id)
        return Response({"success": True, "message": "Payment confirmed.", "data": PaymentSerializer(payment).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        payment = Payment.objects.get(pk=pk)
        s = RejectPaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment = reject_payment(payment, request.user, s.validated_data["reason"])
        log_action(actor=request.user, action="PAYMENT_REJECTED", obj=payment, school_id=payment.school_id)
        return Response({"success": True, "message": "Payment rejected."})

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        payment = Payment.objects.get(pk=pk)
        s = ReversePaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        reversal = reverse_payment(payment, request.user, s.validated_data["reason"])
        log_action(actor=request.user, action="PAYMENT_REVERSED", obj=payment, school_id=payment.school_id)
        return Response({
            "success": True,
            "message": "Payment reversed.",
            "data": PaymentReversalSerializer(reversal).data,
        })
