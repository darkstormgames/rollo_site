# SSO Setup and Configuration Guide

## Overview

This document provides comprehensive instructions for setting up and configuring the secure SSO (Single Sign-On) backend for Rollo Site.

## Prerequisites

- Node.js 20+ 
- MySQL 5.7+ or 8.0+
- npm 10+
- Angular CLI 20+

## Quick Start

### 1. Backend Setup

Navigate to the backend directory and install dependencies:

```bash
cd backend
npm install
```

### 2. Database Configuration

Copy the environment configuration file:

```bash
cp .env.example .env
```

Edit `.env` with your MySQL database credentials:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=rollo_sso
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password

# JWT Configuration - Generate secure secrets for production
JWT_ACCESS_SECRET=your-secure-access-secret-here
JWT_REFRESH_SECRET=your-secure-refresh-secret-here
```

### 3. Database Migration

Create the database schema and initial data:

```bash
npm run migrate
```

This will:
- Create the `rollo_sso` database
- Set up all required tables with proper indexes
- Insert default site configuration

### 4. Start the Backend Server

```bash
# Development mode with auto-reload
npm run dev

# Production mode
npm start
```

The server will start on `http://localhost:3000`

### 5. Frontend Integration

The Angular frontend is already configured to use the SSO backend. Start the frontend development server:

```bash
# From the project root directory
npm start
```

The application will be available at `http://localhost:4200`

## Architecture

### Database Schema

The SSO system uses the following tables:

- **`users`** - User accounts with secure password storage
- **`refresh_tokens`** - JWT refresh token management
- **`jwt_secrets`** - Secret key rotation tracking
- **`user_sessions`** - Session management and tracking
- **`sso_sites`** - Multi-site configuration
- **`user_site_permissions`** - Role-based access control

### Security Features

1. **Password Security**
   - Bcrypt hashing with 12 salt rounds
   - Password strength validation
   - Secure password comparison

2. **JWT Security**
   - Automatic secret rotation
   - Separate access and refresh tokens
   - Token expiration and validation
   - Key ID tracking for rotation

3. **API Security**
   - Rate limiting
   - CORS configuration
   - Helmet.js security headers
   - Input validation and sanitization

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePass123!",
  "firstName": "Test",
  "lastName": "User"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "SecurePass123!"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "your-refresh-token-here"
}
```

#### Logout
```http
POST /api/auth/logout
Content-Type: application/json

{
  "refreshToken": "your-refresh-token-here"
}
```

### Protected Endpoints

All protected endpoints require the `Authorization` header:

```http
Authorization: Bearer your-access-token-here
```

## Frontend Integration

### Authentication Service

The Angular frontend includes a comprehensive `AuthService` that handles:

- User registration and login
- Automatic token refresh
- Authentication state management
- Secure token storage

### Route Protection

Routes are protected using Angular guards:

- **`AuthGuard`** - Requires authentication
- **`GuestGuard`** - Requires no authentication (login/register pages)

### Example Usage

```typescript
// Inject the AuthService
constructor(private authService: AuthService) {}

// Check authentication status
this.authService.isAuthenticated$.subscribe(isAuth => {
  console.log('User authenticated:', isAuth);
});

// Get current user
this.authService.currentUser$.subscribe(user => {
  console.log('Current user:', user);
});

// Login
this.authService.login(credentials).subscribe({
  next: (response) => console.log('Login successful'),
  error: (error) => console.error('Login failed', error)
});
```

## Multi-Site SSO

The system supports multiple sites/applications through the `sso_sites` table.

### Adding New Sites

1. Insert site configuration:
```sql
INSERT INTO sso_sites (site_name, site_url, api_key_hash) 
VALUES ('New Site', 'https://newsite.com', SHA2('unique-api-key', 256));
```

2. Configure user permissions:
```sql
INSERT INTO user_site_permissions (user_id, site_id, role)
VALUES (1, 2, 'admin');
```

## Production Deployment

### Environment Configuration

1. Generate secure JWT secrets:
```bash
# Generate 64-character random strings
openssl rand -hex 64
```

2. Configure production environment:
```env
NODE_ENV=production
JWT_ACCESS_SECRET=your-production-access-secret
JWT_REFRESH_SECRET=your-production-refresh-secret
CORS_ORIGIN=https://your-production-domain.com
```

### Database Security

1. Create dedicated database user:
```sql
CREATE USER 'rollo_sso'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON rollo_sso.* TO 'rollo_sso'@'localhost';
FLUSH PRIVILEGES;
```

2. Enable SSL connections:
```env
DB_SSL=true
DB_SSL_CA=/path/to/ca-cert.pem
```

### Server Security

1. Use HTTPS/TLS termination
2. Configure proper firewall rules
3. Enable rate limiting
4. Set up monitoring and logging
5. Regular security updates

## Testing

### Backend Tests

Run the backend test suite:

```bash
cd backend
npm test
```

### Frontend Tests

Run the frontend tests:

```bash
npm test
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify MySQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **JWT Token Errors**
   - Check JWT secrets configuration
   - Verify token expiration settings
   - Clear browser localStorage

3. **CORS Errors**
   - Update `CORS_ORIGIN` in backend `.env`
   - Verify frontend URL matches CORS configuration

### Debugging

Enable debug logging:

```env
NODE_ENV=development
DEBUG=rollo-sso:*
```

## Security Considerations

1. **Secrets Management**
   - Never commit secrets to version control
   - Use environment variables or secret management service
   - Rotate secrets regularly

2. **Database Security**
   - Use dedicated database users with minimal privileges
   - Enable SSL/TLS for database connections
   - Regular security updates

3. **Network Security**
   - Use HTTPS in production
   - Configure proper CORS origins
   - Implement rate limiting

4. **Monitoring**
   - Log authentication attempts
   - Monitor for suspicious activity
   - Set up alerts for security events

## License

ISC License - see package.json for details