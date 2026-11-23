from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views import PaymentVerificationViewSet

router = DefaultRouter()
router.register("", PaymentVerificationViewSet, basename="payment-verification")
urlpatterns = [path("", include(router.urls))]
