"""
INCOME – Root URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django Admin
    path("django-admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("accounts.urls.auth")),
    path("api/v1/users/", include("accounts.urls.users")),
    path("api/v1/schools/", include("schools.urls")),
    path("api/v1/students/", include("students.urls")),
    path("api/v1/classes/", include("academics.urls.classes")),
    path("api/v1/academic-years/", include("academics.urls.academic_years")),
    path("api/v1/enrollments/", include("academics.urls.enrollments")),
    path("api/v1/fees/", include("finance.urls.fees")),
    path("api/v1/student-charges/", include("finance.urls.student_charges")),
    path("api/v1/payments/", include("payments.urls.payments")),
    path("api/v1/payment-verification/", include("payments.urls.verification")),
    path("api/v1/receipts/", include("receipts.urls")),
    path("api/v1/reports/", include("reports.urls")),
    path("api/v1/audit/", include("audit.urls")),
    path("api/v1/dashboard/", include("reports.urls_dashboard")),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
