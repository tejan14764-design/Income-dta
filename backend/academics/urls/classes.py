from django.urls import path, include
from rest_framework.routers import DefaultRouter
from academics.views import ClassViewSet

router = DefaultRouter()
router.register("", ClassViewSet, basename="classes")
urlpatterns = [path("", include(router.urls))]
