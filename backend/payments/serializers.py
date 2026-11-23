"""
INCOME – Payments serializers.
"""

from decimal import Decimal
from rest_framework import serializers
from .models import Payment, PaymentAllocation, PaymentEvidence, PaymentReversal, StudentCreditTransaction


class PaymentEvidenceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PaymentEvidence
        fields = [
            "id", "payment", "evidence_type", "file", "file_url",
            "original_filename", "file_size", "content_type", "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at", "file_url", "original_filename", "file_size", "content_type"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class PaymentAllocationSerializer(serializers.ModelSerializer):
    charge_description = serializers.SerializerMethodField()

    class Meta:
        model = PaymentAllocation
        fields = [
            "id", "payment", "charge", "charge_description",
            "amount_allocated", "is_reversed", "created_at",
        ]
        read_only_fields = ["id", "created_at", "charge_description"]

    def get_charge_description(self, obj):
        return obj.charge.description


class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    # Use SerializerMethodField so we can call .all() safely
    allocations = serializers.SerializerMethodField()
    evidence_files = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id", "school", "student", "student_name", "student_admission_number",
            "academic_year", "academic_year_name",
            "payment_method", "amount", "payment_date", "status",
            "transaction_reference", "bank_name", "payer_name", "payer_phone",
            "notes", "rejection_reason",
            "recorded_by", "recorded_by_name",
            "verified_by", "verified_by_name", "verified_at",
            "allocations", "evidence_files",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "recorded_by", "verified_by", "verified_at",
            "rejected_by", "rejected_at", "created_at", "updated_at",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_student_admission_number(self, obj):
        return obj.student.admission_number

    def get_academic_year_name(self, obj):
        return obj.academic_year.name

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else None

    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None

    def get_allocations(self, obj):
        return PaymentAllocationSerializer(obj.allocations.all(), many=True).data

    def get_evidence_files(self, obj):
        request = self.context.get("request")
        return PaymentEvidenceSerializer(
            obj.evidence_files.all(), many=True, context={"request": request}
        ).data

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for recording a new payment."""

    allocations = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )
    transaction_reference = serializers.CharField(required=False, allow_blank=True, default="")
    bank_name = serializers.CharField(required=False, allow_blank=True, default="")
    payer_name = serializers.CharField(required=False, allow_blank=True, default="")
    payer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Payment
        fields = [
            "school", "student", "academic_year",
            "payment_method", "amount", "payment_date",
            "transaction_reference", "bank_name", "payer_name", "payer_phone",
            "notes", "allocations",
        ]

    def validate(self, attrs):
        method = attrs.get("payment_method")
        ref = attrs.get("transaction_reference", "")
        if method in ("mobile_money", "bank_transfer") and not (ref or "").strip():
            raise serializers.ValidationError(
                {"transaction_reference": "Transaction reference is required for this payment method."}
            )
        return attrs


class VerifyPaymentSerializer(serializers.Serializer):
    allocations = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )


class RejectPaymentSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10)


class ReversePaymentSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10)


class PaymentReversalSerializer(serializers.ModelSerializer):
    reversed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PaymentReversal
        fields = [
            "id", "payment", "reason", "reversed_by", "reversed_by_name",
            "reversed_at", "refund_amount",
        ]
        read_only_fields = ["id", "reversed_at", "reversed_by_name"]

    def get_reversed_by_name(self, obj):
        return obj.reversed_by.get_full_name() if obj.reversed_by else None
