"""
INCOME – Accounts models.
Custom User, Role, Permission, SchoolMembership.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="staff/photos/", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Can access Django admin
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        db_table = "auth_users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class SystemRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Administrator"
    SCHOOL_ADMIN = "school_admin", "School Administrator"
    REGISTRAR = "registrar", "Registrar"
    BURSAR = "bursar", "Bursar / Cashier"
    FINANCIAL_OFFICER = "financial_officer", "Financial Officer"
    AUDITOR = "auditor", "Auditor"
    TEACHER = "teacher", "Teacher"


class Role(models.Model):
    """School-scoped role definition."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="roles"
    )
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)  # e.g. "bursar"
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        unique_together = [("school", "slug")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} @ {self.school_id}"


class Permission(models.Model):
    """Fine-grained permission definitions (school-independent)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    module = models.CharField(max_length=100)  # e.g. "students", "finance"
    description = models.TextField(blank=True)

    class Meta:
        db_table = "permissions"
        ordering = ["module", "codename"]

    def __str__(self):
        return f"{self.module}.{self.codename}"


class RolePermission(models.Model):
    """Many-to-many between Role and Permission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="permissions_granted"
    )

    class Meta:
        db_table = "role_permissions"
        unique_together = [("role", "permission")]

    def __str__(self):
        return f"{self.role} → {self.permission}"


class SchoolMembership(models.Model):
    """Links a User to a School with a specific Role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="memberships")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="memberships_created"
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "school_memberships"
        unique_together = [("user", "school")]
        indexes = [
            models.Index(fields=["user", "school", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} as {self.role} @ {self.school_id}"


class PasswordResetToken(models.Model):
    """Stores password reset tokens."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"

    def __str__(self):
        return f"Reset token for {self.user}"
