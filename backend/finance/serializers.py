from decimal import Decimal
from rest_framework import serializers
from .models import (
    FeeCategory, FeeTemplate, FeeTemplateItem,
    StudentFeeAssignment, StudentCharge, FeeAdjustment,
)

ZERO = Decimal("0.00")


class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = ["id", "school", "name", "code", "description", "is_active"]
        read_only_fields = ["id"]


class FeeTemplateItemSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = FeeTemplateItem
        fields = [
            "id", "template", "category", "category_name",
            "description", "amount", "is_mandatory", "due_date", "sort_order",
        ]
        read_only_fields = ["id", "category_name"]

    def get_category_name(self, obj):
        return obj.category.name


class FeeTemplateSerializer(serializers.ModelSerializer):
    items = FeeTemplateItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()

    class Meta:
        model = FeeTemplate
        fields = [
            "id", "school", "academic_year", "academic_year_name",
            "target_class", "class_name", "name", "description",
            "is_active", "items", "total_amount", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_total_amount(self, obj):
        from django.db.models import Sum
        total = obj.items.aggregate(Sum("amount"))["amount__sum"] or ZERO
        return str(total)

    def get_academic_year_name(self, obj):
        return obj.academic_year.name

    def get_class_name(self, obj):
        return obj.target_class.name if obj.target_class else None


class StudentChargeSerializer(serializers.ModelSerializer):
    net_amount = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    amount_paid = serializers.SerializerMethodField()
    outstanding = serializers.SerializerMethodField()

    class Meta:
        model = StudentCharge
        fields = [
            "id", "school", "student", "academic_year",
            "category", "category_name", "description",
            "base_amount", "discount_amount", "waiver_amount",
            "net_amount", "amount_paid", "outstanding",
            "is_mandatory", "is_active", "due_date", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "net_amount", "category_name", "amount_paid", "outstanding", "created_at", "updated_at"]

    def get_net_amount(self, obj):
        return str(obj.net_amount)

    def get_category_name(self, obj):
        return obj.category.name

    def get_amount_paid(self, obj):
        from payments.models import PaymentAllocation
        from django.db.models import Sum
        agg = PaymentAllocation.objects.filter(
            charge=obj, payment__status="confirmed"
        ).aggregate(total=Sum("amount_allocated"))
        return str(agg["total"] or ZERO)

    def get_outstanding(self, obj):
        from payments.models import PaymentAllocation
        from django.db.models import Sum
        from decimal import Decimal
        agg = PaymentAllocation.objects.filter(
            charge=obj, payment__status="confirmed"
        ).aggregate(total=Sum("amount_allocated"))
        paid = agg["total"] or Decimal("0.00")
        return str(max(Decimal("0.00"), obj.net_amount - paid))

    def validate(self, attrs):
        # For PATCH, combine incoming values with existing instance values
        instance = self.instance
        discount = attrs.get("discount_amount",
                             instance.discount_amount if instance else Decimal("0.00"))
        waiver = attrs.get("waiver_amount",
                           instance.waiver_amount if instance else Decimal("0.00"))
        base = attrs.get("base_amount",
                         instance.base_amount if instance else Decimal("0.00"))
        if discount is None:
            discount = Decimal("0.00")
        if waiver is None:
            waiver = Decimal("0.00")
        if base is None:
            base = Decimal("0.00")
        if discount + waiver > base:
            raise serializers.ValidationError(
                "Total discounts and waivers cannot exceed the base amount."
            )
        return attrs


class StudentFeeAssignmentSerializer(serializers.ModelSerializer):
    charges = StudentChargeSerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentFeeAssignment
        fields = [
            "id", "school", "student", "student_name",
            "academic_year", "academic_year_name",
            "template", "notes", "charges", "assigned_at",
        ]
        read_only_fields = ["id", "assigned_at"]

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_academic_year_name(self, obj):
        return obj.academic_year.name


class FeeAdjustmentSerializer(serializers.ModelSerializer):
    applied_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FeeAdjustment
        fields = [
            "id", "charge", "adjustment_type",
            "previous_amount", "new_amount", "amount_changed",
            "reason", "applied_by", "applied_by_name", "applied_at",
        ]
        read_only_fields = ["id", "applied_at", "applied_by_name"]

    def get_applied_by_name(self, obj):
        return obj.applied_by.get_full_name() if obj.applied_by else None


class ApplyTemplateSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    academic_year_id = serializers.UUIDField()
    template_id = serializers.UUIDField()
