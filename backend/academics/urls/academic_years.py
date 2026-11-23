from django.urls import path, include
from rest_framework.routers import DefaultRouter
from academics.views import AcademicYearViewSet

router = DefaultRouter()
router.register("", AcademicYearViewSet, basename="academic-years")
urlpatterns = [path("", include(router.urls))]
