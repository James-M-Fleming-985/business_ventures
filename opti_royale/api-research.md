# Clash Royale API Research

## Official Clash Royale API Endpoints (developer.clashroyale.com)

### Player Data Access:
- `GET /players/{playerTag}` - Player profile data
- `GET /players/{playerTag}/battlelog` - Player's recent battles (25 most recent)
- `GET /players/{playerTag}/upcomingchests` - Upcoming chest cycle

### What Battle Log Contains:
- Battle outcome (win/loss)
- Battle mode (1v1, 2v2, etc.)
- Battle time
- Arena info
- **BOTH players' cards and levels**
- **Crowns won by each player**
- **Battle duration**

### KEY LIMITATION:
- **ONLY shows battles for players who have their profile set to PUBLIC**
- **API requires the player's tag (like #ABC123)**
- **Cannot browse random players or search by name**

## Battle Log Data Structure:
```json
{
  "type": "1v1",
  "battleTime": "20231201T120000.000Z",
  "isLadderTournament": false,
  "arena": {
    "id": 54000015,
    "name": "Arena 15"
  },
  "gameMode": {
    "id": 72000006,
    "name": "Ladder"
  },
  "deckSelection": "collection",
  "team": [
    {
      "tag": "#YOURTAG",
      "name": "YourName",
      "startingTrophies": 5000,
      "trophyChange": 30,
      "crowns": 3,
      "cards": [
        {
          "name": "Knight",
          "id": 26000000,
          "level": 11,
          "maxLevel": 13
        }
        // ... 7 more cards
      ]
    }
  ],
  "opponent": [
    {
      "tag": "#OPPTAG",
      "name": "Opponent",
      "startingTrophies": 4970,
      "trophyChange": -30,
      "crowns": 1,
      "cards": [
        // Opponent's 8 cards with levels
      ]
    }
  ]
}
```

## What This Means for Our Pricing:

### ✅ POSSIBLE (API Advantages):
1. **Auto-import YOUR battle log** - convenience feature
2. **See opponent's deck and levels** from YOUR battles
3. **Historical tracking** of your performance
4. **Opponent analysis** from battles you've already played

### ❌ NOT POSSIBLE (Major Limitations):
1. **Cannot scout random players** unless you know their exact tag
2. **Cannot analyze pro players** unless they're public AND you have their tag
3. **Cannot browse top players** without knowing their tags
4. **Most players keep profiles PRIVATE**

### 🤔 GRAY AREA:
- **Leaderboards API** might provide top player tags
- **Some pro players** do keep profiles public
- **Tournament API** might give access to tournament players

## Revised Pricing Strategy:

### 🆓 Free Tier: Video Upload
- Manual video upload and analysis
- 5 battles per month
- Full 3-window interface

### ⭐ Champion Tier: Battle Log Auto-Import
- **YOUR battle log auto-import** (convenience)
- **Opponent deck analysis** from your battles
- **Historical performance tracking**
- Unlimited analysis

### 👑 Legend Tier: Advanced Features
- **Live match coaching**
- **Deck optimization**
- **Meta analysis** from your battle history
- **Tournament mode analysis**

## Bottom Line:
The "scout any player" feature is **severely limited** by API restrictions. The real value is in **convenience** and **advanced analysis** of your own data.
