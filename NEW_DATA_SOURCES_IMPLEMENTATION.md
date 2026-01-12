# New Data Sources Implementation Plan
**Date**: January 12, 2026  
**Purpose**: Add 6 consumer-focused data sources for MVP exploitation opportunities

## Sources to Implement

### 1. Google Trends (Consumer Search Behavior)
**Library**: `pytrends`  
**API Key**: Not required  
**Frequency**: Weekly → Monthly aggregation  
**Variables**:
- "wedding planning" search volume
- "moving companies" search volume
- "diet plan" search volume
- "home improvement" search volume
- "job search" search volume

**MVP Opportunities**:
- Wedding search spikes ↔ Event planning SaaS
- Moving search increases ↔ Relocation services marketplace
- Diet search trends ↔ Meal prep subscription

### 2. OpenWeather API (Weather Patterns)
**API**: OpenWeather One Call API 3.0  
**API Key**: Required (1,000 calls/day free)  
**Frequency**: Daily → Monthly aggregation  
**Variables**:
- Average temperature (°C)
- Total rainfall (mm)
- UV index (average)
- Air quality index

**MVP Opportunities**:
- High rainfall ↔ Indoor activity booking platform
- UV index ↔ Sunscreen subscription service
- Temperature extremes ↔ HVAC service marketplace

### 3. FRED Economic Data (Economic Indicators)
**API**: Federal Reserve Economic Data  
**API Key**: Required (free, instant)  
**Frequency**: Monthly  
**Variables**:
- Unemployment rate (UNRATE)
- Consumer confidence (UMCSENT)
- Housing starts (HOUST)
- Retail sales (RSXFS)
- Inflation rate (CPIAUCSL)

**MVP Opportunities**:
- Rising unemployment ↔ Job training platform
- Consumer confidence drops ↔ Budget shopping aggregator
- Housing starts ↔ Home services marketplace

### 4. USPTO Patents (US Innovation)
**API**: USPTO Patent Data API  
**API Key**: Not required  
**Frequency**: Monthly aggregation  
**Variables**:
- AI/ML patent applications (monthly count)
- Medical device patents
- Clean energy patents
- Biotech patents

**MVP Opportunities**:
- AI patent surge ↔ AI consulting/training services
- Medical device patents ↔ Healthcare tech marketplace

### 5. UK IPO Patents (UK Innovation) ⭐
**API**: UK Intellectual Property Office  
**API Key**: Not required  
**Frequency**: Monthly aggregation  
**Variables**:
- UK AI/ML patent applications
- UK medical device patents
- UK clean energy patents
- UK fintech patents

**MVP Opportunities**:
- UK fintech patents ↔ Fintech advisory services
- UK clean tech patents ↔ Green tech consulting

### 6. USGS Earthquakes (Disaster Events)
**API**: USGS Earthquake API  
**API Key**: Not required  
**Frequency**: Monthly aggregation  
**Variables**:
- Earthquake count (magnitude > 4.0)
- Average magnitude
- Total seismic energy released

**MVP Opportunities**:
- Earthquake frequency ↔ Emergency preparedness kits
- Seismic activity ↔ Home retrofit services

## Implementation Steps

1. **Install required libraries**:
   ```bash
   pip install pytrends fredapi
   ```

2. **Add environment variables**:
   ```
   OPENWEATHER_API_KEY=your_key_here
   FRED_API_KEY=your_key_here
   ```

3. **Update data_fetcher.py** with 6 new methods:
   - `fetch_google_trends_monthly(keyword, months=300)`
   - `fetch_openweather_monthly(city, months=300)`
   - `fetch_fred_indicator(indicator_code, months=300)`
   - `fetch_uspto_patents_monthly(category, months=300)`
   - `fetch_ukipo_patents_monthly(category, months=300)`
   - `fetch_usgs_earthquakes_monthly(region, months=300)`

4. **Update data_ingestion_service.py** to ingest new sources

5. **Update database** with new variable metadata

## Expected Outcome

**Current**: 61 variables → 3,721 correlation pairs (mostly finance/academic)  
**After implementation**: ~120 variables → 14,280 correlation pairs (with consumer behavior)

**New correlation examples**:
- "wedding planning" searches ↔ Event venue bookings
- Rainfall ↔ Umbrella sales / Indoor entertainment
- Unemployment ↔ Budget grocery stores
- AI patents ↔ Tech sector job postings
- UK fintech patents ↔ London startup funding
- Earthquake frequency ↔ Insurance claims

This unlocks **actionable MVP opportunities** instead of just trading signals!
