# FastAPI Production Application

## Overview

Production-ready FastAPI application with PostgreSQL, Redis, and comprehensive DevOps setup.

## Features

- **FastAPI 0.104+** with async/await support
- **SQLAlchemy 2.0+** with async PostgreSQL
- **Redis** for caching and rate limiting
- **Alembic** for database migrations
- **Docker** development environment
- **Railway** deployment configuration
- **Type hints** and Pydantic validation
- **Health checks** and monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Local Development

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd <project-name>
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Access application**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

## Project Structure

```
├── api/              # Route handlers
├── db/               # Database models & repositories  
├── models/           # Pydantic schemas
├── services/         # Business logic
├── core/             # Core configuration
├── migrations/       # Alembic migrations
├── tests/            # Test suite
└── main.py           # Application entry point
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Type checking
mypy .

# Linting
ruff check .
black --check .
```

## Deployment

### Railway

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and initialize**
   ```bash
   railway login
   railway init
   ```

3. **Deploy**
   ```bash
   railway up
   ```

### Environment Variables

Required for production:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string  
- `SECRET_KEY`: JWT secret key
- `ENVIRONMENT`: Set to "production"

### Health Checks

- `/health`: Application health
- `/health/db`: Database connectivity
- `/health/redis`: Redis connectivity

## Monitoring

- Prometheus metrics: `/metrics`
- OpenTelemetry traces (optional)
- Structured JSON logging

## Security

- JWT authentication
- Rate limiting
- CORS configuration
- SQL injection protection
- XSS prevention

## Performance

- Async/await for I/O operations
- Redis caching
- Database connection pooling
- Response compression
- Static file serving

## Troubleshooting

### Database connection issues
```bash
# Check database is running
docker-compose ps

# View logs
docker-compose logs db
```

### Redis connection issues
```bash
# Test Redis connection
docker exec -it redis-cache redis-cli ping
```

### Application logs
```bash
# View application logs
docker-compose logs app
```

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - see LICENSE file for details