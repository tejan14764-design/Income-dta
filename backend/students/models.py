"""
INCOME – Students models.
Student, Guardian, StudentGuardian, StudentConfidentialInformation.
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    GRADUATED = "graduated", "Graduated"
    TRANSFERRED = "transferred", "Transferred"
    WITHDRAWN = "withdrawn", "Withdrawn"
    SUSPENDED = "suspended", "Suspended"


class GuardianRelationship(models.TextChoices):
    FATHER = "father", "Father"
    MOTHER = "mother", "Mother"
    GRANDFATHER = "grandfather", "Grandfather"
    GRANDMOTHER = "grandmother", "Grandmother"
    UNCLE = "uncle", "Uncle"
    AUNT = "aunt", "Aunt"
    SIBLING = "sibling", "Sibling"
    GUARDIAN = "guardian", "Legal Guardian"
    OTHER = "other", "Other"


class Student(models.Model):
    """Core student record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="students"
    )

    # Identification
    admission_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices)
    date_of_birth = models.DateField()
    photograph = models.ImageField(upload_to="students/photos/%Y/%m/", null=True, blank=True)

    # Contact
    residential_address = models.TextField(blank=True)
    email = models.EmailField(blank=True)

    # Admission
    admission_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=StudentStatus.choices, default=StudentStatus.ACTIVE
    )

    # Metadata
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="students_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "students"
        unique_together = [("school", "admission_number")]
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["school", "admission_number"]),
            models.Index(fields=["school", "status"]),
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.admission_number})"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class Guardian(models.Model):
    """Parent or guardian record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="guardians"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True)
    phone_number = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guardians"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class StudentGuardian(models.Model):
    """Links a Student to a Guardian with relationship type."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_guardians")
    guardian = models.ForeignKey(Guardian, on_delete=models.PROTECT, related_name="student_guardians")
    relationship = models.CharField(max_length=20, choices=GuardianRelationship.choices)
    is_primary = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)
    can_pickup = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "student_guardians"
        unique_together = [("student", "guardian")]

    def __str__(self):
        return f"{self.guardian} → {self.student} ({self.relationship})"


class DisabilityCategory(models.TextChoices):
    VISUAL = "visual_impairment", "Visual Impairment"
    HEARING = "hearing_impairment", "Hearing Impairment"
    PHYSICAL = "physical_disability", "Physical Disability"
    INTELLECTUAL = "intellectual_disability", "Intellectual Disability"
    LEARNING = "learning_disability", "Learning Disability"
    SPEECH = "speech_language", "Speech/Language Disorder"
    AUTISM = "autism_spectrum", "Autism Spectrum Disorder"
    MULTIPLE = "multiple_disabilities", "Multiple Disabilities"
    OTHER = "other", "Other"


class StudentConfidentialInformation(models.Model):
    """
    Sensitive / confidential information.
    Restricted access – only authorized staff may view.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="confidential_info"
    )
    has_disability = models.BooleanField(default=False)
    disability_category = models.CharField(
        max_length=50,
        choices=DisabilityCategory.choices,
        blank=True,
    )
    disability_details = models.TextField(blank=True)
    requires_special_support = models.BooleanField(default=False)
    special_support_notes = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    emergency_medical_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_confidential_info"

    def __str__(self):
        return f"Confidential info: {self.student}"
