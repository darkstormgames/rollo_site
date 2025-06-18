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

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src
```

## Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Contributing

Follow the monorepo development workflow. See main repository README for details.