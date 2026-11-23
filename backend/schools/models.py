"""
INCOME – Schools models.
Multi-tenant school architecture.
"""

import uuid
from django.db import models


class School(models.Model):
    """Root tenant entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="schools/logos/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schools"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolSettings(models.Model):
    """Per-school configuration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="settings")
    currency_code = models.CharField(max_length=10, default="SLL")
    currency_symbol = models.CharField(max_length=10, default="NLe")
    receipt_footer = models.TextField(
        blank=True,
        default="Thank you for your payment. Please keep this receipt for your records.",
    )
    receipt_printer_name = models.CharField(max_length=255, blank=True)
    receipt_copies = models.PositiveSmallIntegerField(default=1)
    enable_sms_notifications = models.BooleanField(default=False)
    academic_year_auto_archive = models.BooleanField(default=True)
    max_payment_evidence_size_mb = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "school_settings"

    def __str__(self):
        return f"Settings for {self.school}"


class SchoolBranch(models.Model):
    """Optional school branches (future use)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "school_branches"
        unique_together = [("school", "name")]

    def __str__(self):
        return f"{self.school.name} – {self.name}"
