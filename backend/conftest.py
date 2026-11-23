"""
INCOME – Root pytest configuration and shared fixtures.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def school(db):
    from schools.models import School, SchoolSettings
    school = School.objects.create(name="Test School", code="TST", email="test@school.edu")
    SchoolSettings.objects.create(school=school)
    return school


@pytest.fixture
def admin_user(db, school):
    from accounts.models import Role, SchoolMembership, Permission, RolePermission
    user = User.objects.create_user(
        username="testadmin",
        email="admin@test.com",
        password="TestPass@123",
        first_name="Test",
        last_name="Admin",
        is_superuser=True,
        is_staff=True,
    )
    return user


@pytest.fixture
def cashier_user(db, school):
    from accounts.models import Role, SchoolMembership, Permission, RolePermission
    user = User.objects.create_user(
        username="cashier1",
        email="cashier@test.com",
        password="TestPass@123",
        first_name="Cash",
        last_name="Ier",
    )
    role, _ = Role.objects.get_or_create(
        school=school, slug="bursar",
        defaults={"name": "Bursar / Cashier"},
    )
    SchoolMembership.objects.create(user=user, school=school, role=role)
    return user


@pytest.fixture
def financial_officer(db, school):
    from accounts.models import Role, SchoolMembership
    user = User.objects.create_user(
        username="officer1",
        email="officer@test.com",
        password="TestPass@123",
        first_name="Finance",
        last_name="Officer",
    )
    role, _ = Role.objects.get_or_create(
        school=school, slug="financial_officer",
        defaults={"name": "Financial Officer"},
    )
    SchoolMembership.objects.create(user=user, school=school, role=role)
    return user


@pytest.fixture
def academic_year(db, school):
    from academics.models import AcademicYear
    return AcademicYear.objects.create(
        school=school,
        name="2024/2025",
        start_date="2024-09-01",
        end_date="2025-07-31",
        status="active",
        is_current=True,
    )


@pytest.fixture
def school_class(db, school):
    from academics.models import Class
    return Class.objects.create(school=school, name="Grade 1", level=1)


@pytest.fixture
def student(db, school, admin_user):
    from students.models import Student
    return Student.objects.create(
        school=school,
        admission_number="STU-001",
        first_name="John",
        last_name="Doe",
        gender="male",
        date_of_birth="2010-01-15",
        admission_date="2024-09-01",
        created_by=admin_user,
    )


@pytest.fixture
def fee_category(db, school):
    from finance.models import FeeCategory
    return FeeCategory.objects.create(school=school, name="School Fees", code="SCH")


@pytest.fixture
def student_charge(db, school, student, academic_year, fee_category):
    from finance.models import StudentCharge
    return StudentCharge.objects.create(
        school=school,
        student=student,
        academic_year=academic_year,
        category=fee_category,
        description="Annual School Fees",
        base_amount=Decimal("500.00"),
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client
