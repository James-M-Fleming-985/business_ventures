# Feasibility Platform - Railway Deployment Guide

## Version: 1.1.0

## Prerequisites
- Railway Pro account
- GitHub repository connected to Railway

## Deployment Architecture
This project consists of two services:
1. **Backend API** (FastAPI) - `/feasibility_tool/backend`
2. **Frontend** (React + Vite) - `/feasibility_tool/frontend`

## Initial Setup on Railway

### 1. Create New Project from GitHub
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `business_ventures` repository
5. Railway will detect both services

### 2. Configure Backend Service
1. **Service Name**: `feasibility-api-v1-1-0` (include version in name)
2. **Root Directory**: `/feasibility_tool/backend`
3. **Environment Variables**:
   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   
   # Database (PostgreSQL will be automatically provisioned by Railway)
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   
   # Authentication & Security
   JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars-change-in-production
   
   # Stripe Payment Integration
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
   STRIPE_PRICE_ID_PRO=price_your_stripe_price_id_for_pro_tier
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   
   # Frontend URL for CORS and redirects
   FRONTEND_URL=https://[your-frontend-domain]
   ```
4. **Build Settings**: Uses `railway.toml` in backend folder
5. **Custom Domain** (optional): e.g., `api-feasibility.up.railway.app`
6. **Database**: Add PostgreSQL plugin from Railway dashboard

### 3. Configure Frontend Service
1. **Service Name**: `feasibility-frontend-v1-1-0` (include version in name)
2. **Root Directory**: `/feasibility_tool/frontend`
3. **Environment Variables**:
   ```
   VITE_API_URL=https://[your-backend-url]
   PORT=3000
   ```
4. **Build Settings**: Uses `railway.toml` in frontend folder
5. **Custom Domain** (optional): e.g., `feasibility.up.railway.app`

### 4. Add PostgreSQL Database
1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Database will be automatically linked to backend service
4. `DATABASE_URL` environment variable will be injected automatically

## GitHub Integration & Auto-Deploy

### Enable Auto-Deploy from GitHub
1. In Railway project settings:
   - Go to **Settings** → **Source**
   - Ensure GitHub integration is active
   - Set **Branch**: `main`
   - Enable **Auto-Deploy** on push to main

### Version Control in Deployments
Railway automatically creates deployment history with:
- Git commit hash
- Timestamp
- Branch name

To track versions:
1. Update version in:
   - `backend/version.py` - Update `__version__`
   - `frontend/package.json` - Update `version`
2. Commit with version tag:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```
3. Railway will deploy with commit message visible

### Custom Deployment Names
To include version in deployment title:
1. Use semantic commit messages:
   ```bash
   git commit -m "release: v1.1.0 - Add resizable panels and cost overrides"
   ```
2. Railway displays commit message in deployment log

## Environment Variables Setup

### Backend (.env or Railway)
```bash
# No additional vars needed - uses defaults
```

### Frontend (.env or Railway)
```bash
VITE_API_BASE_URL=https://feasibility-api-v1-1-0.up.railway.app
```

## Deployment Process

### First Deployment
```bash
# 1. Commit version updates
git add .
git commit -m "release: v1.1.0 - Initial Railway deployment"
git tag v1.1.0
git push origin main --tags

# 2. Railway auto-deploys both services
# 3. Check deployment logs in Railway dashboard
```

### Subsequent Updates
```bash
# Update version numbers first
# backend/version.py: __version__ = "1.2.0"
# frontend/package.json: "version": "1.2.0"

git add .
git commit -m "release: v1.2.0 - Feature description"
git tag v1.2.0
git push origin main --tags

# Railway auto-deploys
```

## Version Display

The application displays the version in:
1. **Frontend Footer**: Shows `v{version}` fetched from backend API
2. **Backend API**: `/api/version` endpoint returns version info
3. **Health Check**: `/health` includes version in metadata

## Monitoring & Logs

### View Deployment Status
1. Railway Dashboard → Project → Deployments
2. Each deployment shows:
   - Git commit
   - Build logs
   - Runtime logs
   - Metrics

### Check Version
```bash
# Backend
curl https://[backend-url]/api/version

# Frontend - visible in footer
```

## Rollback Strategy

### Rollback to Previous Version
1. Go to Railway Dashboard → Deployments
2. Find previous successful deployment
3. Click "Redeploy"
4. Or use git:
   ```bash
   git revert HEAD
   git push origin main
   ```

## Health Checks

- **Backend**: `https://[backend-url]/health`
- **Frontend**: `https://[frontend-url]/` (serves static files)

Railway automatically monitors these and restarts on failure.

## Custom Domain Setup (Optional)

1. Railway Dashboard → Service → Settings → Networking
2. Add custom domain: `feasibility.yourdomain.com`
3. Update DNS with provided CNAME
4. Update frontend env var with new backend domain

## Troubleshooting

### Build Fails
- Check `railway.toml` configuration
- Verify `requirements.txt` or `package.json`
- Check build logs in Railway dashboard

### Version Not Updating
- Clear browser cache
- Check `/api/version` endpoint directly
- Verify version files were committed

### CORS Issues
- Ensure frontend URL is in backend CORS allowed origins
- Update in `backend/app/main.py` if using custom domains

## Production Checklist

- [ ] Update version numbers in all files
- [ ] Test locally with production build
- [ ] Commit with semantic version tag
- [ ] Push to main branch
- [ ] Verify Railway auto-deploy triggers
- [ ] Check both services are healthy
- [ ] Test version display in footer
- [ ] Verify API version endpoint
- [ ] Test full application functionality
- [ ] Monitor logs for errors

## Support

For Railway-specific issues:
- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)

For application issues:
- Check deployment logs
- Review environment variables
- Test API endpoints directly
