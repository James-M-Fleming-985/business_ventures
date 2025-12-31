# Railway Deployment Checklist - Feasibility Platform

## Prerequisites
- [ ] Railway account (https://railway.app) - Sign up with GitHub
- [ ] Stripe account (https://dashboard.stripe.com) - For payments
- [ ] This repository pushed to GitHub

---

## Step-by-Step Deployment

### 1. Create Railway Project

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `business_ventures` repository
5. Railway will scan and detect the services

### 2. Add PostgreSQL Database

1. In your Railway project, click **"New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. PostgreSQL will be provisioned automatically
4. The `DATABASE_URL` environment variable will be injected into services

### 3. Configure Backend Service

**Service Settings:**
- **Name**: `feasibility-api-v1-1-0`
- **Root Directory**: Set to `/feasibility_tool/backend`
- **Watch Paths**: Leave empty (auto-detects from railway.toml)

**Environment Variables to Add:**
```env
# JWT Secret (CRITICAL - Generate a secure key)
JWT_SECRET_KEY=<generate-random-32-char-string>

# Stripe Keys (Get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PRICE_ID_PRO=price_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Frontend URL (Will set after frontend deploys)
FRONTEND_URL=https://<your-frontend-domain>.up.railway.app

# Database URL (Auto-injected by Railway when you link PostgreSQL)
# DATABASE_URL=${{Postgres.DATABASE_URL}}
```

**How to Generate JWT_SECRET_KEY:**
```bash
# Run this command locally:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output to JWT_SECRET_KEY
```

**Deploy Settings:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

### 4. Get Stripe Configuration

**Create Pro Subscription Product:**
1. Go to https://dashboard.stripe.com/test/products
2. Click **"Add product"**
3. Name: "Feasibility Platform Pro"
4. Pricing: £9.99 GBP / month (recurring)
5. Click **"Save product"**
6. Copy the **Price ID** (starts with `price_...`)

**Get API Keys:**
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy **Secret key** (starts with `sk_test_...`)
3. Paste into Railway backend environment variables

**Set Up Webhook:**
1. Go to https://dashboard.stripe.com/test/webhooks
2. Click **"Add endpoint"**
3. Endpoint URL: `https://<your-backend-domain>.up.railway.app/stripe/webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (starts with `whsec_...`)
6. Paste into Railway backend environment variables

### 5. Configure Frontend Service

**Service Settings:**
- **Name**: `feasibility-frontend-v1-1-0`
- **Root Directory**: Set to `/feasibility_tool/frontend`

**Environment Variables to Add:**
```env
# Backend API URL (Set after backend deploys)
VITE_API_URL=https://<your-backend-domain>.up.railway.app
```

**Deploy Settings:**
- Build Command: `npm install && npm run build`
- Start Command: `npm run preview -- --host 0.0.0.0 --port $PORT`
- Health Check Path: `/`

### 6. Get Domain URLs

**After Both Services Deploy:**

1. **Backend Domain:**
   - Go to backend service → Settings → Networking
   - Click **"Generate Domain"**
   - Copy the URL (e.g., `feasibility-api-v1-1-0.up.railway.app`)
   - Update frontend `VITE_API_URL` with this URL
   - Update backend `FRONTEND_URL` with frontend domain (from step 2)
   - Update Stripe webhook URL with this backend URL

2. **Frontend Domain:**
   - Go to frontend service → Settings → Networking
   - Click **"Generate Domain"**
   - Copy the URL (e.g., `feasibility-frontend-v1-1-0.up.railway.app`)
   - Update backend `FRONTEND_URL` with this URL

**Redeploy After URL Updates:**
- Both services will need to redeploy after you update the cross-referenced URLs
- Railway auto-deploys when you change environment variables

### 7. Verify Deployment

**Check Backend:**
1. Visit: `https://<backend-domain>/health`
2. Should return: `{"success": true, "data": {"status": "healthy"}}`
3. Visit: `https://<backend-domain>/docs`
4. Should show FastAPI Swagger documentation

**Check Frontend:**
1. Visit: `https://<frontend-domain>`
2. Should show landing page with "Transform Your Feasibility Analysis"
3. Click around to verify routing works

**Check Database:**
1. Backend logs should show: "✅ Database tables created successfully"
2. Check Railway PostgreSQL service for `users`, `baselines`, `exploration_history` tables

---

## Post-Deployment: Register as Admin

1. Visit your frontend URL: `https://<frontend-domain>`
2. Click **"Start Free Trial"** or **"Get Started Free"**
3. Fill in registration form with YOUR email
4. Click **"Create Account"**
5. **✨ You are now the admin!** (`is_superuser=True`)
6. Top-right corner shows: `your@email.com (Admin) · Free`
7. You're logged in and ready to use the platform

---

## Troubleshooting

### Backend Won't Start
- Check logs: Railway → Backend Service → Deployments → View logs
- Common issues:
  - Missing environment variables
  - Database connection failed (ensure PostgreSQL is linked)
  - Import errors (check requirements.txt is complete)

### Frontend Won't Connect to Backend
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in backend (should allow your frontend domain)
- Test backend API directly with curl or browser

### Database Errors
- Ensure PostgreSQL service is running
- Check `DATABASE_URL` is injected into backend
- View backend logs for SQLAlchemy errors
- Database tables should auto-create on first startup

### Stripe Webhook Not Working
- Verify webhook URL is correct: `https://<backend>/stripe/webhook`
- Check webhook secret is set in environment variables
- Test webhook with Stripe CLI:
  ```bash
  stripe listen --forward-to https://<backend>/stripe/webhook
  ```

---

## Environment Variables Summary

### Backend
| Variable | Example | Where to Get |
|----------|---------|--------------|
| `JWT_SECRET_KEY` | `abc123...` (32+ chars) | Generate with Python command above |
| `STRIPE_SECRET_KEY` | `sk_test_xxxxx` | https://dashboard.stripe.com/test/apikeys |
| `STRIPE_PRICE_ID_PRO` | `price_xxxxx` | Create product in Stripe dashboard |
| `STRIPE_WEBHOOK_SECRET` | `whsec_xxxxx` | Set up webhook endpoint in Stripe |
| `FRONTEND_URL` | `https://xxx.up.railway.app` | Railway frontend domain |
| `DATABASE_URL` | Auto-injected | Railway PostgreSQL service |

### Frontend
| Variable | Example | Where to Get |
|----------|---------|--------------|
| `VITE_API_URL` | `https://xxx.up.railway.app` | Railway backend domain |

---

## Custom Domains (Optional)

If you want custom domains like `app.yourdomain.com`:

1. Railway → Service → Settings → Networking
2. Click **"Custom Domain"**
3. Enter your domain
4. Add CNAME record in your DNS provider:
   - Name: `app` (or `api`)
   - Value: `<service-id>.up.railway.app`
5. Wait for DNS propagation (5-30 minutes)

---

## Auto-Deploy Setup

✅ **Already configured!** Railway auto-deploys when you push to GitHub.

To trigger a deployment:
```bash
cd /workspaces/business_ventures
git add .
git commit -m "Deploy feasibility platform v1.1.0"
git push
```

Railway will automatically:
1. Detect changes in `/feasibility_tool/backend` and `/feasibility_tool/frontend`
2. Build both services
3. Run database migrations
4. Deploy new versions
5. Keep old version running until new version is healthy

---

## Monitoring

**View Logs:**
- Railway → Service → Deployments → Click deployment → View logs

**Metrics:**
- Railway → Service → Metrics
- Shows CPU, memory, network usage

**Alerts:**
- Set up in Railway dashboard
- Get notified of deployment failures

---

## Cost Estimate

Railway pricing (as of 2025):
- **Hobby Plan**: $5/month (good for testing)
- **Pro Plan**: $20/month + usage (recommended for production)
- **PostgreSQL**: ~$5/month for small database

**Total estimated**: $10-30/month depending on usage

---

## Security Checklist

- [ ] JWT_SECRET_KEY is strong random string (32+ chars)
- [ ] Stripe keys are in environment variables (not code)
- [ ] DATABASE_URL is auto-injected (not hardcoded)
- [ ] CORS is configured to allow only your frontend domain
- [ ] HTTPS is enabled (Railway provides this automatically)
- [ ] Webhook signature verification is enabled

---

## Next Steps After Deployment

1. **Register as admin** in production
2. **Test full auth flow** (register, login, logout)
3. **Test subscription limits** (create 6 explorations as Free user)
4. **Set up Stripe in live mode** (when ready for real payments)
5. **Configure custom domains** (optional)
6. **Set up monitoring alerts**
7. **Invite beta users** to test

---

**You're ready to deploy! 🚀**

Follow the steps above in order, and you'll have a production-ready feasibility platform with authentication, payments, and multi-tenancy.
