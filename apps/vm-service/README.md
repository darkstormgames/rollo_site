# VM Management Service

FastAPI backend service for VM management within the rollo_site monorepo.

## Features

- FastAPI application with async support
- Environment-based configuration
- Health check endpoints
- CORS configuration for frontend integration
- Structured logging
- Docker development environment
- Database integration ready (SQLAlchemy + Alembic)
- VM management capabilities (libvirt integration ready)

## Quick Start

### Local Development

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment configuration:
```bash
cp .env.example .env
```

4. Start the development server:
```bash
python server.py
```

The service will be available at `http://localhost:8000`

### Docker Development

1. Start with Docker Compose:
```bash
cd docker
docker-compose up --build
```

This will start:
- VM Service API on port 8000
- PostgreSQL database on port 5432

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Health Checks

- Basic health: `GET /api/v1/health`
- Readiness: `GET /api/v1/health/ready`  
- Liveness: `GET /api/v1/health/live`

## Configuration

Configuration is managed through environment variables. See `.env.example` for all available options.

Key settings:
- `DEBUG`: Enable debug mode
- `HOST`, `PORT`: Server binding
- `DATABASE_URL`: Database connection string
- `CORS_ORIGINS`: Allowed CORS origins
- `LOG_LEVEL`: Logging level

## Project Structure

```
vm-service/
├── src/
│   ├── api/           # API route handlers
│   ├── core/          # Core functionality (config, logging)
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── tests/             # Test files
├── docker/            # Docker configuration
├── alembic/           # Database migrations
├── requirements.txt   # Python dependencies
└── server.py         # Application entry point
```

## Database Setup

### Prerequisites

For PostgreSQL (production):
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE vm_service;
CREATE USER vm_user WITH PASSWORD 'vm_password';
GRANT ALL PRIVILEGES ON DATABASE vm_service TO vm_user;
\q
```

### Initialize Database

```bash
# Initialize database with default data
python init_db.py

# Reset database (drops all tables)
python init_db.py --reset
```

### Database Models

The VM service includes the following database models:

**Core Models:**
- **User**: Authentication and authorization with RBAC
- **Role**: Role-based access control with JSON permissions
- **Server**: Physical/remote server management
- **VirtualMachine**: VM instance management
- **VMTemplate**: Predefined VM configurations

**Supporting Models:**
- **AuditLog**: Comprehensive action tracking
- **ServerMetrics**: Time-series metrics storage
- **VMSnapshot**: VM snapshot management

## Testing

```bash
# Run all tests
DATABASE_URL="sqlite:///test.db" pytest

# Run tests with coverage
DATABASE_URL="sqlite:///test.db" pytest --cov=src

# Run specific test files
DATABASE_URL="sqlite:///test.db" pytest tests/test_models.py -v
```

## Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# View migration history
alembic history

# Downgrade to previous migration
alembic downgrade -1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | Full database connection string |
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5432 | Database port |
| `DB_NAME` | vm_service | Database name |
| `DB_USER` | vm_user | Database user |
| `DB_PASSWORD` | - | Database password |
| `SECRET_KEY` | your-secret-key-here | JWT secret key |
| `DEBUG` | false | Enable debug mode |

## API Endpoints

### Health Checks
- `GET /api/v1/health` - Service health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### API Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

## Contributing

Follow the monorepo development workflow. See main repository README for details.