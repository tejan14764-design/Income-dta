"""
INCOME – Academics models.
AcademicYear, Class, Enrollment.
"""

import uuid
from django.db import models


class AcademicYear(models.Model):
    """Represents one academic year at a school."""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="academic_years"
    )
    name = models.CharField(max_length=100)  # e.g. "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPCOMING
    )
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academic_years"
        unique_together = [("school", "name")]
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["school", "is_current"]),
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.school})"

    def save(self, *args, **kwargs):
        # Enforce only one current academic year per school
        if self.is_current:
            AcademicYear.objects.filter(
                school=self.school, is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Class(models.Model):
    """School class / grade level."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="classes"
    )
    name = models.CharField(max_length=100)   # e.g. "Grade 1", "JSS 1A"
    short_name = models.CharField(max_length=20, blank=True)  # e.g. "G1", "JSS1A"
    level = models.PositiveSmallIntegerField(default=1)  # For ordering
    description = models.TextField(blank=True)
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "classes"
        unique_together = [("school", "name")]
        ordering = ["level", "name"]
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.school})"


class Enrollment(models.Model):
    """Links a Student to a Class in a specific Academic Year."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"  # Year ended
        PROMOTED = "promoted", "Promoted"
        REPEATED = "repeated", "Repeated"
        TRANSFERRED = "transferred", "Transferred Out"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="enrollments"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="enrollments"
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.PROTECT, related_name="enrollments"
    )
    class_ref = models.ForeignKey(
        Class, on_delete=models.PROTECT, related_name="enrollments"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    enrollment_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="enrollments_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enrollments"
        # A student can only be actively enrolled once per academic year per school
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                condition=models.Q(is_active=True),
                name="unique_active_enrollment_per_year",
            )
        ]
        ordering = ["-academic_year__start_date", "student__last_name"]
        indexes = [
            models.Index(fields=["school", "academic_year", "is_active"]),
            models.Index(fields=["student", "academic_year"]),
        ]

    def __str__(self):
        return f"{self.student} → {self.class_ref} ({self.academic_year})"
