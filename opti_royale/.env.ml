# Extended Environment Configuration for ML and Data Persistence

# Existing Azure configuration...
# [Previous content remains]

# Machine Learning Pipeline
AZURE_ML_WORKSPACE=your-ml-workspace
AZURE_ML_COMPUTE_CLUSTER=gpu-cluster
AZURE_ML_EXPERIMENT_NAME=clash-royale-optimization
MODEL_TRAINING_SCHEDULE=daily
MODEL_RETRAIN_THRESHOLD=1000  # Retrain after 1000 new analyses

# Data Lake for Training Data
AZURE_DATA_LAKE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=account;AccountKey=key;EndpointSuffix=core.windows.net
AZURE_DATA_LAKE_CONTAINER=training-data
AZURE_SYNAPSE_WORKSPACE=opti-royale-synapse

# Vector Database for Similarity Search
AZURE_COGNITIVE_SEARCH_ENDPOINT=https://search-service.search.windows.net
AZURE_COGNITIVE_SEARCH_KEY=your-search-key
AZURE_COGNITIVE_SEARCH_INDEX=game-patterns

# Time Series Database for Analytics
AZURE_TIME_SERIES_INSIGHTS_ENVIRONMENT=opti-royale-tsi
INFLUXDB_URL=https://influx.azure.com
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=opti-royale
INFLUXDB_BUCKET=game-analytics

# Data Science and ML Training
JUPYTER_NOTEBOOK_ENABLED=true
MLFLOW_TRACKING_URI=https://mlflow.azure.com
TENSORBOARD_LOG_DIR=/app/logs/tensorboard
MODEL_VERSIONING_ENABLED=true

# Feature Store
FEAST_FEATURE_STORE_REPO=/app/feature_store
FEAST_ONLINE_STORE_TYPE=redis
FEAST_OFFLINE_STORE_TYPE=azure_synapse

# Real-time Model Serving
TRITON_INFERENCE_SERVER_URL=http://triton:8000
ONNX_MODEL_CACHE_SIZE=10
MODEL_A_B_TESTING_ENABLED=true
CHAMPION_CHALLENGER_RATIO=90:10

# Data Pipeline Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_GAME_EVENTS=game-events
KAFKA_TOPIC_MODEL_PREDICTIONS=model-predictions
SPARK_MASTER_URL=spark://spark-master:7077

# Privacy and Compliance
DATA_RETENTION_DAYS=2555  # 7 years
GDPR_COMPLIANCE_ENABLED=true
DATA_ANONYMIZATION_ENABLED=true
PII_DETECTION_ENABLED=true
