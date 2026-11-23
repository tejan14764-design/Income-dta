"""
Tests: Financial calculation engine — the most critical tests in the system.
Covers: net amounts, discounts, waivers, payment allocation, duplicate prevention,
overpayment prevention, reversal, and outstanding balance accuracy.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError


@pytest.mark.django_db
class TestNetAmountCalculation:
    def test_net_amount_no_discounts(self, student_charge):
        assert student_charge.net_amount == Decimal("500.00")

    def test_net_amount_with_discount(self, student_charge):
        student_charge.discount_amount = Decimal("50.00")
        student_charge.save()
        assert student_charge.net_amount == Decimal("450.00")

    def test_net_amount_with_waiver(self, student_charge):
        student_charge.waiver_amount = Decimal("100.00")
        student_charge.save()
        assert student_charge.net_amount == Decimal("400.00")

    def test_net_amount_combined_reductions(self, student_charge):
        student_charge.discount_amount = Decimal("50.00")
        student_charge.waiver_amount = Decimal("100.00")
        student_charge.save()
        assert student_charge.net_amount == Decimal("350.00")

    def test_net_amount_cannot_go_negative(self, student_charge):
        student_charge.discount_amount = Decimal("300.00")
        student_charge.waiver_amount = Decimal("300.00")
        student_charge.save()
        assert student_charge.net_amount == Decimal("0.00")

    def test_discount_plus_waiver_cannot_exceed_base_via_api(self, auth_client, student_charge):
        """The API must reject discounts + waivers > base amount."""
        resp = auth_client.patch(
            f"/api/v1/student-charges/{student_charge.id}/",
            {"discount_amount": "300.00", "waiver_amount": "300.00"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPaymentAllocation:
    def _make_confirmed_payment(self, school, student, academic_year, cashier, amount="300.00"):
        from payments.models import Payment, PaymentStatus
        payment = Payment.objects.create(
            school=school,
            student=student,
            academic_year=academic_year,
            payment_method="cash",
            amount=Decimal(amount),
            payment_date="2024-10-01",
            status=PaymentStatus.CONFIRMED,
            recorded_by=cashier,
            verified_by=cashier,
        )
        return payment

    def test_full_allocation(self, school, student, academic_year, student_charge, cashier_user):
        from payments.services import allocate_payment
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "500.00")
        allocs = allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("500.00")}])
        assert len(allocs) == 1
        assert allocs[0].amount_allocated == Decimal("500.00")

    def test_partial_allocation(self, school, student, academic_year, student_charge, cashier_user):
        from payments.services import allocate_payment
        from finance.utils import get_student_financial_summary
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "200.00")
        allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("200.00")}])
        summary = get_student_financial_summary(student, academic_year)
        assert Decimal(summary["total_paid"]) == Decimal("200.00")
        assert Decimal(summary["outstanding"]) == Decimal("300.00")

    def test_allocation_cannot_exceed_payment_amount(self, school, student, academic_year, student_charge, cashier_user):
        from payments.services import allocate_payment
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "100.00")
        with pytest.raises(ValueError, match="exceed payment amount"):
            allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("200.00")}])

    def test_allocation_cannot_over_settle_charge(self, school, student, academic_year, student_charge, cashier_user):
        from payments.services import allocate_payment
        p1 = self._make_confirmed_payment(school, student, academic_year, cashier_user, "400.00")
        allocate_payment(p1, [{"charge_id": str(student_charge.id), "amount": Decimal("400.00")}])
        p2 = self._make_confirmed_payment(school, student, academic_year, cashier_user, "200.00")
        with pytest.raises(ValueError, match="over-settled"):
            allocate_payment(p2, [{"charge_id": str(student_charge.id), "amount": Decimal("200.00")}])

    def test_pending_payment_not_counted(self, school, student, academic_year, student_charge, cashier_user):
        from payments.models import Payment, PaymentStatus
        from finance.utils import get_student_financial_summary
        # Create a PENDING payment (not confirmed)
        Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("300.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="TEST-REF-001",
        )
        summary = get_student_financial_summary(student, academic_year)
        # Pending should NOT count as paid
        assert Decimal(summary["total_paid"]) == Decimal("0.00")
        assert Decimal(summary["outstanding"]) == Decimal("500.00")

    def test_payment_reversal_recalculates_outstanding(
        self, school, student, academic_year, student_charge, cashier_user, financial_officer
    ):
        from payments.services import allocate_payment, reverse_payment
        from finance.utils import get_student_financial_summary
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "300.00")
        allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("300.00")}])

        # Verify paid = 300
        summary = get_student_financial_summary(student, academic_year)
        assert Decimal(summary["total_paid"]) == Decimal("300.00")

        # Reverse it
        reverse_payment(payment, financial_officer, "Payment made in error")

        # Outstanding should be back to 500
        summary_after = get_student_financial_summary(student, academic_year)
        assert Decimal(summary_after["total_paid"]) == Decimal("0.00")
        assert Decimal(summary_after["outstanding"]) == Decimal("500.00")

    def test_payment_progress_calculation(
        self, school, student, academic_year, student_charge, cashier_user
    ):
        from payments.services import allocate_payment
        from finance.utils import get_student_financial_summary
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "250.00")
        allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("250.00")}])
        summary = get_student_financial_summary(student, academic_year)
        assert Decimal(summary["payment_progress"]) == Decimal("50.00")
        assert summary["payment_status"] == "partially_paid"

    def test_fully_paid_status(
        self, school, student, academic_year, student_charge, cashier_user
    ):
        from payments.services import allocate_payment
        from finance.utils import get_student_financial_summary
        payment = self._make_confirmed_payment(school, student, academic_year, cashier_user, "500.00")
        allocate_payment(payment, [{"charge_id": str(student_charge.id), "amount": Decimal("500.00")}])
        summary = get_student_financial_summary(student, academic_year)
        assert summary["payment_status"] == "fully_paid"
        assert Decimal(summary["outstanding"]) == Decimal("0.00")


@pytest.mark.django_db
class TestDuplicateTransactionPrevention:
    def test_duplicate_transaction_reference_rejected(self, school, student, academic_year, cashier_user):
        from payments.models import Payment, PaymentStatus
        Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("100.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="UNIQUE-REF-123",
        )
        with pytest.raises(Exception):
            Payment.objects.create(
                school=school, student=student, academic_year=academic_year,
                payment_method="mobile_money", amount=Decimal("100.00"),
                payment_date="2024-10-02", status=PaymentStatus.PENDING,
                recorded_by=cashier_user, transaction_reference="UNIQUE-REF-123",
            )

    def test_different_schools_can_share_same_reference(self, school, student, academic_year, cashier_user, db):
        """Two schools may legitimately have the same mobile money reference."""
        from payments.models import Payment, PaymentStatus
        from schools.models import School
        from students.models import Student

        other_school = School.objects.create(name="Other School", code="OTH2")
        other_student = Student.objects.create(
            school=other_school, admission_number="OTH-001",
            first_name="Jane", last_name="Doe", gender="female",
            date_of_birth="2010-01-01", admission_date="2024-09-01",
        )
        from academics.models import AcademicYear
        other_year = AcademicYear.objects.create(
            school=other_school, name="2024/2025",
            start_date="2024-09-01", end_date="2025-07-31",
        )
        Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("100.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="SHARED-REF-001",
        )
        # Same reference in a different school should succeed
        p2 = Payment.objects.create(
            school=other_school, student=other_student, academic_year=other_year,
            payment_method="mobile_money", amount=Decimal("200.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="SHARED-REF-001",
        )
        assert p2.pk is not None


@pytest.mark.django_db
class TestFeeAdjustments:
    def test_apply_discount_records_adjustment(self, auth_client, student_charge):
        resp = auth_client.post(
            f"/api/v1/student-charges/{student_charge.id}/adjust/",
            {"adjustment_type": "discount", "new_amount": "50.00", "reason": "Scholarship discount applied"},
            format="json",
        )
        assert resp.status_code == 200
        student_charge.refresh_from_db()
        assert student_charge.discount_amount == Decimal("50.00")

    def test_adjustment_requires_reason(self, auth_client, student_charge):
        resp = auth_client.post(
            f"/api/v1/student-charges/{student_charge.id}/adjust/",
            {"adjustment_type": "discount", "new_amount": "50.00", "reason": ""},
            format="json",
        )
        assert resp.status_code == 400

    def test_adjustment_history_created(self, auth_client, student_charge):
        auth_client.post(
            f"/api/v1/student-charges/{student_charge.id}/adjust/",
            {"adjustment_type": "waiver", "new_amount": "100.00", "reason": "Full waiver approved by principal"},
            format="json",
        )
        from finance.models import FeeAdjustment
        adj = FeeAdjustment.objects.filter(charge=student_charge).first()
        assert adj is not None
        assert adj.adjustment_type == "waiver"
        assert adj.new_amount == Decimal("100.00")
