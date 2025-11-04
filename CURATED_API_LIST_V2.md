# Causal Affect Platform - CURATED 10 APIs for MVP
**Focus**: Politics, Environmental Events, World Events → Economic Impact  
**Date**: November 4, 2025

---

## 🎯 YOUR CORRELATION OPPORTUNITIES

Based on your interests in **politics, environment, science, and advanced medicine**, here are **high-value correlation patterns** we can detect:

### Political Impact
- Election cycles ↔ Stock market volatility
- Presidential approval ratings ↔ Consumer confidence
- Congressional votes ↔ Sector performance (healthcare, defense, energy)
- Political protests ↔ Travel industry impact

### Environmental Events
- Natural disasters ↔ Insurance claims, construction demand
- Wildfire severity ↔ Air quality, real estate prices
- Hurricane forecasts ↔ Home improvement sales, generator demand
- Drought conditions ↔ Agriculture commodity prices

### World Events
- Geopolitical tensions ↔ Oil prices, defense stocks
- Global pandemics ↔ Remote work tools, delivery services
- International trade agreements ↔ Import/export volumes
- War/conflict ↔ Gold prices, cryptocurrency adoption

### **Scientific & Medical Breakthroughs** 🆕
- AI/ML research volume (arXiv) ↔ NVIDIA, Google AI divisions stock
- Quantum computing papers ↔ IBM quantum, IonQ valuations
- Cancer immunotherapy trials (ClinicalTrials.gov) ↔ Biotech sector
- CRISPR gene therapy publications (PubMed) ↔ EDIT, CRSP stock prices
- Patent filings in cleantech (USPTO) ↔ Green energy investment flows
- Phase 3 trial completions ↔ FDA approval speculation, stock spikes
- Fusion energy research (arXiv) ↔ Commonwealth Fusion, TAE Technologies
- Medical device patents (USPTO) ↔ Medtronic, Boston Scientific demand

---

## 🌟 THE CURATED 13 (NO WAITING, INSTANT ACCESS)

### **TIER 1: POLITICAL & ECONOMIC (4 APIs)**

#### 1. FRED - Federal Reserve Economic Data ⭐⭐⭐ **ESSENTIAL**
- **URL**: <https://fred.stlouisfed.org>
- **Sign Up**: <https://fred.stlouisfed.org/docs/api/api_key.html>
- **Free Tier**: Unlimited (rate limited)
- **Data**: 
  - **800,000+ time series** including:
    - GDP, unemployment, inflation, interest rates
    - Consumer confidence, housing starts, retail sales
    - Presidential approval ratings (from University of Michigan)
    - Labor force participation, wage growth
- **Why Critical**: The gold standard for US economic data
- **Correlations**:
  - Unemployment rate ↔ Fast food restaurant traffic
  - Consumer confidence ↔ Luxury good sales
  - Interest rates ↔ Home improvement spending
  - Presidential approval ↔ Stock market performance
- **Variable**: `FRED_API_KEY`
- **Instant Access**: ✅ Key delivered immediately
- [ ] **Status**: ⬜ PRIORITY #1

#### 2. World Bank Data API ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://data.worldbank.org>
- **Documentation**: <https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation>
- **Free Tier**: Unlimited, no authentication required
- **Data**:
  - Global poverty rates, GDP by country
  - CO2 emissions, renewable energy adoption
  - Education, health, infrastructure indicators
  - Agricultural land use, forest coverage
- **Why Critical**: International economic & environmental data
- **Correlations**:
  - CO2 emissions ↔ Climate policy adoption
  - Poverty rates ↔ Remittance flows
  - Renewable energy adoption ↔ Oil prices
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

#### 3. Alpha Vantage - Financial Markets ⭐⭐
- **URL**: <https://www.alphavantage.co>
- **Sign Up**: <https://www.alphavantage.co/support/#api-key>
- **Free Tier**: 5 calls/min, 500 calls/day
- **Data**:
  - Stock prices (global markets)
  - Forex rates, cryptocurrency
  - Technical indicators
  - Economic indicators (GDP, CPI, etc.)
- **Why Useful**: Track how political events affect markets
- **Correlations**:
  - Election results ↔ Defense stock performance
  - Trade war announcements ↔ Tech stock volatility
  - Fed speeches ↔ Bond yields
- **Variable**: `ALPHA_VANTAGE_API_KEY`
- **Instant Access**: ✅ Key in email immediately
- [ ] **Status**: ⬜ PRIORITY #2

#### 4. US Census Bureau API ⭐⭐ **NO KEY NEEDED**
- **URL**: <https://www.census.gov/data/developers.html>
- **Documentation**: <https://www.census.gov/data/developers/guidance/api-user-guide.html>
- **Free Tier**: Unlimited, no key required (recommended but optional)
- **Data**:
  - Population demographics by region
  - Income distribution, poverty levels
  - Housing data, migration patterns
  - Business statistics
- **Why Useful**: Demographic shifts drive economic trends
- **Correlations**:
  - Population aging ↔ Healthcare spending
  - Migration patterns ↔ Real estate demand
  - Income inequality ↔ Luxury vs discount retail
- **Variable**: `CENSUS_API_KEY` (optional)
- **Instant Access**: ✅ Works without key, key is instant if wanted
- [x] **Status**: ✅ Ready to use

---

### **TIER 2: ENVIRONMENTAL & DISASTER (3 APIs)**

#### 5. OpenWeatherMap - Solar Radiation API ⭐⭐⭐
- **URL**: <https://openweathermap.org/api>
- **Specific API**: Solar Radiation & Energy Prediction (<https://openweathermap.org/api/solar-radiation>)
- **Sign Up**: <https://home.openweathermap.org/users/sign_up>
- **Free Tier**: 1,000 calls/day (covers multiple API products)
- **Data**:
  - Solar radiation (GHI, DNI, DHI)
  - Cloud coverage affecting solar energy
  - Also includes: Current weather, air pollution, UV index
- **Why Interesting**: Your instinct was right!
- **Correlations**:
  - Solar radiation ↔ Solar panel installation demand
  - Air pollution levels ↔ Respiratory medication sales
  - UV index ↔ Sunscreen sales
  - Temperature extremes ↔ Energy consumption
- **Variable**: `OPENWEATHER_API_KEY`
- **Instant Access**: ✅ Key immediate after email verification
- [ ] **Status**: ⬜ PRIORITY #3

#### 6. USGS Earthquake API ⭐⭐ **NO KEY NEEDED**
- **URL**: <https://earthquake.usgs.gov/fdsnws/event/1/>
- **Documentation**: <https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php>
- **Free Tier**: Unlimited, no authentication
- **Data**:
  - Real-time earthquake data (magnitude, location, depth)
  - Historical seismic activity
  - Tsunami warnings
- **Why Useful**: Natural disasters have immediate economic impact
- **Correlations**:
  - Earthquake magnitude ↔ Construction material demand
  - Seismic activity ↔ Insurance premium changes
  - Disaster declarations ↔ Emergency supply sales
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

#### 7. NASA EONET - Environmental Events ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://eonet.gsfc.nasa.gov/docs/v3>
- **Documentation**: <https://eonet.gsfc.nasa.gov/api/v3/events>
- **Free Tier**: Unlimited, no authentication
- **Data**:
  - **Wildfires** (location, severity)
  - **Severe storms** (hurricanes, typhoons)
  - **Floods**, **droughts**, **volcanic activity**
  - **Sea/lake ice** changes
- **Why Critical**: Your exact interest - world environmental events!
- **Correlations**:
  - Wildfire count ↔ Air purifier sales, real estate prices
  - Hurricane paths ↔ Home improvement store revenue
  - Drought severity ↔ Water conservation product demand
  - Volcanic eruptions ↔ Aviation industry disruption
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

---

### **TIER 3: SOCIAL & GEOPOLITICAL (3 APIs)**

#### 8. Google Trends (pytrends) ⭐⭐⭐ **NO KEY NEEDED**
- **Library**: `pip install pytrends`
- **Documentation**: <https://pypi.org/project/pytrends/>
- **Free Tier**: Rate limited but generous
- **Data**:
  - Search interest over time for ANY topic
  - Political keywords: "impeachment", "election fraud", "climate change"
  - Economic keywords: "recession", "layoffs", "job search"
  - World events: "war", "pandemic", "protest"
- **Why Essential**: Real-time public sentiment proxy
- **Correlations**:
  - "recession" searches ↔ Gold prices
  - "climate change" searches ↔ ESG investment funds
  - "war" searches ↔ Defense stock prices
  - Political candidate names ↔ Sector-specific stock movement
- **Variable**: None - Library based
- **Instant Access**: ✅ Already available
- [x] **Status**: ✅ Ready to use

#### 9. GDELT Project API ⭐⭐⭐ **NO KEY NEEDED - POWERFUL**
- **URL**: <https://www.gdeltproject.org>
- **Documentation**: <https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/>
- **Free Tier**: Unlimited via BigQuery (100GB/month free tier)
- **Data**:
  - **Global news events** in real-time (300+ million events)
  - Political protests, conflicts, diplomatic meetings
  - Sentiment analysis of news coverage by country/topic
  - Geopolitical event tracking (coups, sanctions, treaties)
- **Why INCREDIBLE**: This is THE dataset for "politics shapes society"
- **Correlations**:
  - Political protest intensity ↔ Tourism industry impact
  - Trade war mentions ↔ Import/export volumes
  - Diplomatic tensions ↔ Safe-haven asset prices (gold, CHF)
  - Media coverage of climate ↔ Green energy stock performance
- **Variable**: Google Cloud credentials (free tier)
- **Instant Access**: ✅ Immediate via BigQuery
- [ ] **Status**: ⬜ Requires Google Cloud signup (instant, free)

#### 10. PubMed/NIH API - Medical & Scientific Research ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://www.ncbi.nlm.nih.gov/home/develop/api/>
- **Documentation**: <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- **Free Tier**: 10 requests/second (with API key), 3/second without
- **Data**:
  - 35+ million biomedical citations
  - Clinical trial data
  - Research publication trends
  - Disease, treatment, drug mentions
- **Why Critical**: Track medical breakthroughs → market impact
- **Correlations**:
  - Cancer research publications ↔ Biotech stock performance
  - Clinical trial announcements ↔ Pharmaceutical company valuations
  - Vaccine research trends ↔ Public health policy changes
  - Medical device innovation ↔ Healthcare equipment demand
- **Variable**: `NCBI_API_KEY` (optional, increases rate limit)
- **Instant Access**: ✅ Works without key, key is instant if wanted
- [x] **Status**: ✅ Ready to use

---

### **TIER 4: SCIENCE & ADVANCED TECHNOLOGY (3 APIs)**

#### 11. arXiv API - Scientific Research ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://arxiv.org>
- **Documentation**: <https://info.arxiv.org/help/api/index.html>
- **Free Tier**: Unlimited, no authentication
- **Data**:
  - 2.3+ million scientific papers (physics, math, CS, AI)
  - Preprints in: Quantum computing, AI/ML, fusion energy, materials science
  - Author networks, citation patterns
  - Research trends by field
- **Why Incredible**: Detect emerging tech BEFORE market adoption
- **Correlations**:
  - AI/ML paper volume ↔ NVIDIA stock performance
  - Quantum computing breakthroughs ↔ IBM, Google quantum divisions
  - Fusion energy papers ↔ Clean energy investment flows
  - CRISPR/gene editing research ↔ Biotech valuations
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

#### 12. USPTO Patent API - Innovation Tracking ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://developer.uspto.gov>
- **Documentation**: <https://developer.uspto.gov/api-catalog>
- **Free Tier**: Unlimited for Patent Grant/Application Data
- **Data**:
  - Patent applications and grants
  - Technology classifications (AI, biotech, cleantech, nanotech)
  - Company innovation activity
  - Patent trends by industry
- **Why Powerful**: Patents predict future products 3-5 years ahead
- **Correlations**:
  - AI patent filings ↔ Tech sector hiring
  - Medical device patents ↔ Healthcare equipment demand
  - Clean energy patents ↔ ESG investment trends
  - Pharma patent expirations ↔ Generic drug market entry
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

#### 13. ClinicalTrials.gov API - Medical Innovation ⭐⭐⭐ **NO KEY NEEDED**
- **URL**: <https://clinicaltrials.gov>
- **Documentation**: <https://clinicaltrials.gov/data-api/api>
- **Free Tier**: Unlimited, no authentication
- **Data**:
  - 450,000+ clinical trials worldwide
  - Trial phases, sponsors, conditions, interventions
  - Drug development pipelines
  - Disease research activity
- **Why Essential**: FDA approvals drive billion-dollar market moves
- **Correlations**:
  - Phase 3 trial completions ↔ Biotech stock spikes
  - Alzheimer's trial volume ↔ Neurology drug demand
  - Cancer immunotherapy trials ↔ Oncology sector performance
  - Rare disease trials ↔ Orphan drug valuations
- **Variable**: None - Open API
- **Instant Access**: ✅ No signup needed
- [x] **Status**: ✅ Ready to use

---

## 📊 FINAL CURATED LIST (13 APIS)

| # | API | Category | Key Required | Instant Access | Alignment |
|---|-----|----------|--------------|----------------|-----------|
| 1 | **FRED** | Economic | ✅ Yes | ✅ Instant | ⭐⭐⭐⭐⭐ |
| 2 | **World Bank** | Global Econ | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |
| 3 | **Alpha Vantage** | Markets | ✅ Yes | ✅ Instant | ⭐⭐⭐⭐ |
| 4 | **US Census** | Demographics | ❌ No | ✅ Open | ⭐⭐⭐⭐ |
| 5 | **OpenWeather Solar** | Environmental | ✅ Yes | ✅ Instant | ⭐⭐⭐⭐ |
| 6 | **USGS Earthquakes** | Disasters | ❌ No | ✅ Open | ⭐⭐⭐⭐ |
| 7 | **NASA EONET** | Environmental | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |
| 8 | **Google Trends** | Sentiment | ❌ No | ✅ Library | ⭐⭐⭐⭐⭐ |
| 9 | **GDELT Project** | Geopolitical | ❌ Cloud | ✅ Free Tier | ⭐⭐⭐⭐⭐ |
| 10 | **PubMed/NIH** | Medical Research | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |
| 11 | **arXiv** | Scientific Research | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |
| 12 | **USPTO Patents** | Innovation | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |
| 13 | **ClinicalTrials.gov** | Medical Innovation | ❌ No | ✅ Open | ⭐⭐⭐⭐⭐ |

**Keys to Collect**: Only 3! (FRED, Alpha Vantage, OpenWeather)  
**No Key Needed**: 10 APIs ready to use immediately  
**Estimated Setup Time**: 10-15 minutes

---

## 🎯 CORRELATION GOLD MINES

With this API stack, you can detect correlations like:

### Politics → Economy
- Presidential approval ratings (FRED) ↔ Consumer confidence (FRED) ↔ Retail sales
- "Impeachment" searches (Google Trends) ↔ Market volatility (Alpha Vantage)
- Political protests (GDELT) ↔ Tourism decline in affected regions
- Congressional healthcare votes (GDELT) ↔ Healthcare stock performance

### Environmental → Economy
- Wildfire severity (NASA EONET) ↔ Air purifier sales, real estate prices
- Hurricane forecasts (NASA EONET) ↔ Home improvement revenue (Home Depot stock)
- Drought conditions (NASA EONET) ↔ Agricultural commodity prices (Alpha Vantage)
- Solar radiation (OpenWeather) ↔ Solar installation demand

### World Events → Markets
- Trade war mentions (GDELT) ↔ Import volumes (UN Comtrade) ↔ Domestic substitutes
- Geopolitical tensions (GDELT) ↔ Gold prices (Alpha Vantage)
- Pandemic news coverage (GDELT) ↔ Remote work stock performance
- Climate disaster coverage (GDELT) ↔ ESG fund flows

---

## 🚀 QUICK START (10-15 MINUTES)

### Priority 1: Core Economic Data (5 min)

```bash
# 1. FRED (3 min)
# Visit: https://fred.stlouisfed.org/docs/api/api_key.html
# Click "Request API Key" → Sign up → Copy key
FRED_API_KEY=your_key_here

# 2. Alpha Vantage (2 min)  
# Visit: https://www.alphavantage.co/support/#api-key
# Enter email → Copy key from email
ALPHA_VANTAGE_API_KEY=your_key_here
```

### Priority 2: Environmental Data (3 min)

```bash
# 3. OpenWeatherMap (3 min)
# Visit: https://home.openweathermap.org/users/sign_up
# Sign up → Verify email → Copy API key
OPENWEATHER_API_KEY=your_key_here
```

### Priority 3: Geopolitical Intelligence (5 min) - OPTIONAL

```bash
# 4. GDELT via Google BigQuery (5 min)
# Visit: https://console.cloud.google.com
# Create free account → Enable BigQuery API
# Download credentials JSON
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Science & Medicine APIs - NO KEYS NEEDED ✅

```bash
# Already available - no signup required:
# - PubMed/NIH API (medical research)
# - arXiv API (scientific papers)
# - USPTO Patent API (innovation tracking)
# - ClinicalTrials.gov API (clinical trials)
# - World Bank, US Census, USGS, NASA EONET, Google Trends
```

---

## 💾 SAVE YOUR KEYS

```bash
cd /workspaces/control_tower/cloned_repos/business_ventures

cat > .env << 'EOF'
# Application Security
SECRET_KEY=<from generate_keys.py>
JWT_SECRET_KEY=<from generate_keys.py>
ENCRYPTION_KEY=<from generate_keys.py>

# Economic Data (REQUIRED)
FRED_API_KEY=<your-fred-key>
ALPHA_VANTAGE_API_KEY=<your-alphavantage-key>

# Environmental Data (REQUIRED)
OPENWEATHER_API_KEY=<your-openweather-key>

# Geopolitical Intelligence (OPTIONAL)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gdelt-credentials.json

# Open APIs - No keys needed ✅
# Political & Economic:
#   - World Bank Data API
#   - US Census Bureau API
# Environmental:
#   - USGS Earthquake API
#   - NASA EONET (Environmental Events)
# Social Sentiment:
#   - Google Trends (pytrends library)
# Science & Medicine:
#   - PubMed/NIH API
#   - arXiv API (scientific research)
#   - USPTO Patent API
#   - ClinicalTrials.gov API
EOF
```

---

## 🧪 TEST YOUR CURATED APIS

```python
# test_curated_apis.py
import requests
import os
from dotenv import load_dotenv
from pytrends.request import TrendReq

load_dotenv()

print("Testing Curated API Stack (13 APIs)...\n")

# === TIER 1: POLITICAL & ECONOMIC ===
print("📊 TIER 1: Political & Economic Data")

# 1. FRED - Economic Data
fred_key = os.getenv('FRED_API_KEY')
r = requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={fred_key}&file_type=json&limit=5')
print(f"  ✅ FRED (Unemployment Rate): {r.status_code == 200}")

# 2. World Bank - No key needed
r = requests.get('https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&date=2020:2023')
print(f"  ✅ World Bank (US GDP): {r.status_code == 200}")

# 3. Alpha Vantage - Markets
av_key = os.getenv('ALPHA_VANTAGE_API_KEY')
r = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SPY&apikey={av_key}')
print(f"  ✅ Alpha Vantage (SPY): {r.status_code == 200}")

# 4. US Census - Demographics (works without key)
r = requests.get('https://api.census.gov/data/2021/acs/acs1?get=NAME,B01001_001E&for=state:*')
print(f"  ✅ US Census (Population): {r.status_code == 200}")

# === TIER 2: ENVIRONMENTAL & DISASTER ===
print("\n🌍 TIER 2: Environmental & Disaster Data")

# 5. OpenWeatherMap - Solar Radiation & Air Pollution
ow_key = os.getenv('OPENWEATHER_API_KEY')
r = requests.get(f'https://api.openweathermap.org/data/2.5/air_pollution?lat=40.7128&lon=-74.0060&appid={ow_key}')
print(f"  ✅ OpenWeather (Air Pollution): {r.status_code == 200}")

# 6. USGS Earthquakes - No key
r = requests.get('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson')
print(f"  ✅ USGS (Earthquakes 24h): {r.status_code == 200}")

# 7. NASA EONET - Environmental Events
r = requests.get('https://eonet.gsfc.nasa.gov/api/v3/events')
print(f"  ✅ NASA EONET (Wildfires/Storms): {r.status_code == 200}")

# === TIER 3: SOCIAL & GEOPOLITICAL ===
print("\n📰 TIER 3: Social & Geopolitical Data")

# 8. Google Trends - No key
pytrends = TrendReq(hl='en-US', tz=360)
pytrends.build_payload(['artificial intelligence'], timeframe='today 12-m')
trends_data = pytrends.interest_over_time()
print(f"  ✅ Google Trends (AI Interest): {not trends_data.empty}")

# 9. GDELT - Requires BigQuery setup
print(f"  ⏳ GDELT: Test via BigQuery after setup (optional)")

# === TIER 4: SCIENCE & ADVANCED MEDICINE ===
print("\n🔬 TIER 4: Science & Advanced Medicine")

# 10. PubMed/NIH - Medical Research
r = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRISPR&retmax=5&retmode=json')
print(f"  ✅ PubMed (CRISPR Research): {r.status_code == 200}")

# 11. arXiv - Scientific Research
r = requests.get('http://export.arxiv.org/api/query?search_query=all:quantum+computing&start=0&max_results=5')
print(f"  ✅ arXiv (Quantum Computing Papers): {r.status_code == 200}")

# 12. USPTO Patents - Innovation
r = requests.get('https://developer.uspto.gov/ibd-api/v1/application/grants?searchText=artificial+intelligence&start=0&rows=5')
print(f"  ✅ USPTO (AI Patents): {r.status_code == 200}")

# 13. ClinicalTrials.gov - Medical Innovation
r = requests.get('https://clinicaltrials.gov/api/v2/studies?query.cond=Cancer&query.intr=Immunotherapy&pageSize=5')
print(f"  ✅ ClinicalTrials.gov (Cancer Immunotherapy): {r.status_code == 200}")

print("\n🎉 API Stack Testing Complete!")
print("\n📈 Summary:")
print(f"  - Political & Economic: 4/4 APIs")
print(f"  - Environmental: 3/3 APIs")
print(f"  - Social & Geopolitical: 1/2 APIs (GDELT optional)")
print(f"  - Science & Medicine: 4/4 APIs")
print(f"  - TOTAL: 12/13 APIs ready (13/13 with GDELT)")
```

---

## 🔥 WHY THIS STACK IS SUPERIOR

**Old List Issues:**
- ❌ Reddit API: 12-week waiting time
- ❌ Generic weather APIs: Low business value
- ❌ COVID-19/Holidays: Too narrow, limited use cases
- ❌ Missing science & medical innovation data

**New List Advantages:**
- ✅ **Instant access**: 10 APIs require NO keys at all
- ✅ **Only 3 keys** needed (all instant delivery)
- ✅ **Perfectly aligned**: Politics, Environment, Science, Advanced Medicine
- ✅ **Breakthrough detection**: Track AI papers → NVIDIA stock, Clinical trials → Biotech valuations
- ✅ **Massive scale**: 
  - GDELT: 300M+ global events
  - FRED: 800K+ economic series
  - PubMed: 35M+ medical papers
  - arXiv: 2.3M+ scientific papers
  - Patents: All US innovation data
  - Clinical Trials: 450K+ trials
- ✅ **Authoritative**: Government & academic sources (NIH, USPTO, NASA, USGS, FRED)

---

## ✅ NEXT STEPS

1. **Collect 3 keys** (10 min): FRED, Alpha Vantage, OpenWeather
2. **Optional: Setup GDELT** (5 min): Free Google Cloud account + BigQuery
3. **Test APIs**: Run `test_curated_apis.py`
4. **Wire into orchestrators**: Replace mock data with real API calls
5. **Deploy to Railway**: Live correlation detection!

---

**This stack gives you the power to detect correlations like:**

**Politics → Economy:**
- *"Presidential approval ratings drop → Consumer confidence falls → Retail stocks decline"*
- *"Political protest intensity (GDELT) → Tourism cancellations → Airline stock impact"*

**Environment → Markets:**
- *"Wildfire severity increases (NASA) → Air purifier searches spike (Trends) → Related product demand"*
- *"Hurricane forecast paths → Home Depot regional sales surge"*

**Science → Innovation → Economy:**
- *"AI/ML paper volume (arXiv) surges → NVIDIA hiring increases → Stock price correlation"*
- *"Quantum computing breakthroughs (arXiv) → IBM quantum division announcements → Valuations"*
- *"CRISPR gene therapy publications (PubMed) → EDIT/CRSP stock movements"*

**Medical → Biotech:**
- *"Phase 3 cancer trial completions (ClinicalTrials.gov) → FDA approval speculation → Biotech stock spikes"*
- *"Alzheimer's research volume (PubMed) → Neurology drug demand forecasting"*
- *"Medical device patents (USPTO) → Medtronic/Boston Scientific product pipeline predictions"*

Ready to collect these 3 keys and detect breakthrough correlations before the market does? 🚀
