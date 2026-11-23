"""
Tests: Authentication — login, logout, token refresh, change password.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestLogin:
    def test_login_valid_credentials(self, api_client, admin_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["username"] == "testadmin"

    def test_login_wrong_password(self, api_client, admin_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "testadmin",
            "password": "WrongPassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, api_client):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "nobody",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_inactive_user(self, api_client, admin_user):
        admin_user.is_active = False
        admin_user.save()
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert resp.status_code == 401

    def test_login_returns_memberships(self, api_client, admin_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "memberships" in data


@pytest.mark.django_db
class TestMe:
    def test_me_authenticated(self, auth_client, admin_user):
        resp = auth_client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "testadmin"

    def test_me_unauthenticated(self, api_client):
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    def test_change_password_success(self, auth_client, admin_user):
        resp = auth_client.post("/api/v1/auth/change-password/", {
            "current_password": "TestPass@123",
            "new_password": "NewSecurePass@456",
            "confirm_password": "NewSecurePass@456",
        })
        assert resp.status_code == 200
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewSecurePass@456")

    def test_change_password_wrong_current(self, auth_client):
        resp = auth_client.post("/api/v1/auth/change-password/", {
            "current_password": "WrongCurrent",
            "new_password": "NewSecurePass@456",
            "confirm_password": "NewSecurePass@456",
        })
        assert resp.status_code == 400

    def test_change_password_mismatch(self, auth_client):
        resp = auth_client.post("/api/v1/auth/change-password/", {
            "current_password": "TestPass@123",
            "new_password": "NewPass@123",
            "confirm_password": "DifferentPass@123",
        })
        assert resp.status_code == 400
