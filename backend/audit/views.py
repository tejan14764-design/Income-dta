from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog
from accounts.permissions import CanViewAuditLogs


class AuditLogSerializer(ModelSerializer):
    actor_name = __import__("rest_framework.serializers", fromlist=["SerializerMethodField"]).SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "school", "actor", "actor_name", "action",
            "object_type", "object_id", "object_repr",
            "previous_data", "new_data", "extra",
            "ip_address", "timestamp",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() if obj.actor else "System"


class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CanViewAuditLogs]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["school", "action", "object_type"]
    search_fields = ["action", "object_repr", "actor__username"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school")
        if school_id:
            return AuditLog.objects.filter(school_id=school_id).select_related("actor", "school")
        if self.request.user.is_superuser:
            return AuditLog.objects.all().select_related("actor", "school")
        return AuditLog.objects.none()
