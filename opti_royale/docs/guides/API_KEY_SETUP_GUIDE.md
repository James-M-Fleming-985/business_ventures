# 🔑 Clash Royale API Key Setup Guide

## Step 1: Get Official API Key

### Registration Process:
1. **Visit**: [https://developer.clashroyale.com/](https://developer.clashroyale.com/)
2. **Sign up** with your Supercell ID
3. **Create a new API key** for development
4. **Copy the API key** (keep it secure!)

### API Key Restrictions:
- **Development**: Usually allows requests from your current IP
- **Production**: Will need to whitelist server IPs
- **Rate Limits**: 1,000 requests per hour for development keys

## Step 2: Configure in OptiRoyale

### Environment Setup:
1. Add to your `.env` file:
```bash
CLASH_ROYALE_API_KEY=your_api_key_here
CLASH_ROYALE_API_BASE_URL=https://api.clashroyale.com/v1
```

2. Restart the API server to load the new environment variable

## Step 3: Verification Process

### Automatic Verification:
Once the API key is configured, run:
```bash
cd /workspaces/opti_royale
python scripts/verify-card-data.py
```

### What Gets Verified:
- ✅ **Total Card Count**: Official count vs our database
- ✅ **Card Names**: Exact spelling and IDs
- ✅ **Card Properties**: Types, rarities, costs
- ✅ **Evolution Status**: Which cards can actually evolve
- ✅ **Recent Updates**: Any new cards we're missing

### Expected Results:
```
🎮 Clash Royale Card Data Verification
=====================================

📊 Verification Results:
Sources checked: official, database
Status: verified

📈 Card Counts:
  official: 120 cards
  database: 135 cards (need to remove test cards)

🎯 Recommendations:
  [HIGH] Update database to match official count of 120 cards
  [MEDIUM] Verify evolution status for 34 cards
```

## Step 4: Database Sync

### Automatic Sync Service:
Our card data sync service will:
1. **Fetch** latest card data from official API
2. **Compare** with current database
3. **Detect** any changes or new cards
4. **Update** database automatically
5. **Log** all changes for review

### Manual Verification:
You can also manually check specific endpoints:
```bash
# Get all cards
curl -H "Authorization: Bearer $CLASH_ROYALE_API_KEY" \
     https://api.clashroyale.com/v1/cards

# Count total cards
curl -s -H "Authorization: Bearer $CLASH_ROYALE_API_KEY" \
     https://api.clashroyale.com/v1/cards | jq '.items | length'
```

## Benefits of Official API

### Legitimacy:
- ✅ **Authoritative Source**: Direct from Supercell
- ✅ **Always Current**: Updates automatically with game changes
- ✅ **Legally Compliant**: Using official developer resources
- ✅ **Community Trust**: Verified data builds user confidence

### Features Available:
- **Card Database**: Complete card list with stats
- **Player Data**: Real player profiles and statistics
- **Clan Information**: Clan details and member data
- **Tournament Data**: Official tournament results
- **Balance Updates**: Automatic detection of card changes

## Next Steps

1. **Get your API key** from developer.clashroyale.com
2. **Add it to `.env`** file in the project
3. **Run verification script** to confirm connection
4. **Review results** and update database as needed
5. **Enable auto-sync** for ongoing updates

Once this is set up, we'll have the most accurate and legitimate card database possible! 🎯
