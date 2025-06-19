"""Test authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User
from models.role import Role
from core.security import SecurityUtils


def test_register_user(client: TestClient, db_session: Session):
    """Test user registration."""
    # Create default role
    default_role = Role(name="user", permissions={"read": True})
    db_session.add(default_role)
    db_session.commit()
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    assert data["tokens"]["token_type"] == "bearer"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


def test_register_user_passwords_dont_match(client: TestClient):
    """Test user registration with mismatched passwords."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "confirm_password": "DifferentPass123!"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Passwords do not match" in response.json()["detail"]


def test_register_duplicate_user(client: TestClient, db_session: Session):
    """Test registering user with existing username/email."""
    # Create default role
    default_role = Role(name="user", permissions={"read": True})
    db_session.add(default_role)
    db_session.commit()
    
    # Create existing user
    existing_user = User(
        username="existinguser",
        email="existing@example.com",
        password_hash=SecurityUtils.hash_password("password123")
    )
    db_session.add(existing_user)
    db_session.commit()
    
    user_data = {
        "username": "existinguser",
        "email": "new@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client: TestClient, db_session: Session):
    """Test successful login."""
    # Create user
    user = User(
        username="loginuser",
        email="login@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "loginuser",
        "password": "password123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["username"] == "loginuser"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


def test_login_invalid_credentials(client: TestClient, db_session: Session):
    """Test login with invalid credentials."""
    # Create user
    user = User(
        username="loginuser",
        email="login@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "loginuser",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, db_session: Session):
    """Test login with inactive user."""
    # Create inactive user
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "inactiveuser",
        "password": "password123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401


def test_refresh_token(client: TestClient, db_session: Session):
    """Test token refresh."""
    # Create and login user
    user = User(
        username="refreshuser",
        email="refresh@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "refreshuser",
        "password": "password123"
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    login_data = login_response.json()
    refresh_token = login_data["tokens"]["refresh_token"]
    
    # Test refresh
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/auth/refresh", json=refresh_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient, db_session: Session):
    """Test getting current user profile."""
    # Create and login user
    user = User(
        username="profileuser",
        email="profile@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "profileuser",
        "password": "password123"
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    login_data = login_response.json()
    access_token = login_data["tokens"]["access_token"]
    
    # Test getting profile
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@example.com"


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # No credentials provided


def test_logout(client: TestClient, db_session: Session):
    """Test user logout."""
    # Create and login user
    user = User(
        username="logoutuser",
        email="logout@example.com",
        password_hash=SecurityUtils.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": "logoutuser",
        "password": "password123"
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    tokens = login_response.json()["tokens"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # Test logout
    headers = {"Authorization": f"Bearer {access_token}"}
    logout_data = {"refresh_token": refresh_token}
    response = client.post("/api/auth/logout", json=logout_data, headers=headers)
    
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]