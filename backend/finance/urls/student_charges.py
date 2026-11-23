from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finance.views import StudentChargeViewSet

router = DefaultRouter()
router.register("", StudentChargeViewSet, basename="student-charges")

urlpatterns = [path("", include(router.urls))]
