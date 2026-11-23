"""
INCOME – Reports and CSV Export views.
"""

import csv
import io
from decimal import Decimal
from django.http import HttpResponse, StreamingHttpResponse
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from students.models import Student
from finance.models import StudentCharge
from payments.models import Payment, PaymentAllocation, PaymentStatus
from academics.models import Enrollment
from finance.utils import get_student_financial_summary, quantize
from accounts.permissions import CanViewReports
from audit.utils import log_action
from .models import ExportLog

ZERO = Decimal("0.00")


def _escape_csv_value(value):
    """Prevent CSV formula injection by prefixing dangerous characters."""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "|", "%"):
        s = "'" + s
    return s


class FinancialReportView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        school_id = request.query_params.get("school")
        academic_year_id = request.query_params.get("academic_year")
        class_id = request.query_params.get("class_id")
        payment_status = request.query_params.get("payment_status")

        if not school_id or not academic_year_id:
            return Response({"success": False, "error": "school and academic_year are required."}, status=400)

        # Get enrollments for the year (and optionally class)
        enrollment_qs = Enrollment.objects.filter(
            school_id=school_id,
            academic_year_id=academic_year_id,
            is_active=True,
        ).select_related("student", "class_ref")

        if class_id:
            enrollment_qs = enrollment_qs.filter(class_ref_id=class_id)

        rows = []
        total_expected = ZERO
        total_paid = ZERO
        total_outstanding = ZERO
        counts = {"fully_paid": 0, "partially_paid": 0, "unpaid": 0}

        for enrollment in enrollment_qs:
            student = enrollment.student
            summary = get_student_financial_summary(student, enrollment.academic_year)

            if payment_status and summary["payment_status"] != payment_status:
                continue

            row = {
                "admission_number": student.admission_number,
                "student_name": student.full_name,
                "class": enrollment.class_ref.name,
                "academic_year": enrollment.academic_year.name,
                "total_expected": summary["total_expected"],
                "total_paid": summary["total_paid"],
                "outstanding": summary["outstanding"],
                "payment_status": summary["payment_status"].replace("_", " ").title(),
            }
            rows.append(row)

            total_expected += Decimal(summary["total_expected"])
            total_paid += Decimal(summary["total_paid"])
            total_outstanding += Decimal(summary["outstanding"])
            stat = summary["payment_status"]
            if stat in counts:
                counts[stat] += 1

        return Response({
            "success": True,
            "data": {
                "rows": rows,
                "summary": {
                    "total_students": len(rows),
                    "total_expected": str(quantize(total_expected)),
                    "total_collected": str(quantize(total_paid)),
                    "total_outstanding": str(quantize(total_outstanding)),
                    "fully_paid": counts["fully_paid"],
                    "partially_paid": counts["partially_paid"],
                    "unpaid": counts["unpaid"],
                },
            }
        })


class CSVExportView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        school_id = request.query_params.get("school")
        academic_year_id = request.query_params.get("academic_year")
        class_id = request.query_params.get("class_id")
        export_type = request.query_params.get("type", "financial_summary")

        if not school_id or not academic_year_id:
            return Response({"success": False, "error": "school and academic_year are required."}, status=400)

        enrollment_qs = Enrollment.objects.filter(
            school_id=school_id,
            academic_year_id=academic_year_id,
            is_active=True,
        ).select_related("student", "class_ref", "academic_year")

        if class_id:
            enrollment_qs = enrollment_qs.filter(class_ref_id=class_id)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        headers = [
            "Admission Number", "Student Name", "Class", "Academic Year",
            "Total Expected (NLe)", "Total Paid (NLe)", "Outstanding (NLe)", "Payment Status",
        ]
        writer.writerow(headers)

        row_count = 0
        for enrollment in enrollment_qs:
            student = enrollment.student
            summary = get_student_financial_summary(student, enrollment.academic_year)
            writer.writerow([
                _escape_csv_value(student.admission_number),
                _escape_csv_value(student.full_name),
                _escape_csv_value(enrollment.class_ref.name),
                _escape_csv_value(enrollment.academic_year.name),
                _escape_csv_value(summary["total_expected"]),
                _escape_csv_value(summary["total_paid"]),
                _escape_csv_value(summary["outstanding"]),
                _escape_csv_value(summary["payment_status"].replace("_", " ").title()),
            ])
            row_count += 1

        # Log the export
        ExportLog.objects.create(
            school_id=school_id,
            exported_by=request.user,
            export_type=export_type,
            filters_used={
                "academic_year": academic_year_id,
                "class": class_id,
            },
            row_count=row_count,
        )
        log_action(
            actor=request.user,
            action="CSV_EXPORTED",
            school_id=school_id,
            extra={"type": export_type, "rows": row_count},
        )

        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="financial-report.csv"'
        response.write("\ufeff")  # BOM for Excel compatibility
        return response


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get("school")
        academic_year_id = request.query_params.get("academic_year")

        if not school_id:
            return Response({"success": False, "error": "school is required."}, status=400)

        # Student counts
        total_students = Student.objects.filter(school_id=school_id, status="active").count()
        total_students_all = Student.objects.filter(school_id=school_id).count()

        from academics.models import Class, AcademicYear
        total_classes = Class.objects.filter(school_id=school_id, is_active=True).count()

        # Financial totals for active academic year
        payment_qs = Payment.objects.filter(school_id=school_id)
        if academic_year_id:
            payment_qs = payment_qs.filter(academic_year_id=academic_year_id)

        confirmed_total = payment_qs.filter(status=PaymentStatus.CONFIRMED).aggregate(
            total=Sum("amount")
        )["total"] or ZERO
        pending_count = payment_qs.filter(status=PaymentStatus.PENDING).count()

        # Charge totals
        charge_qs = StudentCharge.objects.filter(school_id=school_id, is_active=True)
        if academic_year_id:
            charge_qs = charge_qs.filter(academic_year_id=academic_year_id)

        charge_agg = charge_qs.aggregate(
            base_total=Sum("base_amount"),
            discount_total=Sum("discount_amount"),
            waiver_total=Sum("waiver_amount"),
        )
        base = charge_agg["base_total"] or ZERO
        disc = charge_agg["discount_total"] or ZERO
        waiv = charge_agg["waiver_total"] or ZERO
        total_expected = quantize(max(ZERO, base - disc - waiv))

        # Allocation totals for confirmed payments
        alloc_agg = PaymentAllocation.objects.filter(
            payment__school_id=school_id,
            payment__status=PaymentStatus.CONFIRMED,
            is_reversed=False,
        )
        if academic_year_id:
            alloc_agg = alloc_agg.filter(payment__academic_year_id=academic_year_id)

        total_allocated = quantize(alloc_agg.aggregate(total=Sum("amount_allocated"))["total"] or ZERO)
        total_outstanding = quantize(max(ZERO, total_expected - total_allocated))

        # Payment status distribution
        charge_status_counts = charge_qs.values("status").annotate(count=Count("id"))
        status_map = {item["status"]: item["count"] for item in charge_status_counts}

        # Recent transactions
        recent_payments = Payment.objects.filter(school_id=school_id).order_by("-created_at")[:5]
        recent_data = [
            {
                "id": str(p.id),
                "student_name": p.student.full_name,
                "amount": str(p.amount),
                "method": p.payment_method,
                "status": p.status,
                "date": str(p.payment_date),
            }
            for p in recent_payments
        ]

        # Monthly payment collection (last 6 months)
        from django.db.models.functions import TruncMonth
        monthly = (
            Payment.objects.filter(school_id=school_id, status=PaymentStatus.CONFIRMED)
            .annotate(month=TruncMonth("payment_date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")[:6]
        )

        return Response({
            "success": True,
            "data": {
                "total_students": total_students,
                "total_students_all": total_students_all,
                "total_classes": total_classes,
                "total_expected": str(total_expected),
                "total_confirmed_payments": str(quantize(confirmed_total)),
                "total_outstanding": str(total_outstanding),
                "pending_verification_count": pending_count,
                "charge_status_distribution": status_map,
                "recent_transactions": recent_data,
                "monthly_collection": [
                    {"month": str(m["month"]), "total": str(m["total"])}
                    for m in monthly
                ],
            }
        })
