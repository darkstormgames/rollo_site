"""Test core security utilities."""

import pytest
from datetime import datetime, timedelta

from core.security import SecurityUtils


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    
    # Hash password
    hashed = SecurityUtils.hash_password(password)
    assert hashed != password
    assert len(hashed) > 50  # bcrypt hashes are long
    
    # Verify correct password
    assert SecurityUtils.verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert SecurityUtils.verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_verification():
    """Test JWT access token creation and verification."""
    data = {
        "sub": "testuser",
        "user_id": 123,
        "email": "test@example.com",
        "roles": ["user", "admin"]
    }
    
    # Create token
    token = SecurityUtils.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long
    
    # Verify token
    token_data = SecurityUtils.verify_token(token, "access")
    assert token_data is not None
    assert token_data.username == "testuser"
    assert token_data.user_id == 123
    assert token_data.email == "test@example.com"
    assert token_data.roles == ["user", "admin"]


def test_refresh_token_creation_and_verification():
    """Test JWT refresh token creation and verification."""
    data = {
        "sub": "testuser",
        "user_id": 123,
        "email": "test@example.com",
        "roles": ["user"]
    }
    
    # Create refresh token
    token = SecurityUtils.create_refresh_token(data)
    assert isinstance(token, str)
    assert len(token) > 50
    
    # Verify refresh token
    token_data = SecurityUtils.verify_token(token, "refresh")
    assert token_data is not None
    assert token_data.username == "testuser"
    assert token_data.user_id == 123


def test_token_expiration():
    """Test token expiration."""
    data = {"sub": "testuser", "user_id": 123}
    
    # Create token with very short expiration
    short_expiry = timedelta(seconds=1)
    token = SecurityUtils.create_access_token(data, short_expiry)
    
    # Token should be valid immediately
    token_data = SecurityUtils.verify_token(token, "access")
    assert token_data is not None
    
    # Wait for token to expire
    import time
    time.sleep(2)
    
    # Token should now be invalid
    token_data = SecurityUtils.verify_token(token, "access")
    assert token_data is None


def test_token_type_validation():
    """Test that token type is validated."""
    data = {"sub": "testuser", "user_id": 123}
    
    # Create access token
    access_token = SecurityUtils.create_access_token(data)
    
    # Should work with correct type
    token_data = SecurityUtils.verify_token(access_token, "access")
    assert token_data is not None
    
    # Should fail with wrong type
    token_data = SecurityUtils.verify_token(access_token, "refresh")
    assert token_data is None


def test_invalid_token():
    """Test invalid token handling."""
    # Test with invalid token
    token_data = SecurityUtils.verify_token("invalid.token.here", "access")
    assert token_data is None
    
    # Test with empty token
    token_data = SecurityUtils.verify_token("", "access")
    assert token_data is None


def test_reset_token_generation():
    """Test reset token generation."""
    token1 = SecurityUtils.generate_reset_token()
    token2 = SecurityUtils.generate_reset_token()
    
    # Tokens should be different
    assert token1 != token2
    
    # Tokens should be reasonably long
    assert len(token1) > 20
    assert len(token2) > 20


def test_api_key_generation():
    """Test API key generation."""
    key1 = SecurityUtils.generate_api_key()
    key2 = SecurityUtils.generate_api_key()
    
    # Keys should be different
    assert key1 != key2
    
    # Keys should be reasonably long
    assert len(key1) > 20
    assert len(key2) > 20