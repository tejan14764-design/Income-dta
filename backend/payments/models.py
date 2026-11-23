"""
INCOME – Payments models.
Payment, PaymentAllocation, PaymentEvidence, PaymentReversal, StudentCreditTransaction.
All monetary fields use DecimalField.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator

ZERO = Decimal("0.00")


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    MOBILE_MONEY = "mobile_money", "Mobile Money"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CHEQUE = "cheque", "Cheque"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending Verification"
    CONFIRMED = "confirmed", "Confirmed"
    REJECTED = "rejected", "Rejected"
    REVERSED = "reversed", "Reversed"
    REFUNDED = "refunded", "Refunded"


class Payment(models.Model):
    """
    A single payment transaction.
    Cash payments may be confirmed immediately by an authorised cashier.
    Mobile money / bank payments require verification before confirmation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="payments"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="payments"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.PROTECT, related_name="payments"
    )

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    payment_date = models.DateField()
    status = models.CharField(
        max_length=25, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    # Mobile money / bank fields
    transaction_reference = models.CharField(max_length=255, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    payer_phone = models.CharField(max_length=20, blank=True)

    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Staff audit
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True,
        related_name="payments_recorded"
    )
    verified_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments_verified"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments_rejected"
    )
    rejected_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["school", "student", "status"]),
            models.Index(fields=["school", "academic_year", "status"]),
            models.Index(fields=["transaction_reference"]),
        ]
        # Prevent exact duplicate transaction references per school
        constraints = [
            models.UniqueConstraint(
                fields=["school", "transaction_reference"],
                condition=~models.Q(transaction_reference=""),
                name="unique_transaction_ref_per_school",
            )
        ]

    def __str__(self):
        return f"Payment {self.id}: {self.student} – {self.amount} ({self.status})"


class PaymentAllocation(models.Model):
    """
    Links a confirmed Payment to one or more StudentCharge records.
    The sum of all allocations for a payment must not exceed payment.amount.
    A single charge must not be over-settled.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="allocations")
    charge = models.ForeignKey(
        "finance.StudentCharge", on_delete=models.PROTECT, related_name="allocations"
    )
    amount_allocated = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    is_reversed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_allocations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment"]),
            models.Index(fields=["charge"]),
        ]

    def __str__(self):
        return f"Allocation {self.payment_id} → {self.charge_id}: {self.amount_allocated}"


def evidence_upload_path(instance, filename):
    """Secure, non-guessable upload path for payment evidence."""
    return f"evidence/{instance.payment.school_id}/{instance.payment_id}/{filename}"


class PaymentEvidence(models.Model):
    """
    Uploaded evidence files for mobile money / bank payments.
    Private – never publicly accessible via predictable URLs.
    """

    class EvidenceType(models.TextChoices):
        SMS_SCREENSHOT = "sms_screenshot", "SMS Screenshot"
        TRANSACTION_SCREENSHOT = "transaction_screenshot", "Transaction Screenshot"
        BANK_RECEIPT = "bank_receipt", "Bank Receipt"
        DEPOSIT_SLIP = "deposit_slip", "Deposit Slip"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="evidence_files")
    evidence_type = models.CharField(max_length=30, choices=EvidenceType.choices)
    file = models.FileField(upload_to=evidence_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_evidence"

    def __str__(self):
        return f"Evidence for {self.payment_id}: {self.original_filename}"


class PaymentReversal(models.Model):
    """Records a payment reversal (must be authorized by financial officer)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="reversal")
    reason = models.TextField()
    reversed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="reversals_made"
    )
    authorized_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reversals_authorized"
    )
    reversed_at = models.DateTimeField(auto_now_add=True)
    refund_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, validators=[MinValueValidator(ZERO)]
    )

    class Meta:
        db_table = "payment_reversals"

    def __str__(self):
        return f"Reversal of {self.payment_id}"


class StudentCreditTransaction(models.Model):
    """
    Tracks credit balances when a student has overpaid.
    Positive amount = credit. Negative = credit used.
    """

    class TransactionType(models.TextChoices):
        CREDIT_ADDED = "credit_added", "Credit Added"
        CREDIT_USED = "credit_used", "Credit Used"
        REFUND = "refund", "Refund Issued"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="credit_transactions"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="credit_transactions"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.PROTECT, related_name="credit_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reference_payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "student_credit_transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Credit {self.transaction_type}: {self.student} {self.amount}"
