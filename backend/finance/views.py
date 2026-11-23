"""
INCOME – Finance views.
"""

from decimal import Decimal
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    FeeCategory, FeeTemplate, FeeTemplateItem,
    StudentFeeAssignment, StudentCharge, FeeAdjustment,
)
from .serializers import (
    FeeCategorySerializer, FeeTemplateSerializer, FeeTemplateItemSerializer,
    StudentFeeAssignmentSerializer, StudentChargeSerializer, FeeAdjustmentSerializer,
    ApplyTemplateSerializer,
)
from .utils import apply_template_to_student, get_student_financial_summary
from audit.utils import log_action


class FeeCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeeCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["school", "is_active"]
    search_fields = ["name", "code"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return FeeCategory.objects.filter(school_id=school_id)
        return FeeCategory.objects.none()


class FeeTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeeTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["school", "academic_year", "target_class", "is_active"]
    search_fields = ["name"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return FeeTemplate.objects.filter(
                school_id=school_id
            ).prefetch_related("items__category")
        return FeeTemplate.objects.none()

    def perform_create(self, serializer):
        template = serializer.save(created_by=self.request.user)
        log_action(actor=self.request.user, action="FEE_TEMPLATE_CREATED", obj=template)

    @action(detail=True, methods=["post"], url_path="apply")
    def apply_to_student(self, request, pk=None):
        """Apply this template to one student."""
        template = self.get_object()
        serializer = ApplyTemplateSerializer(data={
            "student_id": request.data.get("student_id"),
            "academic_year_id": request.data.get("academic_year_id"),
            "template_id": str(template.id),
        })
        serializer.is_valid(raise_exception=True)

        from students.models import Student
        from academics.models import AcademicYear

        student = Student.objects.get(id=serializer.validated_data["student_id"])
        academic_year = AcademicYear.objects.get(id=serializer.validated_data["academic_year_id"])

        assignment = apply_template_to_student(template, student, academic_year, request.user)
        log_action(
            actor=request.user,
            action="FEE_TEMPLATE_APPLIED",
            obj=assignment,
            school_id=student.school_id,
        )
        return Response({
            "success": True,
            "message": f"Template applied to {student.full_name}.",
            "data": StudentFeeAssignmentSerializer(assignment, context={"request": request}).data,
        })


class FeeTemplateItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeeTemplateItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["template"]

    def get_queryset(self):
        template_id = self.request.query_params.get("template")
        if template_id:
            return FeeTemplateItem.objects.filter(template_id=template_id).select_related("category")
        return FeeTemplateItem.objects.none()


class StudentFeeAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentFeeAssignmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["school", "student", "academic_year"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        student_id = self.request.query_params.get("student")
        if student_id:
            return StudentFeeAssignment.objects.filter(
                student_id=student_id
            ).prefetch_related("charges__category")
        if school_id:
            return StudentFeeAssignment.objects.filter(
                school_id=school_id
            ).prefetch_related("charges__category")
        return StudentFeeAssignment.objects.none()

    @action(detail=True, methods=["get"], url_path="financial-summary")
    def financial_summary(self, request, pk=None):
        assignment = self.get_object()
        summary = get_student_financial_summary(assignment.student, assignment.academic_year)
        return Response({"success": True, "data": summary})


class StudentChargeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentChargeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["school", "student", "academic_year", "category", "status", "is_active"]
    search_fields = ["description"]

    def get_queryset(self):
        # Allow direct pk access for detail/action endpoints
        if self.kwargs.get("pk"):
            return StudentCharge.objects.all()
        student_id = self.request.query_params.get("student")
        school_id = self.request.query_params.get("school")
        if student_id:
            return StudentCharge.objects.filter(
                student_id=student_id
            ).select_related("category", "academic_year")
        if school_id:
            return StudentCharge.objects.filter(
                school_id=school_id
            ).select_related("category", "student", "academic_year")
        return StudentCharge.objects.none()

    def perform_create(self, serializer):
        charge = serializer.save(created_by=self.request.user)
        log_action(
            actor=self.request.user,
            action="CHARGE_ADDED",
            obj=charge,
            school_id=charge.school_id,
        )

    @action(detail=True, methods=["post"], url_path="adjust")
    def apply_adjustment(self, request, pk=None):
        """Apply a discount, waiver or correction to a charge."""
        charge = self.get_object()
        adjustment_type = request.data.get("adjustment_type")
        new_amount = Decimal(str(request.data.get("new_amount", 0)))
        reason = request.data.get("reason", "").strip()

        if not reason:
            return Response(
                {"success": False, "error": "A reason is required for financial adjustments."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_discount = charge.discount_amount
        previous_waiver = charge.waiver_amount

        if adjustment_type == "discount":
            prev = charge.discount_amount
            charge.discount_amount = new_amount
            field = "discount_amount"
        elif adjustment_type == "waiver":
            prev = charge.waiver_amount
            charge.waiver_amount = new_amount
            field = "waiver_amount"
        else:
            return Response(
                {"success": False, "error": "Invalid adjustment type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if charge.discount_amount + charge.waiver_amount > charge.base_amount:
            return Response(
                {"success": False, "error": "Total reductions cannot exceed the base amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        charge.save(update_fields=[field, "updated_at"])

        FeeAdjustment.objects.create(
            charge=charge,
            adjustment_type=adjustment_type,
            previous_amount=prev,
            new_amount=new_amount,
            amount_changed=new_amount - prev,
            reason=reason,
            applied_by=request.user,
        )

        log_action(
            actor=request.user,
            action="FEE_ADJUSTED",
            obj=charge,
            school_id=charge.school_id,
            extra={"type": adjustment_type, "reason": reason},
        )

        return Response({"success": True, "data": StudentChargeSerializer(charge).data})


class FeeAdjustmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeeAdjustmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["charge"]

    def get_queryset(self):
        charge_id = self.request.query_params.get("charge")
        if charge_id:
            return FeeAdjustment.objects.filter(charge_id=charge_id).select_related("applied_by")
        return FeeAdjustment.objects.none()
