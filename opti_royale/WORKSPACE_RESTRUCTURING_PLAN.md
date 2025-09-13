# 🏗️ Workspace Restructuring Implementation Plan

## 🚨 Current Performance Issues

Based on our analysis:
- **34,444+ files** in single workspace causing lag
- **4.2GB+ RAM** usage during development
- **Multiple node_modules** directories (inefficient)
- **Monolithic structure** slowing down VS Code

## 📋 Phase 1: Immediate Restructuring (Next 2 Hours)

### **Step 1: Create Focused Workspaces**

```bash
# 1. Frontend Development Workspace (Lightweight)
mkdir -p /workspaces/opti-frontend
cd /workspaces/opti-frontend

# Initialize clean frontend workspace
npm init -y
npm install next@13 react@18 typescript tailwindcss

# 2. ML/CV Development Workspace (Isolated)
mkdir -p /workspaces/opti-ml
cd /workspaces/opti-ml

# Initialize ML workspace with Python
python3 -m venv venv
source venv/bin/activate
pip install tensorflow opencv-python numpy pandas

# 3. API Development Workspace (Backend)
mkdir -p /workspaces/opti-api
cd /workspaces/opti-api

# Initialize API workspace
npm init -y
npm install express typescript prisma @types/node
```

### **Step 2: Move Components by Concern**

#### **Frontend Components → opti-frontend**
```bash
# Move web application components
cp -r /workspaces/opti_royale/apps/web/* /workspaces/opti-frontend/
cp -r /workspaces/opti_royale/pro-battle-analysis.html /workspaces/opti-frontend/
cp -r /workspaces/opti_royale/pricing-tiers.html /workspaces/opti-frontend/

# Clean frontend-only package.json
cat > /workspaces/opti-frontend/package.json << EOF
{
  "name": "opti-royale-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^13.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "tailwindcss": "^3.0.0",
    "typescript": "^5.0.0"
  }
}
EOF
```

#### **ML/CV Components → opti-ml**
```bash
# Move machine learning components
cp -r /workspaces/opti_royale/services/cv-analyzer/* /workspaces/opti-ml/
cp -r /workspaces/opti_royale/services/ml-pipeline/* /workspaces/opti-ml/
cp /workspaces/opti_royale/scripts/generate-enhanced-database.py /workspaces/opti-ml/
cp /workspaces/opti_royale/enhanced_card_database.json /workspaces/opti-ml/

# Create ML requirements.txt
cat > /workspaces/opti-ml/requirements.txt << EOF
tensorflow==2.13.0
opencv-python==4.8.0
numpy==1.24.0
pandas==2.0.0
scikit-learn==1.3.0
matplotlib==3.7.0
pillow==10.0.0
requests==2.31.0
EOF
```

#### **API Components → opti-api**
```bash
# Move API and backend components
cp -r /workspaces/opti_royale/apps/api/* /workspaces/opti-api/
cp -r /workspaces/opti_royale/services/clash-royale-api/* /workspaces/opti-api/
cp -r /workspaces/opti_royale/real-analysis-api.js /workspaces/opti-api/
cp -r /workspaces/opti_royale/simple-api-server.js /workspaces/opti-api/

# Create API package.json
cat > /workspaces/opti-api/package.json << EOF
{
  "name": "opti-royale-api",
  "version": "1.0.0",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "prisma": "^5.0.0",
    "@prisma/client": "^5.0.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/express": "^4.17.0",
    "tsx": "^3.12.0"
  }
}
EOF
```

### **Step 3: VS Code Workspace Configuration**

#### **Frontend Workspace Settings**
```json
// /workspaces/opti-frontend/.vscode/settings.json
{
  "typescript.preferences.includePackageJsonAutoImports": "auto",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.next/**": true,
    "**/dist/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/.next": true,
    "**/dist": true
  },
  "typescript.preferences.maxDepth": 3,
  "typescript.disableAutomaticTypeAcquisition": true
}
```

#### **ML Workspace Settings**
```json
// /workspaces/opti-ml/.vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "files.watcherExclude": {
    "**/venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true,
    "**/models/**": true,
    "**/data/**": true
  },
  "search.exclude": {
    "**/venv": true,
    "**/__pycache__": true,
    "**/models": true,
    "**/data": true
  },
  "python.analysis.memory.keepLibraryAst": false
}
```

#### **API Workspace Settings**
```json
// /workspaces/opti-api/.vscode/settings.json
{
  "typescript.preferences.includePackageJsonAutoImports": "auto",
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/prisma/generated/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/prisma/generated": true
  },
  "typescript.preferences.maxDepth": 2
}
```

## 🐳 Step 4: Development Containers

### **Frontend Container**
```dockerfile
# /workspaces/opti-frontend/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Development command
CMD ["npm", "run", "dev"]
```

### **ML Container**
```dockerfile
# /workspaces/opti-ml/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Development command
CMD ["python", "-u", "main.py"]
```

### **API Container**
```dockerfile
# /workspaces/opti-api/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Generate Prisma client
RUN npx prisma generate

# Expose port
EXPOSE 5000

# Development command
CMD ["npm", "run", "dev"]
```

## 🔧 Step 5: Development Scripts

### **Master Development Script**
```bash
#!/bin/bash
# /workspaces/opti_royale/scripts/dev-start.sh

echo "🚀 Starting OptiRoyale Development Environment"

# Function to start service in background
start_service() {
    local service=$1
    local workspace=$2
    local command=$3
    
    echo "Starting $service..."
    cd $workspace
    gnome-terminal --tab --title="$service" -- bash -c "$command; exec bash"
}

# Start frontend development
start_service "Frontend" "/workspaces/opti-frontend" "npm run dev"

# Start API development  
start_service "API" "/workspaces/opti-api" "npm run dev"

# Start ML service (optional)
if [ "$1" = "--with-ml" ]; then
    start_service "ML Service" "/workspaces/opti-ml" "python main.py"
fi

echo "✅ All development services started!"
echo "📝 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:5000"
echo "🧠 ML Service: http://localhost:8000 (if enabled)"
```

### **Performance Monitoring Integration**
```bash
#!/bin/bash
# /workspaces/opti_royale/scripts/monitor-all.sh

echo "📊 Monitoring All Development Workspaces"

# Monitor each workspace separately
gnome-terminal --tab --title="Performance Monitor" -- bash -c "
    while true; do
        echo '=== Frontend Workspace ==='
        cd /workspaces/opti-frontend && du -sh . && ps aux | grep next
        echo '=== API Workspace ==='  
        cd /workspaces/opti-api && du -sh . && ps aux | grep express
        echo '=== ML Workspace ==='
        cd /workspaces/opti-ml && du -sh . && ps aux | grep python
        sleep 30
    done
"
```

## 📊 Expected Performance Improvements

### **Before Restructuring:**
- **Total Files**: 34,444
- **Memory Usage**: 4.2GB+
- **VS Code Response**: 2-5 seconds
- **Build Time**: 60+ seconds

### **After Restructuring:**
- **Frontend Workspace**: ~2,000 files, 512MB RAM
- **API Workspace**: ~1,500 files, 1GB RAM  
- **ML Workspace**: ~500 files, 2GB RAM
- **VS Code Response**: <500ms per workspace
- **Build Time**: <20 seconds per service

## 🎯 Implementation Timeline

### **Today (2 hours):**
1. ✅ Create workspace directories
2. ✅ Move components by concern
3. ✅ Set up VS Code configurations
4. ✅ Test basic functionality

### **Tomorrow:**
1. Create development containers
2. Set up inter-service communication
3. Implement performance monitoring
4. Train team on new workflow

### **This Week:**
1. Migrate all development to new structure
2. Optimize each workspace independently  
3. Set up automated performance gates
4. Document development guidelines

## 🚨 Risk Mitigation

### **Backup Strategy:**
- Keep original workspace intact until migration complete
- Version control all configuration changes
- Test each workspace independently before integration

### **Rollback Plan:**
- Symbolic links to maintain temporary compatibility
- Gradual migration over 1 week
- Parallel development capability during transition

Ready to execute Phase 1? This will immediately improve your development experience!
