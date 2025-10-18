# SYSTEM-CA-001: Data Ingestion & Processing Engine

A high-performance data ingestion and processing system built with FastAPI, TimescaleDB, and Celery for scalable time-series data handling.

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐
│  External APIs  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Feature  │
    │    01    │──► API Connector (HTTP, Auth, Rate Limiting, Circuit Breaker)
    └──────────┘
         │
    ┌────▼─────┐
    │ Feature  │
    │    02    │──► Data Validation (Schema, Cleaning, Transform, Quality)
    └──────────┘
         │
    ┌────▼─────┐
    │ Feature  │
    │    03    │──► TimeSeries Storage (TimescaleDB, Partitioning, Compression)
    └──────────┘
         │
    ┌────▼─────┐
    │ Feature  │
    │    04    │──► Monitoring (Metrics, Alerting, Prometheus)
    └──────────┘
```

### Features

#### 01: API Connector
- **HTTP Client**: Async HTTP requests with connection pooling
- **Authentication Manager**: OAuth, API key, JWT support
- **Rate Limiter**: Token bucket algorithm
- **Circuit Breaker**: Fail-fast pattern for external APIs

#### 02: Data Validation
- **Schema Validator**: JSON schema validation
- **Data Cleaner**: Null removal, deduplication, normalization
- **Transformer**: Format transformation, snake_case conversion
- **Quality Checker**: Data quality rules and thresholds

#### 03: TimeSeries Storage
- **DB Connection**: Async PostgreSQL/TimescaleDB
- **Partitioner**: Automatic time-based partitioning
- **Indexer**: Optimized query indexes
- **Compressor**: Data compression for old data

#### 04: Monitoring
- **Metrics Collector**: Prometheus metrics
- **Alerting**: Threshold-based alerts

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+

### 1. Clone and Configure
```bash
cd SYSTEM-CA-001_data_ingestion_processing
cp .env.example .env
# Edit .env with your configuration
```

### 2. Deploy with Docker Compose
```bash
./scripts/deploy.sh
```

Or manually:
```bash
docker-compose up -d
```

### 3. Verify Deployment
```bash
# Check API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Check Prometheus metrics
open http://localhost:9090
```

## 📡 API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /status` - Feature status overview
- `GET /metrics` - Prometheus metrics

### Data Ingestion
(TODO: Add specific endpoints once integration is complete)

## 🛠️ Development

### Local Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Running Tests
```bash
pytest tests/ -v --cov=app
```

### Code Quality
```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## 📊 Database Schema

### TimescaleDB Tables
- **timeseries_data**: Main time-series data table (hypertable)
- **api_configs**: API connector configurations
- **validation_rules**: Data validation rules
- **system_metrics**: System performance metrics

### Migrations
```bash
# Run migrations
docker-compose run --rm backend alembic upgrade head

# Create new migration
docker-compose run --rm backend alembic revision --autogenerate -m "description"
```

## 🔧 Configuration

### Environment Variables
See `.env.example` for all configuration options.

Key settings:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery
- `LOG_LEVEL`: Logging verbosity (debug, info, warning, error)
- `FEATURE_*_ENABLED`: Feature flags for each component

### Celery Tasks
Background tasks are configured in `app/integration/tasks.py`:
- `ingest_data_task`: Async data ingestion pipeline
- `health_check_task`: Periodic system health checks
- `cleanup_old_data_task`: Data retention cleanup

## 📈 Monitoring

### Prometheus Metrics
Available at `http://localhost:9090`

Metrics exposed:
- `http_requests_total`: HTTP request counter
- `http_request_duration_seconds`: Request latency histogram
- `feature_status`: Feature health (1=healthy, 0=unhealthy)
- `data_records_processed_total`: Data processing counter
- `active_db_connections`: Database connection pool

### Logs
```bash
# View all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

## 🏭 Production Deployment

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Add environment variables from `.env.example`
3. Deploy the `backend` service
4. Add TimescaleDB and Redis plugins

### Scaling
```yaml
# docker-compose.override.yml
services:
  celery_worker:
    deploy:
      replicas: 3  # Scale workers
```

### Security Checklist
- [ ] Change `SECRET_KEY` in production
- [ ] Update `DB_PASSWORD`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable audit logging

## 📝 Project Structure
```
SYSTEM-CA-001_data_ingestion_processing/
├── src/backend/app/
│   ├── features/          # Feature implementations
│   │   ├── api_connector/
│   │   ├── data_validation/
│   │   ├── timeseries_storage/
│   │   └── monitoring/
│   ├── integration/       # System orchestration
│   ├── db/               # Database layer
│   ├── middleware/       # FastAPI middleware
│   ├── routes/           # API routes
│   └── schemas/          # Pydantic models
├── tests/               # Test suite
├── scripts/             # Deployment scripts
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-service orchestration
└── requirements.txt     # Python dependencies
```

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test: `pytest tests/`
3. Format code: `black app/`
4. Commit: `git commit -m "Add new feature"`
5. Push: `git push origin feature/new-feature`
6. Open pull request

## 📄 License

Proprietary - Causal Affect Project

## 🆘 Troubleshooting

### Common Issues

**Database connection failed**
```bash
# Check if TimescaleDB is running
docker-compose ps timescaledb

# View logs
docker-compose logs timescaledb
```

**Celery workers not processing tasks**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart workers
docker-compose restart celery_worker
```

**High memory usage**
```bash
# Adjust connection pool size in .env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
```

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
- Check documentation in `/docs`

---

**Status**: ✅ Active Development
**Version**: 1.0.0
**Last Updated**: October 2025
