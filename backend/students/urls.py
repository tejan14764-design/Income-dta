from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, GuardianViewSet, StudentGuardianViewSet

router = DefaultRouter()
router.register("", StudentViewSet, basename="students")

guardian_router = DefaultRouter()
guardian_router.register("guardians", GuardianViewSet, basename="guardians")

student_guardian_router = DefaultRouter()
student_guardian_router.register("student-guardians", StudentGuardianViewSet, basename="student-guardians")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(guardian_router.urls)),
    path("", include(student_guardian_router.urls)),
]
