# Feasibility Platform - Authentication & Multi-Tenancy Integration

## Version 1.1.0 - Complete Integration Summary

### 🎉 What's New

This update transforms the Feasibility Platform from a single-user tool into a production-ready SaaS application with:

- **User Authentication** (JWT-based, secure password hashing)
- **Multi-Tenancy** (User-isolated data for baselines and exploration history)
- **Stripe Payments** (Free tier + Pro subscription at £9.99/month)
- **Admin System** (First registered user becomes admin automatically)
- **Landing Page** (Marketing page with features and pricing)
- **Subscription Limits** (Free: 5 explorations/month, Pro: unlimited)

---

## 🏗️ Architecture Overview

### Backend Structure
```
backend/
├── app/
│   ├── auth/               # Authentication module
│   │   ├── router.py       # /auth/register, /login, /refresh, /me
│   │   ├── utils.py        # JWT tokens, password hashing
│   │   ├── dependencies.py # get_current_user dependency
│   │   └── schemas.py      # Pydantic models
│   │
│   ├── payments/           # Stripe integration
│   │   ├── router.py       # /stripe/tiers, /create-checkout-session, /webhook
│   │   └── stripe_service.py # Payment logic
│   │
│   ├── models/             # Database models
│   │   └── __init__.py     # User, Baseline, ExplorationHistory
│   │
│   ├── middleware/         # Request middleware
│   │   └── subscription.py # Usage limits enforcement
│   │
│   ├── engines/            # Calculation engines (unchanged)
│   ├── database.py         # SQLAlchemy setup (PostgreSQL/SQLite)
│   └── main.py             # FastAPI app with all routers
│
├── version.py              # Version tracking
└── requirements.txt        # Updated with auth/payment deps
```

### Frontend Structure
```
frontend/
├── src/
│   ├── contexts/
│   │   └── AuthContext.tsx      # Global auth state management
│   │
│   ├── pages/
│   │   ├── LandingPage.tsx      # Public marketing page
│   │   ├── LoginPage.tsx        # User login form
│   │   ├── RegisterPage.tsx     # New user registration
│   │   └── AppWrapper.tsx       # Authenticated app wrapper
│   │
│   ├── components/
│   │   └── ProtectedRoute.tsx   # Auth guard for routes
│   │
│   ├── App.tsx                  # Main feasibility tool (unchanged)
│   └── main.tsx                 # Router setup
│
└── package.json                 # Updated with react-router-dom
```

---

## 🔐 Authentication Flow

### 1. First User Registration (YOU become Admin)
```
1. Navigate to http://localhost:5173/register
2. Fill in email, password, full name
3. Click "Create Account"
4. ✅ Automatically logged in
5. ✅ First user is marked as is_superuser=True (ADMIN)
6. ✅ Redirected to /app (main feasibility tool)
```

### 2. Subsequent User Registration
```
1. Same registration flow
2. ✅ Created with Free tier (5 explorations/month)
3. ✅ is_superuser=False (regular user)
```

### 3. Login Flow
```
1. Navigate to http://localhost:5173/login
2. Enter email and password
3. ✅ JWT tokens stored in localStorage
4. ✅ Redirected to /app
```

### 4. Protected Routes
```
/ (Landing Page)        → Public
/login                  → Public
/register               → Public
/app                    → Protected (requires authentication)
```

---

## 💳 Subscription Tiers

### Free Tier
- ✅ 5 feasibility explorations per month
- ✅ Basic visualizations
- ✅ Baseline comparison
- ✅ Export results
- ❌ Advanced visualizations limited
- ❌ Multiple baselines limited

### Pro Tier (£9.99/month)
- ✅ Unlimited explorations
- ✅ All 9 visualization modes
- ✅ Multiple baselines
- ✅ Exploration history export
- ✅ Priority support
- ✅ API access

---

## 🗄️ Database Schema

### Users Table
```sql
users:
  - id: Integer (PK)
  - email: String (unique)
  - hashed_password: String
  - full_name: String
  - is_active: Boolean
  - is_superuser: Boolean        # Admin flag (first user only)
  - subscription_tier: Enum (free, pro)
  - stripe_customer_id: String
  - stripe_subscription_id: String
  - subscription_status: String
  - monthly_explorations: Integer
  - monthly_explorations_reset_date: DateTime
  - created_at: DateTime
  - updated_at: DateTime
```

### Baselines Table (Multi-Tenant)
```sql
baselines:
  - id: Integer (PK)
  - user_id: Integer (FK → users.id)  # Isolates data per user
  - baseline_data: JSON
  - name: String
  - is_active: Boolean
  - created_at: DateTime
  - updated_at: DateTime
```

### Exploration History Table (Multi-Tenant)
```sql
exploration_history:
  - id: Integer (PK)
  - user_id: Integer (FK → users.id)  # Isolates data per user
  - input_parameters: JSON
  - result_data: JSON
  - performance_score: Float
  - durability_score: Float
  - economic_score: Float
  - delta_performance: Float
  - delta_durability: Float
  - delta_economic: Float
  - notes: Text
  - created_at: DateTime
```

---

## 🚀 Local Development Setup

### 1. Backend Setup
```bash
cd /workspaces/business_ventures/feasibility_tool/backend

# Install dependencies (already done)
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and set JWT_SECRET_KEY (for production)
# For local dev, defaults are fine

# Run backend
python -m app.main
# ✅ Server running at http://localhost:8000
# ✅ Database tables auto-created on first run
```

### 2. Frontend Setup
```bash
cd /workspaces/business_ventures/feasibility_tool/frontend

# Install dependencies (already done)
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run frontend
npm run dev
# ✅ App running at http://localhost:5173
```

### 3. Test the Integration
```bash
# 1. Open http://localhost:5173
# 2. Click "Start Free Trial" → /register
# 3. Create account with YOUR email (becomes admin)
# 4. Check top-right corner shows: "your@email.com (Admin) · Free"
# 5. Click around feasibility tool
# 6. Try 6 explorations → should hit free tier limit
# 7. Click logout, then login again to verify auth works
```

---

## 🔧 Stripe Configuration (Optional for Local Dev)

### Get Stripe Keys
```bash
1. Sign up at https://dashboard.stripe.com
2. Get test keys from: https://dashboard.stripe.com/test/apikeys
3. Create a Product with £9.99/month price
4. Get price_id (starts with price_...)
5. Set up webhook endpoint: https://yourapp.railway.app/stripe/webhook
6. Get webhook secret (starts with whsec_...)
```

### Update .env
```bash
STRIPE_SECRET_KEY=sk_test_your_actual_key
STRIPE_PRICE_ID_PRO=price_your_actual_price_id
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

---

## 📦 Railway Deployment

### Environment Variables Needed

**Backend Service:**
```
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-injected by Railway
JWT_SECRET_KEY=your-production-secret-min-32-chars
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_PRICE_ID_PRO=price_your_pro_tier_price
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
FRONTEND_URL=https://your-frontend-domain.railway.app
PORT=8000
```

**Frontend Service:**
```
VITE_API_URL=https://your-backend-domain.railway.app
PORT=3000
```

### Deployment Steps
1. Push code to GitHub
2. Railway auto-detects changes and deploys
3. Add PostgreSQL database plugin in Railway
4. Configure environment variables
5. Set up custom domains
6. Configure Stripe webhook URL: `https://your-backend.railway.app/stripe/webhook`

---

## 🛡️ Security Features

✅ **Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number

✅ **JWT Tokens:**
- Access token: 24 hours expiry
- Refresh token: 7 days expiry
- Secure HS256 signing

✅ **Database:**
- Passwords hashed with bcrypt
- SQL injection protection via SQLAlchemy
- User data isolation with foreign keys

---

## 📊 API Endpoints

### Authentication
```
POST /auth/register          # Create new user
POST /auth/login             # Login and get tokens
POST /auth/refresh           # Refresh access token
GET  /auth/me                # Get current user info
```

### Payments
```
GET  /stripe/tiers                      # Get pricing tiers
POST /stripe/create-checkout-session   # Start checkout
POST /stripe/create-portal-session     # Manage subscription
POST /stripe/webhook                    # Stripe webhook handler
```

### Engines (Existing - Need Auth Update)
```
GET  /api/engines                      # List engines
POST /api/engines/{id}/calculate       # Run calculation
GET  /api/engines/{id}/input-schema    # Get input schema
```

---

## 🎯 Next Steps (Final Integration)

### Update Existing Endpoints to Require Auth:
1. Add `Depends(get_current_user)` to `/api/engines/{id}/calculate`
2. Add subscription limit check before calculation
3. Increment user's monthly_explorations counter
4. Filter baselines and history by user_id
5. Create API endpoints for baseline/history CRUD operations

### Example:
```python
from app.auth.dependencies import get_current_user
from app.middleware.subscription import check_exploration_limit, increment_exploration_count

@app.post("/api/engines/{engine_id}/calculate")
async def calculate(
    engine_id: str, 
    inputs: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check subscription limits
    await check_exploration_limit(current_user, db)
    
    # Perform calculation
    engine = registry.get_engine(engine_id)
    result = engine.calculate(inputs)
    
    # Increment usage counter
    await increment_exploration_count(current_user, db)
    
    # Save to history with user_id
    history = ExplorationHistory(
        user_id=current_user.id,
        input_parameters=inputs,
        result_data=result.dict(),
        ...
    )
    db.add(history)
    db.commit()
    
    return result
```

---

## ✅ What's Been Completed

- ✅ Backend auth infrastructure (JWT, password hashing)
- ✅ User model with subscription tiers
- ✅ Database configuration (PostgreSQL/SQLite)
- ✅ Stripe payment integration
- ✅ Frontend auth context and pages
- ✅ Landing page with pricing
- ✅ React Router with protected routes
- ✅ Subscription enforcement middleware
- ✅ Railway deployment configuration
- ✅ Admin system (first user becomes admin)
- ✅ Environment variable documentation

---

## 🚧 Remaining Work

- ❌ Update `/api/engines/{id}/calculate` to require auth
- ❌ Add baseline CRUD endpoints with user_id filtering
- ❌ Add exploration history CRUD endpoints with user_id filtering
- ❌ Update frontend to call new authenticated endpoints
- ❌ Add usage stats display in frontend
- ❌ Add upgrade prompts when hitting free tier limits

---

## 🎓 Admin Features (You)

As the first registered user, you have:
- ✅ `is_superuser=True` flag
- ✅ Visible in UI: "email@example.com (Admin)"
- 🔮 Future: Admin dashboard to view all users
- 🔮 Future: Ability to manually upgrade users
- 🔮 Future: Platform analytics and metrics

---

## 📞 Support

For issues or questions:
1. Check backend logs: `railway logs -s feasibility-api`
2. Check frontend logs: `railway logs -s feasibility-frontend`
3. Verify environment variables are set correctly
4. Test Stripe webhooks with Stripe CLI: `stripe listen --forward-to localhost:8000/stripe/webhook`

---

**Built with ❤️ using FastAPI, React, SQLAlchemy, Stripe, and Railway**
