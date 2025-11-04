# Causal Affect Platform - 10 FREE TIER APIs for MVP
**Target**: Identify 10 lucrative correlation opportunities for MVP development  
**Date**: November 4, 2025

---

## 🎯 MVP API COLLECTION CHECKLIST

### **TIER 1: WEATHER & CLIMATE (3 APIs)**

#### 1. OpenWeatherMap ⭐ **PRIORITY #1**
- **URL**: https://openweathermap.org/api
- **Sign Up**: https://home.openweathermap.org/users/sign_up
- **Free Tier**: 1,000 calls/day, 60 calls/minute
- **Data**: Temperature, humidity, precipitation, UV index, wind
- **Use Cases**: 
  - Ice cream sales ↔ Temperature
  - Sunscreen demand ↔ UV index  
  - Umbrella sales ↔ Precipitation
- **Variable**: `WEATHER_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

#### 2. WeatherAPI.com
- **URL**: https://www.weatherapi.com
- **Sign Up**: https://www.weatherapi.com/signup.aspx
- **Free Tier**: 1 million calls/month
- **Data**: Current, forecast, historical weather
- **Use Cases**: Weather-dependent product correlations
- **Variable**: `WEATHERAPI_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

#### 3. Tomorrow.io (Weather)
- **URL**: https://www.tomorrow.io/weather-api/
- **Sign Up**: https://app.tomorrow.io/signup
- **Free Tier**: 500 calls/day
- **Data**: Hyperlocal weather, pollen, air quality
- **Use Cases**: Allergy medication ↔ Pollen count
- **Variable**: `TOMORROW_IO_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

---

### **TIER 2: FINANCIAL & ECONOMIC (3 APIs)**

#### 4. Alpha Vantage ⭐ **PRIORITY #2**
- **URL**: https://www.alphavantage.co
- **Sign Up**: https://www.alphavantage.co/support/#api-key
- **Free Tier**: 5 calls/minute, 500 calls/day
- **Data**: Stock prices, forex, crypto, economic indicators
- **Use Cases**:
  - Gold prices ↔ Market volatility
  - Stock market ↔ Consumer sentiment
  - Crypto ↔ Tech stocks
- **Variable**: `ALPHA_VANTAGE_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

#### 5. FRED (Federal Reserve Economic Data)
- **URL**: https://fred.stlouisfed.org
- **Sign Up**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Free Tier**: Unlimited (with rate limiting)
- **Data**: 500,000+ economic time series (GDP, unemployment, inflation, etc.)
- **Use Cases**:
  - Unemployment rate ↔ Fast food sales
  - Interest rates ↔ Home improvement
  - Consumer confidence ↔ Luxury goods
- **Variable**: `FRED_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

#### 6. Polygon.io
- **URL**: https://polygon.io
- **Sign Up**: https://polygon.io/dashboard/signup
- **Free Tier**: 5 calls/minute
- **Data**: Real-time stock, forex, crypto market data
- **Use Cases**: Market correlation analysis
- **Variable**: `POLYGON_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

---

### **TIER 3: SOCIAL & TRENDS (2 APIs)**

#### 7. Google Trends (pytrends) ⭐ **NO API KEY NEEDED**
- **Library**: `pip install pytrends`
- **Documentation**: https://pypi.org/project/pytrends/
- **Free Tier**: Rate limited but generous
- **Data**: Search interest over time, related queries
- **Use Cases**:
  - "face masks" searches ↔ COVID cases
  - "diet" searches ↔ gym memberships
  - "wedding" searches ↔ engagement ring sales
- **Variable**: None (library-based)
- **Cost**: FREE
- [x] **Status**: ✅ No key needed - already available

#### 8. Reddit API (PRAW)
- **URL**: https://www.reddit.com/dev/api
- **Sign Up**: https://www.reddit.com/prefs/apps
- **Free Tier**: 60 requests/minute
- **Data**: Subreddit posts, comments, sentiment, trending topics
- **Use Cases**:
  - r/wallstreetbets activity ↔ Meme stock prices
  - r/fitness posts ↔ Supplement sales
  - Subreddit growth ↔ Product demand
- **Variables**: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

---

### **TIER 4: ALTERNATIVE DATA (2 APIs)**

#### 9. Holidays API (Abstract API)
- **URL**: https://www.abstractapi.com/holidays-api
- **Sign Up**: https://app.abstractapi.com/users/signup
- **Free Tier**: 1,000 requests/month
- **Data**: Public holidays, observances by country
- **Use Cases**:
  - Holiday dates ↔ Travel bookings
  - Black Friday ↔ E-commerce spikes
  - Valentine's Day ↔ Flower sales
- **Variable**: `ABSTRACT_HOLIDAYS_API_KEY`
- **Cost**: FREE
- [ ] **Status**: ⬜ Need to collect

#### 10. COVID-19 Data (disease.sh)
- **URL**: https://disease.sh
- **Documentation**: https://disease.sh/docs/
- **Free Tier**: Unlimited, no key required
- **Data**: COVID-19 cases, deaths, vaccinations by region
- **Use Cases**:
  - COVID cases ↔ Remote work tools
  - Vaccination rates ↔ Travel demand
  - Case spikes ↔ Home delivery services
- **Variable**: None (open API)
- **Cost**: FREE
- [x] **Status**: ✅ No key needed - already available

---

## 📊 SUMMARY

| # | API | Category | Key Required | Priority | Status |
|---|-----|----------|--------------|----------|---------|
| 1 | OpenWeatherMap | Weather | ✅ Yes | ⭐⭐⭐ | ⬜ |
| 2 | WeatherAPI.com | Weather | ✅ Yes | ⭐⭐ | ⬜ |
| 3 | Tomorrow.io | Weather | ✅ Yes | ⭐⭐ | ⬜ |
| 4 | Alpha Vantage | Financial | ✅ Yes | ⭐⭐⭐ | ⬜ |
| 5 | FRED | Economic | ✅ Yes | ⭐⭐⭐ | ⬜ |
| 6 | Polygon.io | Financial | ✅ Yes | ⭐⭐ | ⬜ |
| 7 | Google Trends | Social | ❌ No | ⭐⭐⭐ | ✅ |
| 8 | Reddit API | Social | ✅ Yes | ⭐⭐ | ⬜ |
| 9 | Holidays API | Alternative | ✅ Yes | ⭐ | ⬜ |
| 10 | COVID-19 Data | Alternative | ❌ No | ⭐ | ✅ |

**Keys to Collect**: 7  
**No Key Needed**: 3 (Google Trends, COVID-19 Data, yfinance)  
**Estimated Time**: 30-45 minutes

---

## 🔑 COLLECTION WORKFLOW

### Step 1: Priority APIs (15 minutes)
Start with these 3 - they cover your main use cases:

1. **OpenWeatherMap** (5 min)
   - Go to: https://home.openweathermap.org/users/sign_up
   - Sign up with email
   - Verify email
   - Copy API key from dashboard
   - Save to: `WEATHER_API_KEY=xxx`

2. **Alpha Vantage** (5 min)
   - Go to: https://www.alphavantage.co/support/#api-key
   - Enter email
   - Copy key from email confirmation
   - Save to: `ALPHA_VANTAGE_API_KEY=xxx`

3. **FRED** (5 min)
   - Go to: https://fred.stlouisfed.org/docs/api/api_key.html
   - Click "Request API Key"
   - Sign up for account
   - Copy key from account page
   - Save to: `FRED_API_KEY=xxx`

### Step 2: Secondary APIs (15 minutes)
Add these for broader coverage:

4. **WeatherAPI.com** (3 min)
5. **Tomorrow.io** (3 min)  
6. **Polygon.io** (3 min)
7. **Reddit API** (6 min - requires app creation)

### Step 3: Optional APIs (10 minutes)
Complete the set:

8. **Holidays API** (5 min)
9. Google Trends - Already available ✅
10. COVID-19 Data - Already available ✅

---

## 💾 SAVE YOUR KEYS

After collecting, create `.env` file:

```bash
cd /workspaces/control_tower/cloned_repos/business_ventures

# Create .env file
cat > .env << 'EOF'
# Application Security
SECRET_KEY=<from generate_keys.py>
JWT_SECRET_KEY=<from generate_keys.py>
ENCRYPTION_KEY=<from generate_keys.py>

# Weather APIs
WEATHER_API_KEY=<your-openweathermap-key>
WEATHERAPI_KEY=<your-weatherapi-key>
TOMORROW_IO_API_KEY=<your-tomorrow-io-key>

# Financial APIs
ALPHA_VANTAGE_API_KEY=<your-alphavantage-key>
FRED_API_KEY=<your-fred-key>
POLYGON_API_KEY=<your-polygon-key>

# Social APIs
REDDIT_CLIENT_ID=<your-reddit-client-id>
REDDIT_CLIENT_SECRET=<your-reddit-secret>

# Alternative Data APIs
ABSTRACT_HOLIDAYS_API_KEY=<your-abstract-api-key>

# Google Trends & COVID-19 - No keys needed (library-based)
EOF
```

Then set in Railway:
```bash
railway variables set WEATHER_API_KEY="xxx"
railway variables set ALPHA_VANTAGE_API_KEY="xxx"
# ... etc for all keys
```

---

## 🧪 TEST YOUR KEYS

After collecting, test each API:

```python
# test_apis.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Test OpenWeatherMap
weather_key = os.getenv('WEATHER_API_KEY')
response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q=London&appid={weather_key}')
print(f"OpenWeatherMap: {'✅' if response.status_code == 200 else '❌'}")

# Test Alpha Vantage  
av_key = os.getenv('ALPHA_VANTAGE_API_KEY')
response = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={av_key}')
print(f"Alpha Vantage: {'✅' if response.status_code == 200 else '❌'}")

# Test FRED
fred_key = os.getenv('FRED_API_KEY')
response = requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id=GNPCA&api_key={fred_key}&file_type=json')
print(f"FRED: {'✅' if response.status_code == 200 else '❌'}")

# ... test others
```

---

## ✅ COMPLETION CHECKLIST

- [ ] Collected all 7 required API keys
- [ ] Saved keys to local `.env` file
- [ ] Tested each API with simple request
- [ ] Set keys in Railway variables
- [ ] Added to password manager (1Password, LastPass, etc.)
- [ ] Documented which keys are for dev vs production
- [ ] Ready to proceed with deployment

---

## 📞 SUPPORT LINKS

**If you have issues:**
- OpenWeatherMap: https://openweathermap.org/faq
- Alpha Vantage: https://www.alphavantage.co/support/
- FRED: https://fred.stlouisfed.org/docs/api/
- Reddit API: https://www.reddit.com/dev/api/
- Polygon.io: https://polygon.io/docs/

---

**Next Step**: Once you have these keys, we can proceed with wiring them into the feature orchestrators and testing locally before Railway deployment!
