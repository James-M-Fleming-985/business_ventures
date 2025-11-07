# Cat Sanctuary Game - Roblox Project

A competitive cat rescue and sanctuary building game where players collect homeless cats, train them in various skills, and compete in mini-games to earn charity money for upgrades.

## 🎮 Game Concept

Players are cat rescuers who:
1. Meet homeless cats and bring them home
2. Build a sanctuary in their garden
3. Train cats with different skills
4. Compete in mini-games against other players
5. Earn charity money based on performance
6. Upgrade cats, buildings, furniture, and materials
7. Progress from basic materials to diamond/emerald structures

## 📁 Project Structure

This project is organized for **copy-paste workflow** into Roblox Studio, in the exact order you need to implement it.

```
cat-sanctuary-game/
├── 00-SETUP/               # Start here - game setup instructions
├── 01-SHARED/              # Copy these FIRST (shared by server & client)
│   ├── Config.lua          # Game configuration
│   ├── Types.lua           # Type definitions
│   └── Utils.lua           # Utility functions
├── 02-SERVER/              # Copy these SECOND (ServerScriptService)
│   ├── DataStore.lua       # Player data persistence
│   ├── CatManager.lua      # Cat spawning and management
│   ├── SanctuaryManager.lua # Building system
│   ├── CurrencyManager.lua # Charity money system
│   ├── MiniGameManager.lua # Competition orchestration
│   └── mini-games/         # Individual mini-game logic
├── 03-CLIENT/              # Copy these THIRD (StarterPlayer/StarterPlayerScripts)
│   ├── Controllers/        # Client-side game controllers
│   └── UI/                 # GUI scripts
├── 04-TESTS/               # TDD test files
└── docs/                   # Design documents

```

## 🚀 Quick Start - Copy-Paste Order

### Step 1: Create Folders in Roblox Studio

In Roblox Studio Explorer:
1. Create `ReplicatedStorage/Shared/` folder
2. Create `ServerScriptService/CatSanctuary/` folder
3. Create `StarterPlayer/StarterPlayerScripts/CatSanctuary/` folder

### Step 2: Copy Files in This Order

**FIRST - Shared Modules (ReplicatedStorage/Shared/):**
1. `01-SHARED/Config.lua` → ModuleScript in ReplicatedStorage/Shared/
2. `01-SHARED/Types.lua` → ModuleScript in ReplicatedStorage/Shared/
3. `01-SHARED/Utils.lua` → ModuleScript in ReplicatedStorage/Shared/

**SECOND - Server Scripts (ServerScriptService/CatSanctuary/):**
4. `02-SERVER/DataStore.lua` → ModuleScript
5. `02-SERVER/CurrencyManager.lua` → ModuleScript
6. `02-SERVER/CatManager.lua` → ModuleScript
7. `02-SERVER/SanctuaryManager.lua` → ModuleScript
8. `02-SERVER/MiniGameManager.lua` → ModuleScript
9. `02-SERVER/mini-games/*.lua` → ModuleScripts in mini-games folder
10. `02-SERVER/MainServer.lua` → Script (starts everything)

**THIRD - Client Scripts (StarterPlayer/StarterPlayerScripts/CatSanctuary/):**
11. `03-CLIENT/Controllers/*.lua` → LocalScripts
12. `03-CLIENT/UI/*.lua` → LocalScripts

### Step 3: Test with TDD

Run tests from `04-TESTS/` to validate each module before integration.

## 🎯 Development Phases

### MVP (Phase 1) - What We're Building First
- [ ] Basic sanctuary plot system
- [ ] 5 cat types with 2-3 skills each
- [ ] 2 mini-games (Race, Agility Course)
- [ ] Simple charity earning system
- [ ] Basic furniture placement
- [ ] Core monetization (game passes)

### Phase 2 - Expansion
- [ ] More cats and skills
- [ ] Competitive matchmaking
- [ ] Leaderboards
- [ ] Trading system
- [ ] Premium materials

### Phase 3 - Polish
- [ ] Seasonal events
- [ ] Rare/legendary cats
- [ ] Clubs and teams
- [ ] Advanced social features

## 💰 Monetization Strategy

### Game Passes (One-time purchase)
- VIP Status - $5 (auto-collect charity, extra cat slots)
- Premium Builder - $3 (exclusive furniture)
- Speed Trainer - $4 (2x training speed)
- Mega Sanctuary - $7 (larger plot size)

### Developer Products (Repeatable)
- Charity Money Packs ($0.99 - $9.99)
- Rare Cat Eggs ($1.99 - $4.99)
- Skill Boosters ($0.49 - $1.99)
- Premium Materials ($2.99 - $7.99)

### Premium Benefits
- 1.5x charity earnings
- Exclusive daily cat
- Special decoration items

## 🧪 Testing Approach (TDD)

Each module has corresponding test files in `04-TESTS/`:
- Write tests first
- Implement functionality
- Run tests to verify
- Refactor with confidence

## 🎨 Art & Assets Needed

### 3D Models (create in Studio or use toolbox)
- Cat models (5-10 types)
- Furniture items (beds, scratching posts, toys)
- Building parts (walls, floors, roofs)
- Mini-game props (obstacles, hoops, puzzles)

### UI Elements
- Sanctuary management screen
- Cat stats panel
- Mini-game interface
- Shop/upgrade menus
- Leaderboards

## 🔧 Technical Requirements

- Roblox Studio (latest version)
- Basic Lua knowledge
- Understanding of RemoteEvents/RemoteFunctions
- DataStore service (for persistence)

## 📝 Notes

- All scripts use modern Lua practices
- Follows Roblox style guide
- Comments explain key logic
- Built for scalability
- Mobile-friendly design considerations

## 🎓 Learning Resources

- [Roblox Developer Hub](https://create.roblox.com/docs)
- [Lua Learning](https://create.roblox.com/docs/tutorials/scripting/basic-scripting/intro-to-scripting)
- [DataStore Guide](https://create.roblox.com/docs/cloud-services/data-stores)

## 👨‍👩‍👧‍👧 Credits

Concept by: Your Daughters (Ages 7 & 9)
Development: Family Project

---

**Ready to build something amazing!** 🐱✨
