"""
Tests: Student registration, search, profile access, school isolation.
"""
import pytest
from decimal import Decimal


@pytest.mark.django_db
class TestStudentRegistration:
    def test_register_student(self, auth_client, school):
        resp = auth_client.post("/api/v1/students/", {
            "school": str(school.id),
            "admission_number": "STU-100",
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": "female",
            "date_of_birth": "2010-03-20",
            "admission_date": "2024-09-01",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["admission_number"] == "STU-100"
        assert data["first_name"] == "Alice"

    def test_duplicate_admission_number_rejected(self, auth_client, school, student):
        resp = auth_client.post("/api/v1/students/", {
            "school": str(school.id),
            "admission_number": "STU-001",  # duplicate
            "first_name": "Bob",
            "last_name": "Jones",
            "gender": "male",
            "date_of_birth": "2011-06-10",
            "admission_date": "2024-09-01",
        })
        assert resp.status_code == 400

    def test_list_students_requires_auth(self, api_client, school):
        resp = api_client.get(f"/api/v1/students/?school={school.id}")
        assert resp.status_code == 401

    def test_list_students_filtered_by_school(self, auth_client, school, student):
        resp = auth_client.get(f"/api/v1/students/?school={school.id}")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["results"]]
        assert str(student.id) in ids

    def test_search_by_name(self, auth_client, school, student):
        resp = auth_client.get(f"/api/v1/students/?school={school.id}&search=John")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_search_by_admission_number(self, auth_client, school, student):
        resp = auth_client.get(f"/api/v1/students/?school={school.id}&search=STU-001")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_school_data_isolation(self, auth_client, db):
        """Students from another school must not appear in queries."""
        from schools.models import School
        from students.models import Student
        from django.contrib.auth import get_user_model
        User = get_user_model()

        other_school = School.objects.create(name="Other School", code="OTH")
        other_student = Student.objects.create(
            school=other_school,
            admission_number="OTH-001",
            first_name="Hidden",
            last_name="Student",
            gender="male",
            date_of_birth="2010-01-01",
            admission_date="2024-09-01",
        )
        # Query with original school — should not see the other school's student
        from schools.models import School as S
        my_school = S.objects.get(code="TST")
        resp = auth_client.get(f"/api/v1/students/?school={my_school.id}&search=Hidden")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


@pytest.mark.django_db
class TestStudentProfile:
    def test_get_student_detail(self, auth_client, student):
        resp = auth_client.get(f"/api/v1/students/{student.id}/")
        assert resp.status_code == 200
        assert resp.json()["admission_number"] == "STU-001"

    def test_full_name_property(self, student):
        student.middle_name = "Michael"
        assert student.full_name == "John Michael Doe"

    def test_financial_summary_endpoint(self, auth_client, student):
        resp = auth_client.get(f"/api/v1/students/{student.id}/financial_summary/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_expected" in data
        assert "outstanding" in data
        assert "payment_status" in data
