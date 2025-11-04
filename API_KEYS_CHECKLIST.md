# API Keys & Secrets Checklist

## 🔐 Required for Deployment

### 1. Application Security Keys (CRITICAL)

**Generate these for production:**

```bash
# SECRET_KEY (for general app encryption)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT_SECRET_KEY (for JWT token signing)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY (for Fernet encryption - must be 32 url-safe base64-encoded bytes)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Set in Railway:**
```bash
railway variables set SECRET_KEY="<generated-secret>"
railway variables set JWT_SECRET_KEY="<generated-jwt-secret>"
railway variables set ENCRYPTION_KEY="<generated-encryption-key>"
```

⚠️ **NEVER commit these to Git!**

---

### 2. External Data Source API Keys (CA-002/CA-003)

These depend on what data sources you're using for correlation analysis:

#### Weather Data (for temperature correlations)
- [ ] **OpenWeatherMap**: https://openweathermap.org/api
  - Free tier: 1,000 calls/day
  - Variable: `WEATHER_API_KEY`
  
- [ ] **WeatherAPI.com**: https://www.weatherapi.com/
  - Free tier: 1M calls/month
  - Variable: `WEATHER_API_KEY`

#### Financial/Economic Data
- [ ] **Alpha Vantage**: https://www.alphavantage.co/
  - Free tier: 5 calls/minute, 500 calls/day
  - Variable: `FINANCIAL_DATA_API_KEY`
  
- [ ] **Polygon.io**: https://polygon.io/
  - Free tier: 5 calls/minute
  - Variable: `POLYGON_API_KEY`

- [ ] **Yahoo Finance** (via yfinance library)
  - No API key needed
  - Already in requirements.txt (if needed)

#### Social Media/Trends Data
- [ ] **Twitter/X API**: https://developer.twitter.com/
  - Variable: `TWITTER_API_KEY`, `TWITTER_API_SECRET`
  
- [ ] **Google Trends** (via pytrends library)
  - No API key needed
  - Can add to requirements.txt

#### General Data Sources
- [ ] **Kaggle API**: https://www.kaggle.com/docs/api
  - For downloading datasets
  - Variable: `KAGGLE_USERNAME`, `KAGGLE_KEY`

---

### 3. Infrastructure Services (Auto-provided by Railway)

✅ These are automatically injected by Railway:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PORT` - Application port

**No action needed** - Railway handles these.

---

### 4. Optional Services

#### Email/Notifications (for alerts)
- [ ] **SendGrid**: https://sendgrid.com/
  - Free tier: 100 emails/day
  - Variable: `SENDGRID_API_KEY`

- [ ] **Mailgun**: https://www.mailgun.com/
  - Free tier: 5,000 emails/month
  - Variable: `MAILGUN_API_KEY`

#### Analytics/Monitoring
- [ ] **Sentry** (error tracking): https://sentry.io/
  - Free tier: 5K errors/month
  - Variable: `SENTRY_DSN`

- [ ] **LogDNA/Mezmo** (logging): https://www.mezmo.com/
  - Variable: `LOGDNA_INGESTION_KEY`

---

## 📝 Current Implementation Status

### What's Currently in `.env.template`:

```bash
# Already defined (need values):
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production

# Placeholders for external services:
# WEATHER_API_KEY=
# FINANCIAL_DATA_API_KEY=
```

### What the Code Expects:

Looking at the generated implementations:

**CA-003-01 (Forecasting)**:
- Currently self-contained (ARIMA, Prophet, LSTM, XGBoost)
- No external API keys required for core functionality
- Prophet may need `cmdstanpy` installation (already in requirements.txt)

**CA-002-07 (Explanations)**:
- Uses internal NLG templates
- No external API keys required

**CA-002 (Correlations)**:
- Depends on your data sources
- If using live data, you'll need API keys for those sources

---

## 🎯 Minimum Viable Deployment

### For testing/MVP (can deploy immediately):

**Required:**
```bash
SECRET_KEY="<generate with secrets module>"
JWT_SECRET_KEY="<generate with secrets module>"
ENCRYPTION_KEY="<generate with Fernet>"
```

**Optional (for now):**
- External data API keys - can add later when you connect real data sources

### For production with live data:

**Add based on data sources:**
- Weather data → OpenWeatherMap or WeatherAPI.com key
- Financial data → Alpha Vantage or Polygon.io key
- Social trends → Twitter API or Google Trends (no key)

---

## 🔧 Setup Instructions

### Step 1: Generate Security Keys

Create a Python script to generate all keys at once:

```python
# generate_keys.py
import secrets
from cryptography.fernet import Fernet

print("=== Generated Security Keys ===\n")
print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
print("\n⚠️  Save these securely! Never commit to Git!")
```

Run it:
```bash
cd /workspaces/control_tower/cloned_repos/business_ventures
python generate_keys.py
```

### Step 2: Save to .env (Local Testing)

```bash
# Create .env from template
cp .env.template .env

# Edit .env and paste your generated keys
nano .env
```

### Step 3: Set in Railway (Production)

```bash
# After railway login
railway variables set SECRET_KEY="<your-generated-secret>"
railway variables set JWT_SECRET_KEY="<your-generated-jwt-secret>"
railway variables set ENCRYPTION_KEY="<your-generated-encryption-key>"
```

### Step 4: Add External API Keys (As Needed)

When you're ready to connect real data sources:

```bash
# Example for weather data
railway variables set WEATHER_API_KEY="<your-openweather-key>"

# Example for financial data
railway variables set FINANCIAL_DATA_API_KEY="<your-alphavantage-key>"
```

---

## 🚨 Security Best Practices

### DO:
- ✅ Generate unique keys for each environment (dev, staging, prod)
- ✅ Store keys in password manager (1Password, LastPass, etc.)
- ✅ Rotate keys periodically (every 90 days)
- ✅ Use Railway's secret variables (encrypted at rest)
- ✅ Keep `.env` in `.gitignore`

### DON'T:
- ❌ Commit keys to Git (even private repos)
- ❌ Share keys in Slack/email
- ❌ Use the same keys across environments
- ❌ Hardcode keys in source code
- ❌ Use simple/guessable keys

---

## 📋 Quick Reference

| Key | Purpose | How to Generate | Where to Set |
|-----|---------|-----------------|--------------|
| SECRET_KEY | General app encryption | `secrets.token_urlsafe(32)` | Railway vars |
| JWT_SECRET_KEY | JWT token signing | `secrets.token_urlsafe(32)` | Railway vars |
| ENCRYPTION_KEY | Fernet encryption | `Fernet.generate_key()` | Railway vars |
| DATABASE_URL | PostgreSQL | Auto by Railway | Auto-injected |
| REDIS_URL | Redis cache | Auto by Railway | Auto-injected |
| WEATHER_API_KEY | Weather data | Sign up OpenWeatherMap | Railway vars |
| FINANCIAL_DATA_API_KEY | Financial data | Sign up Alpha Vantage | Railway vars |

---

## ✅ Deployment Checklist

Before deploying:

- [ ] Generate SECRET_KEY
- [ ] Generate JWT_SECRET_KEY  
- [ ] Generate ENCRYPTION_KEY
- [ ] Test keys work locally with `.env` file
- [ ] Set keys in Railway variables
- [ ] Add `.env` to `.gitignore`
- [ ] Document where keys are stored (password manager)
- [ ] (Optional) Sign up for external data API keys
- [ ] (Optional) Set external API keys in Railway

After deploying:

- [ ] Verify environment variables are set: `railway variables`
- [ ] Test health endpoint
- [ ] Check logs for any key-related errors
- [ ] Rotate keys if any were exposed

---

**Next Steps**: Run `python generate_keys.py` and save the output securely!
