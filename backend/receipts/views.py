"""
INCOME – Receipt views.
"""

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Receipt, ReceiptPrintLog
from .services import generate_receipt_for_payment, generate_receipt_pdf
from payments.models import Payment, PaymentStatus
from audit.utils import log_action


class ReceiptSerializer(ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            "id", "receipt_number", "student_name", "student_admission_number",
            "class_name", "academic_year_name", "payment_method",
            "amount_paid", "outstanding_after", "fee_descriptions",
            "transaction_reference", "cashier_name", "generated_at",
        ]
        read_only_fields = fields


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        # Allow direct pk access for detail actions (reprint, pdf)
        if self.kwargs.get("pk"):
            return Receipt.objects.all()
        school_id = self.request.query_params.get("school")
        student_id = self.request.query_params.get("student")
        if student_id:
            return Receipt.objects.filter(payment__student_id=student_id).order_by("-generated_at")
        if school_id:
            return Receipt.objects.filter(school_id=school_id).order_by("-generated_at")
        return Receipt.objects.none()

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """Generate (or return existing) receipt for a payment."""
        payment_id = request.data.get("payment_id")
        try:
            payment = Payment.objects.select_related(
                "student", "academic_year", "school", "recorded_by"
            ).prefetch_related("allocations__charge").get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({"success": False, "error": "Payment not found."}, status=404)

        if payment.status != PaymentStatus.CONFIRMED:
            return Response(
                {"success": False, "error": "Receipts can only be generated for confirmed payments."},
                status=400,
            )

        receipt = generate_receipt_for_payment(payment, request.user)
        log_action(actor=request.user, action="RECEIPT_GENERATED", obj=receipt, school_id=payment.school_id)
        return Response({"success": True, "data": ReceiptSerializer(receipt).data})

    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request, pk=None):
        """Download receipt as PDF."""
        receipt = self.get_object()
        pdf_bytes = generate_receipt_pdf(receipt)

        ReceiptPrintLog.objects.create(
            receipt=receipt,
            printed_by=request.user,
            print_type="pdf",
        )
        log_action(actor=request.user, action="RECEIPT_PRINTED", obj=receipt, school_id=receipt.school_id)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="receipt-{receipt.receipt_number}.pdf"'
        return response

    @action(detail=True, methods=["post"], url_path="reprint")
    def reprint(self, request, pk=None):
        """Log a reprint event and return receipt data."""
        receipt = self.get_object()
        ReceiptPrintLog.objects.create(
            receipt=receipt,
            printed_by=request.user,
            print_type="reprint",
            notes=request.data.get("notes", ""),
        )
        log_action(actor=request.user, action="RECEIPT_REPRINTED", obj=receipt, school_id=receipt.school_id)
        return Response({"success": True, "data": ReceiptSerializer(receipt).data})
