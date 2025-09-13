#!/bin/bash

# Azure Production Deployment Script for OptiRoyale
# High-Performance Clash Royale Analysis Platform

set -e

echo "🚀 Starting Azure deployment for OptiRoyale..."

# Configuration
RESOURCE_GROUP="opti-royale-prod"
LOCATION="eastus2"  # Choose region with GPU availability
SUBSCRIPTION_ID="your-subscription-id"
AKS_CLUSTER_NAME="opti-royale-aks"
ACR_NAME="optiroyaleacr"

# Set subscription
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry (Premium for geo-replication)
echo "🐳 Creating Azure Container Registry..."
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Premium \
  --location $LOCATION \
  --admin-enabled true

# Create AKS cluster with enterprise-scale GPU nodes
echo "☸️ Creating enterprise-scale AKS cluster..."
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --node-count 5 \
  --node-vm-size Standard_D8s_v3 \
  --enable-cluster-autoscaler \
  --min-count 5 \
  --max-count 50 \
  --network-plugin azure \
  --enable-managed-identity \
  --attach-acr $ACR_NAME \
  --kubernetes-version 1.28.0 \
  --load-balancer-sku standard \
  --vm-set-type VirtualMachineScaleSets

# Add large GPU node pool for enterprise CV processing
echo "🎮 Adding enterprise GPU node pool..."
az aks nodepool add \
  --resource-group $RESOURCE_GROUP \
  --cluster-name $AKS_CLUSTER_NAME \
  --name gpupool \
  --node-count 10 \
  --node-vm-size Standard_NC24s_v3 \
  --node-taints nvidia.com/gpu=true:NoSchedule \
  --enable-cluster-autoscaler \
  --min-count 5 \
  --max-count 30 \
  --max-pods-per-node 50

# Add high-memory pool for video processing
echo "🧠 Adding high-memory node pool..."
az aks nodepool add \
  --resource-group $RESOURCE_GROUP \
  --cluster-name $AKS_CLUSTER_NAME \
  --name highmempool \
  --node-count 5 \
  --node-vm-size Standard_E32s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 20

# Create Azure Database for PostgreSQL Flexible Server
echo "🗄️ Creating PostgreSQL Flexible Server..."
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name opti-royale-postgres \
  --location $LOCATION \
  --admin-user postgres \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose \
  --storage-size 1024 \
  --version 15 \
  --high-availability Enabled \
  --backup-retention 30

# Create Azure Cache for Redis Premium (Enterprise Scale)
echo "🔴 Creating Redis Premium Enterprise cache..."
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name opti-royale-redis \
  --location $LOCATION \
  --sku Premium \
  --vm-size P5 \
  --redis-configuration maxmemory-policy=allkeys-lru \
  --enable-non-ssl-port false \
  --shard-count 3 \
  --static-ip

# Create Azure Storage Account (Premium SSD)
echo "💾 Creating Storage Account..."
az storage account create \
  --name optiroyalestorage \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Premium_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --enable-large-file-share

# Create Azure CDN for global content delivery
echo "🌐 Creating CDN profile..."
az cdn profile create \
  --resource-group $RESOURCE_GROUP \
  --name opti-royale-cdn \
  --sku Standard_Microsoft \
  --location Global

# Create Computer Vision service
echo "👁️ Creating Computer Vision service..."
az cognitiveservices account create \
  --name opti-royale-vision \
  --resource-group $RESOURCE_GROUP \
  --kind ComputerVision \
  --sku S1 \
  --location $LOCATION

# Create Application Insights
echo "📊 Creating Application Insights..."
az monitor app-insights component create \
  --app opti-royale-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --kind web \
  --application-type web

# Create Azure Key Vault for secrets
echo "🔐 Creating Key Vault..."
az keyvault create \
  --name opti-royale-kv \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku premium \
  --enable-rbac-authorization

# Get AKS credentials
echo "🔑 Getting AKS credentials..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME

# Install NVIDIA GPU operator for AKS
echo "🎮 Installing NVIDIA GPU operator..."
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/gpu-operator/main/deployments/gpu-operator/values.yaml

# Build and push images to ACR
echo "🏗️ Building and pushing container images..."
az acr login --name $ACR_NAME

# Build API image
docker build -f apps/api/Dockerfile.azure -t $ACR_NAME.azurecr.io/opti-royale-api:latest apps/api/
docker push $ACR_NAME.azurecr.io/opti-royale-api:latest

# Build CV service image
docker build -f services/cv-analyzer/Dockerfile.azure-gpu -t $ACR_NAME.azurecr.io/opti-royale-cv:latest services/cv-analyzer/
docker push $ACR_NAME.azurecr.io/opti-royale-cv:latest

# Build web app image
docker build -f apps/web/Dockerfile.azure -t $ACR_NAME.azurecr.io/opti-royale-web:latest apps/web/
docker push $ACR_NAME.azurecr.io/opti-royale-web:latest

# Deploy to AKS
echo "☸️ Deploying to AKS..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/cv-deployment.yaml
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Setup monitoring
echo "📊 Setting up monitoring..."
kubectl apply -f k8s/monitoring/

echo "✅ Azure deployment completed successfully!"
echo "🌐 Your application will be available at the ingress endpoint"
echo "📊 Monitor your application in Azure Portal and Application Insights"

# Display important endpoints
echo "📋 Important endpoints:"
echo "- AKS cluster: $AKS_CLUSTER_NAME"
echo "- Container Registry: $ACR_NAME.azurecr.io"
echo "- PostgreSQL: opti-royale-postgres.postgres.database.azure.com"
echo "- Redis: opti-royale-redis.redis.cache.windows.net"
