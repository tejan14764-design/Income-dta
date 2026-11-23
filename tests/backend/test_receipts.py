"""
Tests: Receipt generation, unique numbering, reprint logging, PDF bytes.
"""
import pytest
from decimal import Decimal


@pytest.mark.django_db
class TestReceiptGeneration:
    def _make_confirmed_payment(self, school, student, academic_year, user):
        from payments.models import Payment, PaymentStatus
        return Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="cash", amount=Decimal("300.00"),
            payment_date="2024-10-01", status=PaymentStatus.CONFIRMED,
            recorded_by=user, verified_by=user,
        )

    def test_receipt_generated_for_confirmed_payment(
        self, school, student, academic_year, admin_user
    ):
        from receipts.services import generate_receipt_for_payment
        payment = self._make_confirmed_payment(school, student, academic_year, admin_user)
        receipt = generate_receipt_for_payment(payment, admin_user)
        assert receipt.receipt_number.startswith("RCP-TST-")
        assert receipt.student_name == student.full_name
        assert receipt.amount_paid == Decimal("300.00")

    def test_idempotent_receipt_generation(self, school, student, academic_year, admin_user):
        """Generating a receipt twice should return the same receipt."""
        from receipts.services import generate_receipt_for_payment
        from receipts.models import Receipt
        payment = self._make_confirmed_payment(school, student, academic_year, admin_user)
        r1 = generate_receipt_for_payment(payment, admin_user)
        r2 = generate_receipt_for_payment(payment, admin_user)
        assert r1.id == r2.id
        assert Receipt.objects.filter(payment=payment).count() == 1

    def test_receipt_numbers_are_sequential(self, school, student, academic_year, admin_user):
        from receipts.services import generate_receipt_for_payment, generate_receipt_number
        from payments.models import Payment, PaymentStatus
        p1 = Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="cash", amount=Decimal("100.00"),
            payment_date="2024-10-01", status=PaymentStatus.CONFIRMED,
            recorded_by=admin_user,
        )
        p2 = Payment.objects.create(
            school=school, student=student, academic_year=academic_year,
            payment_method="cash", amount=Decimal("200.00"),
            payment_date="2024-10-02", status=PaymentStatus.CONFIRMED,
            recorded_by=admin_user,
        )
        r1 = generate_receipt_for_payment(p1, admin_user)
        r2 = generate_receipt_for_payment(p2, admin_user)
        num1 = int(r1.receipt_number.split("-")[-1])
        num2 = int(r2.receipt_number.split("-")[-1])
        assert num2 == num1 + 1

    def test_pdf_bytes_generated(self, school, student, academic_year, admin_user):
        from receipts.services import generate_receipt_for_payment, generate_receipt_pdf
        payment = self._make_confirmed_payment(school, student, academic_year, admin_user)
        receipt = generate_receipt_for_payment(payment, admin_user)
        pdf_bytes = generate_receipt_pdf(receipt)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Valid PDF starts with %PDF
        assert pdf_bytes[:4] == b"%PDF"

    def test_reprint_logs_event(self, school, student, academic_year, admin_user, auth_client):
        from receipts.services import generate_receipt_for_payment
        from receipts.models import ReceiptPrintLog
        payment = self._make_confirmed_payment(school, student, academic_year, admin_user)
        receipt = generate_receipt_for_payment(payment, admin_user)
        resp = auth_client.post(f"/api/v1/receipts/{receipt.id}/reprint/", {"notes": "Customer requested copy"})
        assert resp.status_code == 200
        reprints = ReceiptPrintLog.objects.filter(receipt=receipt, print_type="reprint")
        assert reprints.exists()
