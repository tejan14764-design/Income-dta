"""
INCOME – Receipts models.
"""

import uuid
from django.db import models


class Receipt(models.Model):
    """Generated receipt for a confirmed payment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="receipts"
    )
    payment = models.OneToOneField(
        "payments.Payment", on_delete=models.PROTECT, related_name="receipt"
    )
    receipt_number = models.CharField(max_length=50)
    student_name = models.CharField(max_length=255)
    student_admission_number = models.CharField(max_length=50)
    class_name = models.CharField(max_length=100, blank=True)
    academic_year_name = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    outstanding_after = models.DecimalField(max_digits=14, decimal_places=2)
    fee_descriptions = models.JSONField(default=list)  # list of {description, amount}
    transaction_reference = models.CharField(max_length=255, blank=True)
    cashier_name = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    pdf_file = models.FileField(upload_to="receipts/pdfs/%Y/%m/", null=True, blank=True)

    class Meta:
        db_table = "receipts"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["school", "receipt_number"]),
            models.Index(fields=["payment"]),
        ]

    def __str__(self):
        return f"Receipt {self.receipt_number} – {self.student_name}"


class ReceiptPrintLog(models.Model):
    """Records every time a receipt is printed or reprinted."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT, related_name="print_logs")
    printed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    printed_at = models.DateTimeField(auto_now_add=True)
    print_type = models.CharField(
        max_length=20,
        choices=[("original", "Original"), ("reprint", "Reprint"), ("pdf", "PDF Download")],
        default="original",
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "receipt_print_logs"
        ordering = ["-printed_at"]

    def __str__(self):
        return f"{self.print_type} of {self.receipt.receipt_number} at {self.printed_at}"
