"""
INCOME – Finance models.
FeeCategory, FeeTemplate, FeeTemplateItem,
StudentFeeAssignment, StudentCharge, FeeAdjustment.
All monetary values use DecimalField (NUMERIC in PostgreSQL).
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


ZERO = Decimal("0.00")


class FeeCategory(models.Model):
    """Types of fees the school charges."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="fee_categories"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fee_categories"
        unique_together = [("school", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeeTemplate(models.Model):
    """
    A configurable fee template used to suggest fees for a class/year.
    Assigning a template to a student copies items into StudentCharge records.
    Subsequent changes to the template do NOT automatically update student charges.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="fee_templates"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.PROTECT, related_name="fee_templates"
    )
    target_class = models.ForeignKey(
        "academics.Class", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fee_templates"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fee_templates"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class FeeTemplateItem(models.Model):
    """Individual fee item within a template."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(FeeTemplate, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="template_items")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(ZERO)])
    is_mandatory = models.BooleanField(default=True)
    due_date = models.DateField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "fee_template_items"
        ordering = ["sort_order", "description"]

    def __str__(self):
        return f"{self.description}: {self.amount}"


class StudentFeeAssignment(models.Model):
    """
    Records that a fee template was applied to a student.
    Acts as a header for the resulting StudentCharge records.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="fee_assignments"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="fee_assignments"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.PROTECT, related_name="fee_assignments"
    )
    template = models.ForeignKey(
        FeeTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="student_assignments"
    )
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="fee_assignments_created"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_fee_assignments"
        unique_together = [("student", "academic_year")]
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"Fee assignment: {self.student} / {self.academic_year}"


class ChargeStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    FULLY_PAID = "fully_paid", "Fully Paid"
    PENDING_VERIFICATION = "pending_verification", "Pending Verification"
    WAIVED = "waived", "Waived"
    OVERDUE = "overdue", "Overdue"


class StudentCharge(models.Model):
    """
    An individual charge on a student's account.
    May originate from a fee template item or be manually added.
    Monetary values use DecimalField – never float.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="student_charges"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="charges"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.PROTECT, related_name="student_charges"
    )
    assignment = models.ForeignKey(
        StudentFeeAssignment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="charges"
    )
    category = models.ForeignKey(
        FeeCategory, on_delete=models.PROTECT, related_name="student_charges"
    )
    description = models.CharField(max_length=255)
    base_amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(ZERO)]
    )
    discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, validators=[MinValueValidator(ZERO)]
    )
    waiver_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, validators=[MinValueValidator(ZERO)]
    )
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=25, choices=ChargeStatus.choices, default=ChargeStatus.UNPAID
    )
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="charges_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_charges"
        ordering = ["description"]
        indexes = [
            models.Index(fields=["student", "academic_year"]),
            models.Index(fields=["school", "academic_year", "status"]),
        ]

    def __str__(self):
        return f"{self.student} – {self.description}: {self.net_amount}"

    @property
    def net_amount(self):
        """Net expected = base - discount - waiver."""
        return max(ZERO, self.base_amount - self.discount_amount - self.waiver_amount)


class AdjustmentType(models.TextChoices):
    DISCOUNT = "discount", "Discount"
    WAIVER = "waiver", "Waiver"
    EXEMPTION = "exemption", "Full Exemption"
    ADDITIONAL_CHARGE = "additional_charge", "Additional Charge"
    AMOUNT_CORRECTION = "amount_correction", "Amount Correction"


class FeeAdjustment(models.Model):
    """
    Audit record for every financial adjustment on a StudentCharge.
    Preserves history when discounts / waivers are applied.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    charge = models.ForeignKey(StudentCharge, on_delete=models.PROTECT, related_name="adjustments")
    adjustment_type = models.CharField(max_length=25, choices=AdjustmentType.choices)
    previous_amount = models.DecimalField(max_digits=14, decimal_places=2)
    new_amount = models.DecimalField(max_digits=14, decimal_places=2)
    amount_changed = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField()
    applied_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="adjustments_applied"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    authorized_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="adjustments_authorized"
    )

    class Meta:
        db_table = "fee_adjustments"
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.adjustment_type} on {self.charge}: {self.amount_changed}"
