from django.urls import path, include
from rest_framework.routers import DefaultRouter
from academics.views import EnrollmentViewSet

router = DefaultRouter()
router.register("", EnrollmentViewSet, basename="enrollments")
urlpatterns = [path("", include(router.urls))]
