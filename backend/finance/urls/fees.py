from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finance.views import (
    FeeCategoryViewSet, FeeTemplateViewSet, FeeTemplateItemViewSet,
    StudentFeeAssignmentViewSet, StudentChargeViewSet, FeeAdjustmentViewSet,
)

router = DefaultRouter()
router.register("categories", FeeCategoryViewSet, basename="fee-categories")
router.register("templates", FeeTemplateViewSet, basename="fee-templates")
router.register("template-items", FeeTemplateItemViewSet, basename="fee-template-items")
router.register("assignments", StudentFeeAssignmentViewSet, basename="fee-assignments")
router.register("adjustments", FeeAdjustmentViewSet, basename="fee-adjustments")

urlpatterns = [path("", include(router.urls))]
