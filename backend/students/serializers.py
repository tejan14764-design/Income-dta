"""
INCOME – Students serializers.
"""

from rest_framework import serializers
from .models import Student, Guardian, StudentGuardian, StudentConfidentialInformation


class GuardianSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Guardian
        fields = [
            "id", "school", "first_name", "last_name", "full_name",
            "gender", "phone_number", "alternate_phone", "email",
            "occupation", "address", "national_id",
        ]
        read_only_fields = ["id", "full_name"]

    def get_full_name(self, obj):
        return obj.full_name


class StudentGuardianSerializer(serializers.ModelSerializer):
    guardian_detail = GuardianSerializer(source="guardian", read_only=True)

    class Meta:
        model = StudentGuardian
        fields = [
            "id", "student", "guardian", "guardian_detail",
            "relationship", "is_primary", "is_emergency_contact", "can_pickup",
        ]
        read_only_fields = ["id", "guardian_detail"]


class StudentConfidentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentConfidentialInformation
        fields = [
            "id", "has_disability", "disability_category", "disability_details",
            "requires_special_support", "special_support_notes",
            "medical_conditions", "allergies", "emergency_medical_notes",
        ]
        read_only_fields = ["id"]


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    full_name = serializers.SerializerMethodField()
    current_class = serializers.SerializerMethodField()
    current_academic_year = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id", "admission_number", "first_name", "middle_name", "last_name",
            "full_name", "gender", "date_of_birth", "photograph",
            "admission_date", "status", "current_class", "current_academic_year",
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_current_class(self, obj):
        active = obj.enrollments.filter(is_active=True).select_related("class_ref").first()
        return active.class_ref.name if active else None

    def get_current_academic_year(self, obj):
        active = obj.enrollments.filter(is_active=True).select_related("academic_year").first()
        return active.academic_year.name if active else None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Full serializer including guardians and confidential info."""

    full_name = serializers.SerializerMethodField()
    guardians = StudentGuardianSerializer(source="student_guardians", many=True, read_only=True)
    photograph_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id", "school", "admission_number",
            "first_name", "middle_name", "last_name", "full_name",
            "gender", "date_of_birth", "photograph", "photograph_url",
            "residential_address", "email",
            "admission_date", "status", "notes",
            "guardians", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_name", "photograph_url"]

    def get_full_name(self, obj):
        return obj.full_name

    def get_photograph_url(self, obj):
        request = self.context.get("request")
        if obj.photograph and request:
            return request.build_absolute_uri(obj.photograph.url)
        return None


class StudentCreateSerializer(serializers.ModelSerializer):
    """Used for creating a new student."""

    class Meta:
        model = Student
        fields = [
            "school", "admission_number", "first_name", "middle_name", "last_name",
            "gender", "date_of_birth", "photograph", "residential_address", "email",
            "admission_date", "status", "notes",
        ]

    def validate_admission_number(self, value):
        return value.strip().upper()
