from django.urls import path
from .views import FinancialReportView, CSVExportView

urlpatterns = [
    path("financial/", FinancialReportView.as_view(), name="financial-report"),
    path("export/csv/", CSVExportView.as_view(), name="csv-export"),
]
