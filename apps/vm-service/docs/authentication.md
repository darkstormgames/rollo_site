# JWT Authentication and Authorization

This document describes the JWT authentication and authorization system implemented for the VM Management Service.

## Overview

The authentication system provides:
- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Token blacklisting for secure logout
- Rate limiting on authentication endpoints
- Password reset functionality

## Security Features

- **Password Hashing**: Passwords are hashed using bcrypt with 12 rounds
- **JWT Tokens**: 
  - Access tokens expire in 15 minutes (configurable)
  - Refresh tokens expire in 7 days (configurable)
  - Tokens include user ID, username, email, and roles
- **Rate Limiting**: 
  - General endpoints: 60 requests per minute per IP
  - Auth endpoints: 5 requests per minute per IP
- **Token Blacklisting**: Refresh tokens are stored in database and can be revoked
- **Role-based Permissions**: Users can have multiple roles with granular permissions

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string (3-50 chars, alphanumeric + underscore)",
  "email": "valid email address",
  "password": "string (min 8 chars)",
  "confirm_password": "string (must match password)"
}
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2023-12-01T10:00:00Z",
    "roles": [
      {
        "id": 1,
        "name": "user",
        "permissions": {"read": true}
      }
    ]
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

#### POST /api/auth/login
Authenticate user with username and password.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):** Same as registration response.

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST /api/auth/logout
Logout user and revoke refresh token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

#### GET /api/auth/me
Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2023-12-01T10:00:00Z",
  "roles": [
    {
      "id": 1,
      "name": "user",
      "permissions": {"read": true}
    }
  ]
}
```

### Password Reset Endpoints

#### POST /api/auth/forgot-password
Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

#### POST /api/auth/reset-password
Reset password using reset token.

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "string (min 8 chars)",
  "confirm_password": "string (must match new_password)"
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

## Authorization

### Using Access Tokens

Include the access token in the Authorization header for protected endpoints:

```http
Authorization: Bearer <access_token>
```

### Permission-based Authorization

Use the `require_permissions` decorator to protect endpoints:

```python
from core.auth import require_permissions

@router.get("/protected")
@require_permissions(["read", "write"])
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    return {"message": "Access granted"}
```

### Role-based Authorization

Use the `require_roles` decorator to protect endpoints:

```python
from core.auth import require_roles

@router.get("/admin")
@require_roles(["admin"])
async def admin_endpoint(current_user: User = Depends(get_current_active_user)):
    return {"message": "Admin access granted"}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 400 Bad Request
```json
{
  "detail": "Username or email already registered"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Too many authentication requests. Please try again later."
}
```

## Configuration

Configure authentication settings via environment variables:

```bash
# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_MINUTE=5
```

## Database Models

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `is_active`: Account status
- `created_at`, `updated_at`: Timestamps

### Roles Table
- `id`: Primary key
- `name`: Unique role name
- `permissions`: JSON object with permissions
- `created_at`: Timestamp

### Refresh Tokens Table
- `id`: Primary key
- `token_hash`: SHA256 hash of refresh token
- `user_id`: Foreign key to users
- `is_revoked`: Revocation status
- `created_at`, `expires_at`, `revoked_at`: Timestamps

### Password Reset Tokens Table
- `id`: Primary key
- `token_hash`: SHA256 hash of reset token
- `user_id`: Foreign key to users
- `is_used`: Usage status
- `created_at`, `expires_at`, `used_at`: Timestamps

## Security Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** on client side (httpOnly cookies recommended)
3. **Validate token expiration** on every request
4. **Use short-lived access tokens** with refresh token rotation
5. **Implement proper CORS** policies
6. **Log authentication events** for security monitoring
7. **Use strong passwords** with complexity requirements
8. **Implement account lockout** after multiple failed attempts (planned feature)

## Example Usage

See `demo_auth.py` for a complete example of using the authentication API.

## Testing

Run the authentication tests:

```bash
# Test core security functions
python -m pytest tests/test_security.py -v

# Test user model methods
python -m pytest tests/test_user_model.py -v

# Test authentication endpoints (requires database setup)
python -m pytest tests/test_auth.py -v
```