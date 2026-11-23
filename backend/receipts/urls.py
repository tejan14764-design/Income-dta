from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReceiptViewSet

router = DefaultRouter()
router.register("", ReceiptViewSet, basename="receipts")
urlpatterns = [path("", include(router.urls))]
