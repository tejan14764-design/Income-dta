from rest_framework import serializers
from .models import AcademicYear, Class, Enrollment


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = [
            "id", "school", "name", "start_date", "end_date",
            "status", "is_current", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["start_date"] >= attrs["end_date"]:
                raise serializers.ValidationError(
                    {"end_date": "End date must be after start date."}
                )
        return attrs


class ClassSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            "id", "school", "name", "short_name", "level",
            "description", "capacity", "is_active", "student_count",
        ]
        read_only_fields = ["id", "student_count"]

    def get_student_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id", "school", "student", "student_name", "student_admission_number",
            "academic_year", "academic_year_name",
            "class_ref", "class_name",
            "status", "is_active", "enrollment_date", "end_date", "notes",
        ]
        read_only_fields = [
            "id", "student_name", "student_admission_number",
            "class_name", "academic_year_name", "enrollment_date",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_student_admission_number(self, obj):
        return obj.student.admission_number

    def get_class_name(self, obj):
        return obj.class_ref.name

    def get_academic_year_name(self, obj):
        return obj.academic_year.name

    def validate(self, attrs):
        student = attrs.get("student")
        academic_year = attrs.get("academic_year")
        # Prevent duplicate active enrollment in same academic year
        if student and academic_year:
            existing = Enrollment.objects.filter(
                student=student, academic_year=academic_year, is_active=True
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    "This student already has an active enrollment in this academic year."
                )
        return attrs
