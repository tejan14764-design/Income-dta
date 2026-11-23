"""
INCOME – Custom DRF permissions.
School-scoped, role-based permission checks.
"""

from rest_framework.permissions import BasePermission
from .models import SchoolMembership


def get_user_school_role(user, school_id):
    """Return the active SchoolMembership for a user in a given school."""
    try:
        return SchoolMembership.objects.select_related("role").get(
            user=user, school_id=school_id, is_active=True
        )
    except SchoolMembership.DoesNotExist:
        return None


def user_has_permission(user, school_id, codename):
    """Check if a user has a specific permission in a school."""
    if user.is_superuser:
        return True
    membership = get_user_school_role(user, school_id)
    if not membership:
        return False
    return membership.role.role_permissions.filter(
        permission__codename=codename
    ).exists()


def user_has_role(user, school_id, role_slug):
    """Check if a user holds a specific role slug in a school."""
    if user.is_superuser:
        return True
    membership = get_user_school_role(user, school_id)
    return membership is not None and membership.role.slug == role_slug


def user_has_any_role(user, school_id, role_slugs):
    """Check if a user holds any of the given role slugs in a school."""
    if user.is_superuser:
        return True
    membership = get_user_school_role(user, school_id)
    return membership is not None and membership.role.slug in role_slugs


# ---------------------------------------------------------------------------
# DRF Permission classes
# ---------------------------------------------------------------------------
class IsSchoolMember(BasePermission):
    """User must have an active membership in the requested school."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        school_id = view.kwargs.get("school_id") or request.query_params.get("school_id")
        if not school_id:
            # Allow if school_id resolved from token/session in view
            return True
        return bool(get_user_school_role(request.user, school_id))


class CanRegisterStudents(BasePermission):
    message = "You do not have permission to register students."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "students.register")


class CanManageFinance(BasePermission):
    message = "You do not have permission to manage financial records."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "finance.manage")


class CanRecordPayments(BasePermission):
    message = "You do not have permission to record payments."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "payments.record")


class CanVerifyPayments(BasePermission):
    message = "You do not have permission to verify payments."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "payments.verify")


class CanViewReports(BasePermission):
    message = "You do not have permission to view reports."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "reports.view")


class CanManageUsers(BasePermission):
    message = "You do not have permission to manage users."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "users.manage")


class CanViewAuditLogs(BasePermission):
    message = "You do not have permission to view audit logs."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        school_id = _get_school_id(request, view)
        return user_has_permission(request.user, school_id, "audit.view")


def _get_school_id(request, view):
    """Helper to extract school_id from various sources."""
    return (
        view.kwargs.get("school_id")
        or request.data.get("school")
        or request.query_params.get("school_id")
        or getattr(request.user, "_active_school_id", None)
    )
