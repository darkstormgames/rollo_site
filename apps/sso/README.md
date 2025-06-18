# Rollo SSO Backend

Secure Single Sign-On backend service for Rollo Site and other applications.

## Features

- 🔐 Secure JWT authentication with automatic secret rotation
- 🛡️ Password hashing using bcrypt with configurable salt rounds
- 🗄️ Sequelize ORM with MySQL database support
- 🔄 Refresh token mechanism for enhanced security
- 🌐 Multi-site SSO support with access level controls
- 👑 User access levels (admin, premium, standard, basic)
- 🔐 Site-specific access restrictions based on user level
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
# From the monorepo root
npm run install:sso

# Or from this directory
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
# From the monorepo root
npm run dev:sso

# Or from this directory:
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
- `GET /api/auth/sites` - Get accessible sites for user

### Admin Management

- `PUT /api/auth/admin/users/:userId/access-level` - Update user access level (admin only)
- `PUT /api/auth/admin/sites/:siteId/access-level` - Update site access level requirement (admin only)
- `GET /api/auth/admin/users` - List users by access level (admin only)

### Health Check

- `GET /health` - Server health status

## Access Level System

The system implements a hierarchical access level system for controlling site access:

### Access Levels (in order of priority)

1. **basic** - Entry level access
2. **standard** - Standard user access
3. **premium** - Premium user access
4. **admin** - Administrator access (full system control)

### How It Works

- **User Access Level**: Each user is assigned an access level when registered (defaults to 'basic')
- **Site Requirements**: Each site can specify a minimum access level requirement
- **Access Control**: Users can only access sites where their access level meets or exceeds the site's requirement

### Examples

- A user with 'premium' access can access sites requiring 'basic', 'standard', or 'premium' levels
- A user with 'basic' access can only access sites requiring 'basic' level
- Admin users can access all sites and manage other users' access levels

### Admin Functions

Only users with 'admin' access level can:
- Modify other users' access levels
- Change site access level requirements
- View all users and their access levels

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

The system uses Sequelize ORM with a comprehensive MySQL schema with the following tables:

- `users` - User accounts with secure password storage and access levels
- `refresh_tokens` - JWT refresh token management
- `jwt_secrets` - Secret key rotation tracking
- `user_sessions` - Session management and tracking
- `sso_sites` - Multi-site configuration with access level requirements
- `user_site_permissions` - Role-based access control per site

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

The system supports multiple sites/applications with access level controls:

1. Register sites in the `sso_sites` table with minimum access level requirements
2. Configure user permissions per site (optional, beyond access levels)
3. Use site-specific API keys for authentication
4. Validate tokens across all registered sites
5. Automatic access control based on user access levels vs site requirements

## Production Deployment

1. Use environment variables for all configuration
2. Enable HTTPS/TLS termination
3. Configure proper CORS origins
4. Set up database connection pooling
5. Implement monitoring and logging
6. Regular secret rotation schedule

## License

ISC License