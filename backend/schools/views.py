from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import School, SchoolSettings, SchoolBranch
from .serializers import SchoolSerializer, SchoolSettingsSerializer, SchoolBranchSerializer
from accounts.permissions import CanManageUsers


class SchoolViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SchoolSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return School.objects.all()
        school_ids = user.memberships.filter(is_active=True).values_list("school_id", flat=True)
        return School.objects.filter(id__in=school_ids)

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def school_settings(self, request, pk=None):
        school = self.get_object()
        school_settings, _ = SchoolSettings.objects.get_or_create(school=school)
        if request.method == "GET":
            return Response(SchoolSettingsSerializer(school_settings).data)
        serializer = SchoolSettingsSerializer(school_settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})
