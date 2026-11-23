"""
INCOME – Accounts views: auth, user CRUD, roles, memberships.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, Permission, RolePermission, SchoolMembership
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    ChangePasswordSerializer,
    RoleSerializer,
    PermissionSerializer,
    SchoolMembershipSerializer,
)
from .permissions import CanManageUsers
from audit.utils import log_action

User = get_user_model()


# ---------------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------------
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"success": True, "message": "Logged out successfully."})
        except Exception:
            return Response({"success": True, "message": "Logged out."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        memberships = request.user.memberships.filter(is_active=True).select_related("school", "role")
        data = serializer.data
        data["memberships"] = [
            {
                "school_id": str(m.school_id),
                "school_name": m.school.name,
                "role_id": str(m.role_id),
                "role_name": m.role.name,
                "role_slug": m.role.slug,
            }
            for m in memberships
        ]
        return Response({"success": True, "data": data})

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"success": False, "error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "must_change_password", "password_changed_at"])

        return Response({"success": True, "message": "Password changed successfully."})


# ---------------------------------------------------------------------------
# User management (school admins)
# ---------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")
        if school_id:
            user_ids = SchoolMembership.objects.filter(
                school_id=school_id, is_active=True
            ).values_list("user_id", flat=True)
            return User.objects.filter(id__in=user_ids).order_by("last_name", "first_name")
        return User.objects.none()

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(
            actor=self.request.user,
            action="USER_CREATED",
            obj=user,
            school_id=self.request.data.get("school"),
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        log_action(actor=request.user, action="USER_DEACTIVATED", obj=user)
        return Response({"success": True, "message": "User deactivated."})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        log_action(actor=request.user, action="USER_ACTIVATED", obj=user)
        return Response({"success": True, "message": "User activated."})


# ---------------------------------------------------------------------------
# Roles and Permissions
# ---------------------------------------------------------------------------
class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = RoleSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")
        if school_id:
            return Role.objects.filter(school_id=school_id, is_active=True)
        return Role.objects.none()


class PermissionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all().order_by("module", "codename")


# ---------------------------------------------------------------------------
# School Membership
# ---------------------------------------------------------------------------
class SchoolMembershipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = SchoolMembershipSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")
        if school_id:
            return SchoolMembership.objects.filter(
                school_id=school_id
            ).select_related("user", "role", "school").order_by("user__last_name")
        return SchoolMembership.objects.none()

    def perform_create(self, serializer):
        membership = serializer.save(created_by=self.request.user)
        log_action(
            actor=self.request.user,
            action="MEMBERSHIP_CREATED",
            obj=membership,
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        membership = self.get_object()
        membership.is_active = False
        membership.deactivated_at = timezone.now()
        membership.save(update_fields=["is_active", "deactivated_at"])
        return Response({"success": True, "message": "Membership deactivated."})
