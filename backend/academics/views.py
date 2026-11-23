from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import AcademicYear, Class, Enrollment
from .serializers import AcademicYearSerializer, ClassSerializer, EnrollmentSerializer
from audit.utils import log_action


class AcademicYearViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicYearSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["school", "status", "is_current"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return AcademicYear.objects.filter(school_id=school_id)
        if self.request.user.is_superuser:
            return AcademicYear.objects.all()
        school_ids = self.request.user.memberships.filter(is_active=True).values_list("school_id", flat=True)
        return AcademicYear.objects.filter(school_id__in=school_ids)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        year = self.get_object()
        year.status = AcademicYear.Status.ACTIVE
        year.is_current = True
        year.save()
        log_action(actor=request.user, action="ACADEMIC_YEAR_ACTIVATED", obj=year, school_id=year.school_id)
        return Response({"success": True, "message": f"{year.name} is now active."})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        year = self.get_object()
        year.status = AcademicYear.Status.CLOSED
        year.is_current = False
        year.save()
        log_action(actor=request.user, action="ACADEMIC_YEAR_CLOSED", obj=year, school_id=year.school_id)
        return Response({"success": True, "message": f"{year.name} has been closed."})


class ClassViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ClassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["school", "is_active"]
    search_fields = ["name", "short_name"]
    ordering_fields = ["level", "name"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return Class.objects.filter(school_id=school_id)
        if self.request.user.is_superuser:
            return Class.objects.all()
        school_ids = self.request.user.memberships.filter(is_active=True).values_list("school_id", flat=True)
        return Class.objects.filter(school_id__in=school_ids)


class EnrollmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["school", "academic_year", "class_ref", "status", "is_active"]
    search_fields = ["student__first_name", "student__last_name", "student__admission_number"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return Enrollment.objects.filter(
                school_id=school_id
            ).select_related("student", "class_ref", "academic_year")
        return Enrollment.objects.none()

    def perform_create(self, serializer):
        enrollment = serializer.save(
            created_by=self.request.user,
            school=serializer.validated_data["academic_year"].school,
        )
        log_action(
            actor=self.request.user,
            action="STUDENT_ENROLLED",
            obj=enrollment,
            school_id=enrollment.school_id,
        )
