# CA-006 - FastAPI Application

Production-ready FastAPI application with PostgreSQL, Redis, and Celery.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### Local Development with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd ca-006
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. **Check service status**
```bash
docker-compose -f docker-compose.dev.yml ps
```

5. **View logs**
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
```

6. **Access the application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development without Docker

1. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start PostgreSQL and Redis**
```bash
# Using Docker for databases only
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

4. **Run migrations**
```bash
alembic upgrade head
```

5. **Start the application**
```bash
uvicorn main:app --reload
```

## 📁 Project Structure

```
ca-006/
├── alembic/                 # Database migrations
│   ├── versions/
│   └── env.py
├── api/                     # API routes
│   ├── v1/
│   └── deps.py
├── core/                    # Core configuration
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── db/                      # Database layer
│   ├── models.py           # SQLAlchemy models
│   ├── base.py
│   └── repositories/
├── models/                  # Pydantic schemas
│   ├── user.py
│   └── item.py
├── services/               # Business logic
│   ├── user_service.py
│   └── item_service.py
├── tasks/                  # Celery tasks
│   └── __init__.py
├── tests/                  # Test suite
│   ├── unit/
│   └── integration/
├── .env.example           # Environment variables template
├── alembic.ini           # Alembic configuration
├── docker-compose.dev.yml # Development containers
├── Dockerfile.dev        # Development Dockerfile
├── main.py              # Application entry point
├── celery_app.py        # Celery configuration
└── requirements.txt     # Python dependencies
```

## 🔧 Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_users.py
```

## 🔐 Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (min 32 characters)
- `ENVIRONMENT`: development/staging/production
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR

## 📦 Docker Commands

### Rebuild containers
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

### Stop all services
```bash
docker-compose -f docker-compose.dev.yml down
```

### Remove volumes (clean slate)
```bash
docker-compose -f docker-compose.dev.yml down -v
```

### Execute commands in container
```bash
docker-compose -f docker-compose.dev.yml exec backend bash
```

### View resource usage
```bash
docker stats
```

## 🚀 Deployment

### Production Build

1. **Update environment variables**
```bash
cp .env.example .env.production
# Configure production values
```

2. **Build production image**
```bash
docker build -t ca-006:latest -f Dockerfile .
```

3. **Run migrations**
```bash
docker run --rm ca-006:latest alembic upgrade head
```

4. **Deploy to container orchestration**
- Kubernetes
- Docker Swarm
- AWS ECS
- Google Cloud Run

### Environment-specific Configurations

**Development:**
- Debug mode enabled
- Hot reload active
- Verbose logging

**Production:**
- Debug mode disabled
- Optimized settings
- Error tracking (Sentry)
- Performance monitoring

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Application Metrics
```bash
curl http://localhost:8000/metrics
```

### Database Connection Pool
- Monitor in application logs
- Check PostgreSQL stats

## 🐛 Troubleshooting

### Database connection issues
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Test connection
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres
```

### Redis connection issues
```bash
# Check Redis is running
docker-compose -f docker-compose.dev.yml ps redis

# Test connection
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
```

### Migration errors
```bash
# Check current revision
alembic current

# View pending migrations
alembic history

# Reset to specific version
alembic downgrade <revision>
```

## 📝 API Documentation

Once the application is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

### Code Style
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team
- Check documentation at /docs
