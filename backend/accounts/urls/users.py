from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, RoleViewSet, PermissionListView, SchoolMembershipViewSet

router = DefaultRouter()
router.register("", UserViewSet, basename="users")

role_router = DefaultRouter()
role_router.register("roles", RoleViewSet, basename="roles")

membership_router = DefaultRouter()
membership_router.register("memberships", SchoolMembershipViewSet, basename="memberships")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(role_router.urls)),
    path("", include(membership_router.urls)),
    path("permissions/", PermissionListView.as_view(), name="permissions-list"),
]
