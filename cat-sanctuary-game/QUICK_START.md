# 🚀 Quick Start Guide

## Welcome to Cat Sanctuary!

This guide will get you from code to playable game in under 30 minutes.

## Prerequisites

✅ Roblox Studio installed  
✅ Basic understanding of Roblox Studio interface  
✅ GitHub Codespaces access (optional, for development)

## Step 1: Open Roblox Studio (5 minutes)

1. Open Roblox Studio
2. Click "New" → "Baseplate"
3. Save your place: File → Publish to Roblox → Name it "Cat Sanctuary"

## Step 2: Set Up Folder Structure (2 minutes)

Create these folders in Explorer:

**In ReplicatedStorage:**
- Create folder: `Shared`

**In ServerScriptService:**
- Create folder: `CatSanctuary`
- Inside CatSanctuary, create folder: `MiniGames`

**In StarterPlayer → StarterPlayerScripts:**
- Create folder: `CatSanctuary`
- Inside CatSanctuary, create folders: `Controllers` and `UI`

## Step 3: Copy Files (15 minutes)

Follow the exact order in `00-SETUP/COPY_PASTE_GUIDE.md`:

### Phase 1: Shared Modules (3 files)
Copy from `01-SHARED/` to `ReplicatedStorage/Shared/`:
1. Config.lua (ModuleScript)
2. Types.lua (ModuleScript)
3. Utils.lua (ModuleScript)

### Phase 2: Server Scripts (9 files)
Copy from `02-SERVER/` to `ServerScriptService/CatSanctuary/`:
4. DataStore.lua (ModuleScript)
5. CurrencyManager.lua (ModuleScript)
6. CatManager.lua (ModuleScript)
7. SanctuaryManager.lua (ModuleScript)
8. MiniGameManager.lua (ModuleScript)
9. RaceGame.lua (ModuleScript) → MiniGames folder
10. AgilityGame.lua (ModuleScript) → MiniGames folder
11. **MainServer.lua (Script - NOT ModuleScript!)**

⚠️ **IMPORTANT**: MainServer.lua must be a regular **Script**, not a ModuleScript!

### Phase 3: Client Scripts (4 files)
Copy from `03-CLIENT/`:
12. SanctuaryController.lua (LocalScript) → Controllers folder
13. CatController.lua (LocalScript) → Controllers folder
14. MiniGameController.lua (LocalScript) → Controllers folder
15. MainUI.lua (LocalScript) → UI folder

## Step 4: Test It! (5 minutes)

1. Press **F5** or click **Play**
2. Check the **Output** window (View → Output)
3. You should see:
   ```
   ═══════════════════════════════════════
   🐱 Cat Sanctuary Server Starting...
   ═══════════════════════════════════════
   ✅ Cat Sanctuary Server Ready!
   ```

4. Your character should spawn with:
   - A top bar showing "Cat Sanctuary"
   - Currency display: "💰 Charity: 1000"
   - A menu button on the right
   - Quick action buttons on the side

## Step 5: Try the Game! (5 minutes)

### Test Commands (Debug Mode)
Type these in chat (only works when DEBUG mode is enabled):

- `/givemoney 10000` - Add 10,000 charity
- `/givecat` - Spawn a random cat
- `/givecat bengal` - Spawn a specific cat type
- `/levelup` - Level up your first cat
- `/help` - Show all commands

### Test Gameplay
1. Open the menu (top right button)
2. Click "🐱 My Cats" to see your starter cat
3. Try training a cat (costs charity)
4. Join a mini-game queue
5. Build something in your sanctuary

## Common Issues & Fixes

### "attempt to index nil" errors
❌ Problem: Shared modules not copied first  
✅ Fix: Make sure Config, Types, and Utils are in ReplicatedStorage/Shared/

### "ServerScriptService is not a valid member"
❌ Problem: Trying to access server from client  
✅ Fix: Double-check file locations match the guide

### Nothing happens when you play
❌ Problem: MainServer.lua is a ModuleScript instead of Script  
✅ Fix: Delete it and recreate as a regular Script

### Game is laggy
❌ Problem: Too many studio windows open  
✅ Fix: Close unnecessary tabs, restart Studio

## Next Steps

### Customize Your Game
1. Edit `Config.lua` to change:
   - Starting currency
   - Cat stats and rarities
   - Building costs
   - Game balance

2. Add more cats:
   - Copy existing cat entry in Config.CATS
   - Change Id, Name, Stats, Rarity
   
3. Create new buildings:
   - Add to Config.BUILDINGS
   - Set cost, type, capacity

### Build the World
1. Create spawn location
2. Add terrain (grass, paths)
3. Create sanctuary plots
4. Add mini-game arenas
5. Place NPCs or signs

### Test with Friends
1. Publish your game (File → Publish to Roblox)
2. Set it to Friends or Public
3. Share the link
4. Get feedback!

## Development Workflow

### Using Codespaces (Recommended)
1. Edit code in Codespaces
2. Test and refine
3. Copy-paste updates to Roblox Studio
4. Test in-game
5. Commit changes to Git

### Using Roblox Studio Only
1. Edit scripts directly in Studio
2. Test frequently
3. Use version control (File → Save to File)

## Getting Help

### Check the Documentation
- `README.md` - Project overview
- `COPY_PASTE_GUIDE.md` - Detailed setup
- `GAME_DESIGN_DOCUMENT.md` - Game concept
- `TESTING_GUIDE.md` - How to test

### Debug Tips
1. Check Output window for errors
2. Use `print()` statements liberally
3. Test one system at a time
4. Use debug commands to speed up testing

### Resources
- [Roblox Developer Hub](https://create.roblox.com/docs)
- [Lua Learning](https://create.roblox.com/docs/tutorials/scripting)
- [DataStore Guide](https://create.roblox.com/docs/cloud-services/data-stores)

## Success Checklist

✅ All files copied to correct locations  
✅ Server starts without errors  
✅ UI appears when playing  
✅ Can spawn cats with /givecat  
✅ Currency system works  
✅ No red errors in Output  
✅ Game saves when leaving  

## Ready to Build!

You now have a fully functional game foundation! 

The core systems are complete:
- ✅ Data persistence
- ✅ Currency system
- ✅ Cat collection & training
- ✅ Mini-games
- ✅ Building system
- ✅ UI framework

Now it's time to:
1. Create the visual world
2. Add more content (cats, buildings, games)
3. Polish the UI
4. Balance the progression
5. Test with players
6. Launch!

**Good luck with your game! 🐱✨**
