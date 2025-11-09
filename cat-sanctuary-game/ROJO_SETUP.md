# 🚀 Rojo Setup Guide - Automated Code Sync

**Rojo** automatically syncs your Lua code from this folder to Roblox Studio. **No more copy-paste!**

## ✅ Rojo is Already Installed!

The `rojo` executable and `default.project.json` configuration are already set up in this folder.

---

## Quick Start (3 Steps)

### Step 1: Install Rojo Plugin (One-Time)

1. Open Roblox Studio
2. View → Toolbox → Search for "**Rojo**"
3. Install the official **Rojo** plugin (by Roblox)
4. Restart Studio

Or install from: <https://create.roblox.com/marketplace/asset/13916111004/Rojo>

### Step 2: Start Rojo Server

**In Codespaces terminal:**

```bash
cd /workspaces/business_ventures/cat-sanctuary-game
./rojo serve
```

You'll see:

```text
Rojo server listening on port 34872
```

**Keep this terminal running!** (Leave it open in background)

### Step 3: Connect from Roblox Studio

1. Create a new Baseplate in Roblox Studio (or open existing place)
2. Look for **Rojo** button in the toolbar (top of Studio)
3. Click **Connect** button
4. Your code syncs automatically! 🎉

**Done!** Now you can edit code in VS Code and see changes instantly in Studio.

---

## Alternative: Build Place File (Offline Method)

If you can't run the live server, build a `.rbxl` file you can open directly:

```bash
cd /workspaces/business_ventures/cat-sanctuary-game
./rojo build -o CatSanctuary.rbxl
```

This creates `CatSanctuary.rbxl` - open it in Studio like any place file.

**Note:** This doesn't auto-sync changes. Rebuild after edits.

---

## Daily Development Workflow

1. **Start Rojo**: `cd cat-sanctuary-game && ./rojo serve`
2. **Open Studio**: Open your Cat Sanctuary place
3. **Connect**: Click Rojo button → Connect
4. **Edit Code**: Make changes in VS Code (any `.lua` file)
5. **Auto-Sync**: Changes appear in Studio instantly!
6. **Test**: Press Play (F5) in Studio

---

## What Gets Synced

**ReplicatedStorage/Shared/**

- Config (ModuleScript)
- Types (ModuleScript)
- Utils (ModuleScript)

**ServerScriptService/MainServer/** (Script)

- All server managers as ModuleScripts:
  - DataStore, CurrencyManager, TrophyManager
  - LeaderboardManager, ProfileServer
  - CatManager, SanctuaryManager, MiniGameManager
  - MiniGames/RaceGame, MiniGames/AgilityGame

**StarterPlayerScripts/**

- Controllers/ (all controller ModuleScripts)
- UI/ (all UI ModuleScripts)

---

## Troubleshooting

### "Connection refused"

- Make sure `./rojo serve` is running
- Check port 34872 is available
- Try restarting: Ctrl+C then `./rojo serve` again

### "Cannot find module"

- Check file paths match `default.project.json`
- Restart Rojo server
- Check that all `.lua` files exist

### Changes not appearing

- Click **"Sync In"** in Rojo plugin manually
- Or disconnect and reconnect
- Check Output window in Studio for errors

### Plugin not showing

- Restart Roblox Studio after installing
- Check Plugins tab → Click Rojo icon
- Reinstall plugin if needed

### Working in Codespaces (Port Forwarding)

If running Rojo in Codespaces with Studio on your desktop:

1. Start Rojo: `./rojo serve`
2. VS Code auto-forwards port 34872 (check "PORTS" tab)
3. Right-click port → "Port Visibility" → "Public"
4. Copy the forwarded URL (e.g., `https://xxxx-34872.app.github.dev`)
5. In Studio Rojo plugin: Paste this URL instead of localhost

---

## Why Use Rojo?

## Daily Workflow

1. **Start Rojo**: `./rojo serve` (in Codespaces terminal)
2. **Open Studio**: Open your place file
3. **Connect**: Click Rojo → Connect
4. **Edit Code**: Edit `.lua` files in VS Code
5. **Auto-Sync**: Changes appear instantly in Studio!

## What Gets Synced

✅ **ReplicatedStorage/Shared/**
   - Config.lua, Types.lua, Utils.lua

✅ **ServerScriptService/**
   - MainServer (as Script)
   - Server folder (all managers as ModuleScripts)

✅ **StarterPlayerScripts/**
   - Controllers folder (all controllers)
   - UI folder (all UI modules)

## Testing Changes

1. Edit a `.lua` file in VS Code
2. Save the file (Ctrl+S)
3. Check Studio - code updates automatically!
4. Press Play (F5) to test

## Troubleshooting

**"Connection refused"**
- Make sure `./rojo serve` is running
- Check if port 34872 is open

**"Cannot find module"**
- Check `default.project.json` paths match your file structure
- Restart Rojo server: Ctrl+C then `./rojo serve` again

**Changes not appearing**
- Click "Sync In" in Rojo plugin
- Or disconnect and reconnect

**Plugin not showing**
- Restart Roblox Studio after installing plugin
- Check Plugins tab for Rojo button

## Advanced: Port Forwarding (Codespaces → Desktop)

If you're running Rojo in Codespaces and Studio on your desktop:

1. Codespaces will auto-forward port 34872
2. Look for "PORTS" tab in VS Code (bottom panel)
3. Right-click port 34872 → "Port Visibility" → "Public"
4. Copy the forwarded URL (looks like: `https://xxxx-34872.app.github.dev`)
5. In Studio Rojo plugin: Enter this URL instead of localhost

## Why Use Rojo?

- ✅ **No Copy-Paste**: Edit in VS Code with all your favorite extensions
- ✅ **Version Control**: Git tracks every code change
- ✅ **Team Collaboration**: Multiple devs work on same codebase
- ✅ **Fast Iteration**: Save → instantly see in Studio
- ✅ **Professional**: Used by every major Roblox game studio
- ✅ **IntelliSense**: Better code completion than Studio editor

---

## Resources

- [Rojo Documentation](https://rojo.space/docs)
- [Rojo GitHub](https://github.com/rojo-rbx/rojo)
- [Video Tutorial](https://www.youtube.com/watch?v=xNNuIWFfYqo)

---

## File Structure Reference

```text
cat-sanctuary-game/
├── default.project.json    ← Rojo configuration
├── rojo                     ← Rojo executable
├── 01-SHARED/              → ReplicatedStorage/Shared/
│   ├── Config.lua
│   ├── Types.lua
│   └── Utils.lua
├── 02-SERVER/              → ServerScriptService/MainServer/
│   ├── init.server.lua     (Main server script)
│   ├── DataStore.lua
│   ├── CurrencyManager.lua
│   └── ... (all other managers)
└── 03-CLIENT/              → StarterPlayerScripts/
    ├── Controllers/
    └── UI/
```

The `init.server.lua` file becomes the Script that runs, and all other `.lua` files become ModuleScripts.

