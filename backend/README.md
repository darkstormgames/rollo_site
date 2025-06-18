# Rollo SSO Backend

Secure Single Sign-On backend service for Rollo Site and other applications.

## Features

- 🔐 Secure JWT authentication with automatic secret rotation
- 🛡️ Password hashing using bcrypt with configurable salt rounds
- 🗄️ MySQL database with optimized schema
- 🔄 Refresh token mechanism for enhanced security
- 🌐 Multi-site SSO support
- 📊 Session tracking and management
- 🚀 Express.js with security middleware
- ✅ Comprehensive input validation
- 🔒 Rate limiting and CORS protection

## Quick Start

### Prerequisites

- Node.js 20+ 
- MySQL 5.7+
- npm

### Installation

1. Install dependencies:
```bash
cd backend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Set up database:
```bash
npm run migrate
```

4. Start the server:
```bash
# Development
npm run dev

# Production  
npm start
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout

### Health Check

- `GET /health` - Server health status

## Security Features

### Password Security
- Bcrypt hashing with 12 salt rounds
- Password strength validation
- Secure password comparison

### JWT Security
- Automatic secret rotation
- Separate access and refresh tokens
- Token expiration and validation
- Key ID tracking for rotation

### Database Security
- Prepared statements to prevent SQL injection
- Sensitive data hashing
- Connection pooling with limits
- Transaction support

### HTTP Security
- Helmet.js security headers
- CORS configuration
- Rate limiting
- Request size limits

## Database Schema

The system uses a comprehensive MySQL schema with the following tables:

- `users` - User accounts with secure password storage
- `refresh_tokens` - JWT refresh token management
- `jwt_secrets` - Secret key rotation tracking
- `user_sessions` - Session management and tracking
- `sso_sites` - Multi-site configuration
- `user_site_permissions` - Role-based access control

## Testing

Run the test suite:
```bash
npm test
```

## Configuration

Key environment variables:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database connection
- `JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET` - JWT secrets (auto-rotated)
- `JWT_ACCESS_EXPIRES_IN`, `JWT_REFRESH_EXPIRES_IN` - Token expiration
- `CORS_ORIGIN` - Allowed origins for CORS
- `RATE_LIMIT_*` - Rate limiting configuration

## Multi-Site SSO

The system supports multiple sites/applications:

1. Register sites in the `sso_sites` table
2. Configure user permissions per site
3. Use site-specific API keys for authentication
4. Validate tokens across all registered sites

## Production Deployment

1. Use environment variables for all configuration
2. Enable HTTPS/TLS termination
3. Configure proper CORS origins
4. Set up database connection pooling
5. Implement monitoring and logging
6. Regular secret rotation schedule

## License

ISC License