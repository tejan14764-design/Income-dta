"""
Tests: Payment recording, verification, rejection, reversal, separation of duties.
"""
import pytest
from decimal import Decimal


@pytest.mark.django_db
class TestPaymentRecording:
    def test_cash_payment_auto_confirmed(self, auth_client, school, student, academic_year):
        resp = auth_client.post("/api/v1/payments/", {
            "school": str(school.id),
            "student": str(student.id),
            "academic_year": str(academic_year.id),
            "payment_method": "cash",
            "amount": "200.00",
            "payment_date": "2024-10-15",
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["status"] == "confirmed"

    def test_mobile_money_starts_pending(self, auth_client, school, student, academic_year):
        resp = auth_client.post("/api/v1/payments/", {
            "school": str(school.id),
            "student": str(student.id),
            "academic_year": str(academic_year.id),
            "payment_method": "mobile_money",
            "amount": "200.00",
            "payment_date": "2024-10-15",
            "transaction_reference": "MM-TEST-001",
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    def test_mobile_money_requires_reference(self, auth_client, school, student, academic_year):
        resp = auth_client.post("/api/v1/payments/", {
            "school": str(school.id),
            "student": str(student.id),
            "academic_year": str(academic_year.id),
            "payment_method": "mobile_money",
            "amount": "200.00",
            "payment_date": "2024-10-15",
            # No transaction_reference
        }, format="json")
        assert resp.status_code == 400

    def test_zero_amount_rejected(self, auth_client, school, student, academic_year):
        resp = auth_client.post("/api/v1/payments/", {
            "school": str(school.id),
            "student": str(student.id),
            "academic_year": str(academic_year.id),
            "payment_method": "cash",
            "amount": "0.00",
            "payment_date": "2024-10-15",
        }, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestSeparationOfDuties:
    def test_cashier_cannot_verify_own_payment(self, school, student, academic_year, cashier_user):
        from payments.models import Payment, PaymentStatus
        from payments.services import confirm_payment
        payment = Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("300.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="DUTY-TEST-001",
        )
        # Simulate the API's separation of duties check
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        client = APIClient()
        refresh = RefreshToken.for_user(cashier_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = client.post(
            f"/api/v1/payment-verification/{payment.id}/confirm/",
            {"allocations": []},
            format="json",
        )
        assert resp.status_code == 403

    def test_different_officer_can_verify(self, school, student, academic_year, cashier_user, financial_officer):
        from payments.models import Payment, PaymentStatus
        from payments.services import confirm_payment
        payment = Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("300.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference="DUTY-TEST-002",
        )
        confirmed = confirm_payment(payment, financial_officer)
        assert confirmed.status == PaymentStatus.CONFIRMED
        assert confirmed.verified_by == financial_officer


@pytest.mark.django_db
class TestPaymentVerification:
    def _pending_payment(self, school, student, academic_year, cashier_user, ref="VER-001"):
        from payments.models import Payment, PaymentStatus
        return Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="mobile_money", amount=Decimal("300.00"),
            payment_date="2024-10-01", status=PaymentStatus.PENDING,
            recorded_by=cashier_user, transaction_reference=ref,
        )

    def test_confirm_changes_status(self, school, student, academic_year, cashier_user, financial_officer):
        from payments.services import confirm_payment
        from payments.models import PaymentStatus
        p = self._pending_payment(school, student, academic_year, cashier_user)
        confirmed = confirm_payment(p, financial_officer)
        assert confirmed.status == PaymentStatus.CONFIRMED

    def test_reject_changes_status(self, school, student, academic_year, cashier_user, financial_officer):
        from payments.services import reject_payment
        from payments.models import PaymentStatus
        p = self._pending_payment(school, student, academic_year, cashier_user, ref="VER-002")
        rejected = reject_payment(p, financial_officer, "Invalid transaction reference")
        assert rejected.status == PaymentStatus.REJECTED
        assert "Invalid" in rejected.rejection_reason

    def test_reject_requires_reason(self, school, student, academic_year, cashier_user, financial_officer):
        from payments.services import reject_payment
        p = self._pending_payment(school, student, academic_year, cashier_user, ref="VER-003")
        with pytest.raises(ValueError, match="reason is required"):
            reject_payment(p, financial_officer, "")

    def test_cannot_confirm_already_confirmed(self, school, student, academic_year, cashier_user, financial_officer):
        from payments.services import confirm_payment
        from payments.models import PaymentStatus
        p = self._pending_payment(school, student, academic_year, cashier_user, ref="VER-004")
        confirm_payment(p, financial_officer)
        with pytest.raises(ValueError):
            confirm_payment(p, financial_officer)
