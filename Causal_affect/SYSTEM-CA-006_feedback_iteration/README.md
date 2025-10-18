# CA-006 Feedback Collection & Iteration Orchestrator

**System ID**: SYSTEM-CA-006  
**Status**: Development  
**Tech Stack**: FastAPI + PostgreSQL + Redis + Celery

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Start the Development Environment

```bash
# Copy environment variables
cp .env.example .env

# Edit .env and add your API keys (Google Analytics, Mixpanel, Amplitude)

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

### 2. Access the API

- **API Base URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

### 3. Run Database Migrations

```bash
# Apply migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Create a new migration (after model changes)
docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "description"
```

---

## 📁 Project Structure

```
SYSTEM-CA-006_feedback_iteration/
├── src/backend/
│   └── app/
│       ├── main.py              # FastAPI application entry point
│       ├── config.py            # Configuration & settings
│       ├── api/                 # API route handlers
│       ├── core/                # Business logic
│       ├── db/                  # Database connection & base
│       ├── middleware/          # CORS, logging, error handling
│       └── schemas/             # Pydantic models
│
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
│
├── FEATURE-CA-006-01_analytics_integration/
├── FEATURE-CA-006-02_engagement_tracking/
├── FEATURE-CA-006-03_revenue_tracking/
├── FEATURE-CA-006-04_prioritization_engine/
├── FEATURE-CA-006-05_archive_automation/
├── FEATURE-CA-006-06_dashboard_ui/
├── FEATURE-CA-006-07_admin_configuration/
│
├── requirements.txt             # Python dependencies
├── Dockerfile.dev               # Development container
├── Dockerfile                   # Production container
├── docker-compose.dev.yml       # Local dev environment
├── alembic.ini                  # Database migration config
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

---

## 🔧 Development

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://ca006_user:password@localhost:5432/feedback_iteration"
export REDIS_URL="redis://localhost:6379/0"

# Run development server
cd src/backend
uvicorn app.main:app --reload --port 8000
```

### Running Tests

```bash
# Run all tests
docker-compose -f docker-compose.dev.yml exec backend pytest

# Run with coverage
docker-compose -f docker-compose.dev.yml exec backend pytest --cov=app --cov-report=html

# Run specific feature tests
docker-compose -f docker-compose.dev.yml exec backend pytest tests/integration/test_analytics.py -v
```

### Code Quality

```bash
# Format code
docker-compose -f docker-compose.dev.yml exec backend black .

# Lint code
docker-compose -f docker-compose.dev.yml exec backend ruff check .

# Type checking
docker-compose -f docker-compose.dev.yml exec backend mypy app/
```

---

## 📊 API Endpoints

### Health & Status
- `GET /health` - Health check endpoint

### Analytics Integration (Feature CA-006-01)
- `POST /api/v1/analytics/collect` - Collect analytics from multiple sources
- `GET /api/v1/analytics/summary/{mvp_id}` - Get analytics summary

### Engagement Tracking (Feature CA-006-02)
- `POST /api/v1/engagement/events` - Track engagement events
- `GET /api/v1/engagement/metrics/{mvp_id}` - Get engagement metrics

### Revenue Tracking (Feature CA-006-03)
- `POST /api/v1/revenue/events` - Track conversion events
- `GET /api/v1/revenue/summary/{mvp_id}` - Get revenue metrics

### Prioritization Engine (Feature CA-006-04)
- `POST /api/v1/prioritization/calculate` - Calculate priority scores
- `GET /api/v1/prioritization/ranked` - Get ranked feedback items

### Archive Automation (Feature CA-006-05)
- `POST /api/v1/archive/mvp/{mvp_id}` - Archive MVP and related data
- `GET /api/v1/archive/status/{mvp_id}` - Check archive status

### Dashboard (Feature CA-006-06)
- `GET /api/v1/dashboard/overview` - Portfolio overview
- `GET /api/v1/dashboard/mvp/{mvp_id}` - MVP detailed view

---

## 🔐 Environment Variables

See `.env.example` for all available configuration options.

### Required Variables
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
SECRET_KEY=your_secret_key
```

### API Keys (Optional - for analytics features)
```bash
GOOGLE_ANALYTICS_CREDENTIALS=path/to/credentials.json
MIXPANEL_API_SECRET=your_api_secret
AMPLITUDE_API_KEY=your_api_key
```

---

## 🗄️ Database

### PostgreSQL Schema
The system uses PostgreSQL 15+ for persistent storage:
- Feedback items and iterations
- Analytics events
- Revenue tracking data
- User engagement metrics

### Redis Cache
Redis is used for:
- Session data
- Real-time metrics caching
- Celery task queue

### Migrations
Database migrations are managed with Alembic. To create a new migration:

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add new table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## 🐳 Docker Services

### Backend (FastAPI)
- Port: 8000
- Hot-reload enabled in dev mode
- Auto-restarts on code changes

### PostgreSQL
- Port: 5432
- Database: `feedback_iteration`
- Persistent volume: `postgres_data`

### Redis
- Port: 6379
- Persistent volume: `redis_data`

### Celery Worker
- Processes background tasks
- Monitors Redis queue
- Auto-scales based on load

---

## 📈 Monitoring & Logs

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f postgres
docker-compose -f docker-compose.dev.yml logs -f celery-worker
```

### Log Files
Application logs are mounted to `./logs/` directory for persistence.

---

## 🚢 Production Deployment

### Build Production Image
```bash
docker build -t ca006-backend:latest -f Dockerfile .
```

### Deploy to Railway (Recommended Platform)
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Railway will automatically build and deploy

### Environment-Specific Configurations
- **Development**: Hot-reload, debug mode, verbose logging
- **Production**: Multiple workers, optimized builds, error tracking

---

## 🧪 Testing

### Test Structure
```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for features
└── e2e/              # End-to-end tests for complete workflows
```

### Run Specific Tests
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=app --cov-report=term-missing
```

---

## 📚 Documentation

### System Documentation
- `SYSTEM_INTEGRATION_REPORT.md` - System integration details
- `SYSTEM_TEST_PYRAMID_*.yaml` - Test coverage metrics
- `SYSTEM_TRACEABILITY_MATRIX_*.yaml` - Requirements traceability

### Feature Documentation
Each feature has its own documentation in:
```
FEATURE-CA-006-XX_feature_name/
└── Requirements Verification/
    ├── feature_test_pyramid_*.yaml
    └── feature_traceability_matrix_*.yaml
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/new-feature`
2. Make changes and add tests
3. Run tests: `pytest`
4. Format code: `black .`
5. Commit: `git commit -m "Add new feature"`
6. Push: `git push origin feature/new-feature`

---

## 📞 Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review feature-specific documentation in `FEATURE-CA-006-XX/` directories
- Check system logs: `docker-compose logs -f backend`

---

## 📄 License

Proprietary - Causal Affect Internal Use Only
