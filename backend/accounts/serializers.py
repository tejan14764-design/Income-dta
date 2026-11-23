"""
INCOME – Accounts serializers.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, Permission, RolePermission, SchoolMembership

User = get_user_model()


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user info to the JWT token response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Inject user profile into response
        data["user"] = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.get_full_name(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "must_change_password": user.must_change_password,
        }
        # Inject school memberships
        memberships = user.memberships.filter(is_active=True).select_related("school", "role")
        data["memberships"] = [
            {
                "school_id": str(m.school_id),
                "school_name": m.school.name,
                "role_id": str(m.role_id),
                "role_name": m.role.name,
                "role_slug": m.role.slug,
            }
            for m in memberships
        ]
        return data


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "full_name", "phone_number", "is_active", "date_joined",
            "must_change_password",
        ]
        read_only_fields = ["id", "date_joined", "full_name"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username", "email", "first_name", "last_name",
            "phone_number", "password", "confirm_password",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


# ---------------------------------------------------------------------------
# Role and Permission
# ---------------------------------------------------------------------------
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "name", "module", "description"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False,
        write_only=True,
    )
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Role
        fields = [
            "id", "school", "name", "slug", "description",
            "is_system_role", "is_active", "permissions", "permission_ids",
        ]
        read_only_fields = ["id"]

    def get_permissions(self, obj):
        perms = obj.role_permissions.select_related("permission").all()
        return PermissionSerializer([rp.permission for rp in perms], many=True).data

    def validate(self, attrs):
        school = attrs.get("school", getattr(self.instance, "school", None))
        name = attrs.get("name", getattr(self.instance, "name", ""))
        slug = attrs.get("slug")

        if slug:
            attrs["slug"] = slugify(slug)
        elif self.instance is None and school and name:
            base = slugify(name) or "role"
            candidate = base
            qs = Role.objects.filter(school=school, slug=candidate)
            counter = 2
            while qs.exists():
                candidate = f"{base}-{counter}"
                counter += 1
                qs = Role.objects.filter(school=school, slug=candidate)
            attrs["slug"] = candidate
        elif "slug" in attrs:
            attrs.pop("slug")

        return attrs

    def _set_permissions(self, role, permissions):
        request = self.context.get("request")
        granted_by = request.user if request and request.user.is_authenticated else None
        existing = {rp.permission_id: rp for rp in role.role_permissions.select_related("permission").all()}
        desired = {permission.id: permission for permission in permissions}

        for permission_id, role_permission in existing.items():
            if permission_id not in desired:
                role_permission.delete()

        for permission_id, permission in desired.items():
            if permission_id not in existing:
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    granted_by=granted_by,
                )

    def create(self, validated_data):
        permissions = validated_data.pop("permission_ids", None)
        role = super().create(validated_data)
        if permissions is not None:
            self._set_permissions(role, permissions)
        return role

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permission_ids", None)
        role = super().update(instance, validated_data)
        if permissions is not None:
            self._set_permissions(role, permissions)
        return role


# ---------------------------------------------------------------------------
# School Membership
# ---------------------------------------------------------------------------
class SchoolMembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolMembership
        fields = [
            "id", "user", "user_name", "school", "school_name",
            "role", "role_name", "is_active", "joined_at",
        ]
        read_only_fields = ["id", "joined_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_role_name(self, obj):
        return obj.role.name

    def get_school_name(self, obj):
        return obj.school.name
