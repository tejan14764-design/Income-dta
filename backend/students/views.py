"""
INCOME – Students views.
"""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters

from .models import Student, Guardian, StudentGuardian, StudentConfidentialInformation
from .serializers import (
    StudentListSerializer,
    StudentDetailSerializer,
    StudentCreateSerializer,
    GuardianSerializer,
    StudentGuardianSerializer,
    StudentConfidentialSerializer,
)
from accounts.permissions import CanRegisterStudents
from audit.utils import log_action


class StudentFilter(django_filters.FilterSet):
    school = django_filters.UUIDFilter(field_name="school_id")
    status = django_filters.CharFilter(field_name="status")
    gender = django_filters.CharFilter(field_name="gender")
    admission_date_from = django_filters.DateFilter(field_name="admission_date", lookup_expr="gte")
    admission_date_to = django_filters.DateFilter(field_name="admission_date", lookup_expr="lte")

    class Meta:
        model = Student
        fields = ["school", "status", "gender"]


class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StudentFilter
    search_fields = ["first_name", "last_name", "middle_name", "admission_number", "email"]
    ordering_fields = ["last_name", "first_name", "admission_number", "admission_date", "created_at"]
    ordering = ["last_name", "first_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        if self.action == "create":
            return StudentCreateSerializer
        return StudentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        school_id = self.request.query_params.get("school")
        if school_id:
            return Student.objects.filter(school_id=school_id).prefetch_related(
                "student_guardians__guardian", "enrollments__class_ref", "enrollments__academic_year"
            )
        if user.is_superuser:
            return Student.objects.all()
        school_ids = user.memberships.filter(is_active=True).values_list("school_id", flat=True)
        return Student.objects.filter(school_id__in=school_ids).prefetch_related(
            "student_guardians__guardian", "enrollments__class_ref", "enrollments__academic_year"
        )

    def perform_create(self, serializer):
        student = serializer.save(created_by=self.request.user)
        log_action(
            actor=self.request.user,
            action="STUDENT_REGISTERED",
            obj=student,
            school_id=student.school_id,
        )

    def perform_update(self, serializer):
        student = serializer.save()
        log_action(
            actor=self.request.user,
            action="STUDENT_UPDATED",
            obj=student,
            school_id=student.school_id,
        )

    @action(detail=True, methods=["get", "patch"])
    def confidential(self, request, pk=None):
        """View or update confidential student information."""
        student = self.get_object()
        # Only users with disability access permission can view this
        info, _ = StudentConfidentialInformation.objects.get_or_create(student=student)
        if request.method == "GET":
            return Response(StudentConfidentialSerializer(info).data)
        serializer = StudentConfidentialSerializer(info, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(
            actor=request.user,
            action="STUDENT_CONFIDENTIAL_UPDATED",
            obj=student,
            school_id=student.school_id,
        )
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["get"])
    def financial_summary(self, request, pk=None):
        """Return financial summary for a student."""
        student = self.get_object()
        from finance.utils import get_student_financial_summary
        summary = get_student_financial_summary(student)
        return Response({"success": True, "data": summary})


class GuardianViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GuardianSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["first_name", "last_name", "phone_number", "email"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return Guardian.objects.filter(school_id=school_id)
        return Guardian.objects.none()


class StudentGuardianViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentGuardianSerializer

    def get_queryset(self):
        student_id = self.request.query_params.get("student")
        if student_id:
            return StudentGuardian.objects.filter(
                student_id=student_id
            ).select_related("guardian")
        return StudentGuardian.objects.none()
