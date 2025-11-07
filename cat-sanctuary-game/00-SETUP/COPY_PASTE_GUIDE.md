# Copy-Paste Guide for Roblox Studio

## ⚠️ IMPORTANT: Follow This Order Exactly

The files must be copied in this specific order because later modules depend on earlier ones.

## 📋 Roblox Studio Setup

### Create These Folders First:

1. In **ReplicatedStorage**:
   - Right-click → Insert Object → Folder
   - Name it: `Shared`

2. In **ServerScriptService**:
   - Right-click → Insert Object → Folder
   - Name it: `CatSanctuary`
   - Inside CatSanctuary, create folder: `MiniGames`

3. In **StarterPlayer/StarterPlayerScripts**:
   - Right-click → Insert Object → Folder
   - Name it: `CatSanctuary`
   - Inside, create folders: `Controllers` and `UI`

---

## 📥 Copy Order

### Phase 1: Shared Modules (Foundation)
**Location: ReplicatedStorage/Shared/**

| # | File | Type | Purpose |
|---|------|------|---------|
| 1 | Config.lua | ModuleScript | Game settings and constants |
| 2 | Types.lua | ModuleScript | Type definitions for IntelliSense |
| 3 | Utils.lua | ModuleScript | Helper functions |

**How to copy:**
1. In ReplicatedStorage/Shared/, right-click → Insert Object → ModuleScript
2. Rename it to the filename (remove .lua)
3. Open the script, select all (Ctrl+A), paste the code
4. Repeat for each file

---

### Phase 2: Server Systems (Core Logic)
**Location: ServerScriptService/CatSanctuary/**

| # | File | Type | Purpose |
|---|------|------|---------|
| 4 | DataStore.lua | ModuleScript | Save/load player data |
| 5 | CurrencyManager.lua | ModuleScript | Charity money system |
| 6 | CatManager.lua | ModuleScript | Cat spawning and stats |
| 7 | SanctuaryManager.lua | ModuleScript | Building system |
| 8 | MiniGameManager.lua | ModuleScript | Competition orchestration |

**Mini-Games (ServerScriptService/CatSanctuary/MiniGames/):**

| # | File | Type | Purpose |
|---|------|------|---------|
| 9 | RaceGame.lua | ModuleScript | Racing mini-game |
| 10 | AgilityGame.lua | ModuleScript | Obstacle course game |

**Main Server Script:**

| # | File | Type | Purpose |
|---|------|------|---------|
| 11 | MainServer.lua | **Script** | Initializes all systems |

⚠️ **Note:** MainServer.lua is a **Script** (not ModuleScript)!

---

### Phase 3: Client Systems (Player UI)
**Location: StarterPlayer/StarterPlayerScripts/CatSanctuary/**

**Controllers (StarterPlayerScripts/CatSanctuary/Controllers/):**

| # | File | Type | Purpose |
|---|------|------|---------|
| 12 | SanctuaryController.lua | LocalScript | Client building logic |
| 13 | CatController.lua | LocalScript | Cat interaction |
| 14 | MiniGameController.lua | LocalScript | Competition client |

**UI Scripts (StarterPlayerScripts/CatSanctuary/UI/):**

| # | File | Type | Purpose |
|---|------|------|---------|
| 15 | MainUI.lua | LocalScript | HUD and main interface |
| 16 | ShopUI.lua | LocalScript | Purchase interface |

---

## ✅ Testing Each Phase

### After Phase 1 (Shared):
Run this in Command Bar:
```lua
local Config = require(game.ReplicatedStorage.Shared.Config)
print(Config.GAME_NAME)
```
Should print: "Cat Sanctuary"

### After Phase 2 (Server):
Run this test in Command Bar:
```lua
local DataStore = require(game.ServerScriptService.CatSanctuary.DataStore)
print("DataStore loaded successfully")
```

### After Phase 3 (Client):
Join the game as a player and check Output for any errors.

---

## 🐛 Common Issues

**"attempt to index nil" error:**
- You didn't copy the Shared modules first
- Check that ReplicatedStorage/Shared/ exists and has all 3 modules

**"ServerScriptService is not a valid member":**
- You're trying to require a server module from client
- Double-check you're putting files in the correct locations

**Script doesn't run:**
- ModuleScripts don't run automatically - they're required by other scripts
- Only MainServer.lua (Script) and LocalScripts run automatically

---

## 🎮 First Test Play

After copying everything:
1. Press F5 or click Play
2. Check Output window (View → Output)
3. Look for: "Cat Sanctuary Server Initialized"
4. No errors? You're ready to build!

---

## 🔄 Iterative Development

You can now:
1. Edit code in VS Code/Codespaces
2. Copy-paste individual functions to update
3. Test in Studio immediately
4. Commit changes to Git

For advanced workflow, set up Rojo (see ROJO_SETUP.md).
