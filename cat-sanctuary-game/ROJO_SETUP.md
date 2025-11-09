# 🚀 Rojo Setup Guide - Automated Code Sync

Rojo automatically syncs your Lua code from this folder to Roblox Studio. **No more copy-paste!**

## One-Time Setup (5 minutes)

### Step 1: Install Rojo Plugin in Roblox Studio

1. Open Roblox Studio
2. Go to **Plugins** tab → **Manage Plugins**
3. Search for "**Rojo**" in the toolbox
4. Install the official **Rojo plugin** (by Rojo)
   - Or download from: https://create.roblox.com/marketplace/asset/13916111004/Rojo

### Step 2: Start Rojo Server

In your terminal/Codespaces:

```bash
cd /workspaces/business_ventures/cat-sanctuary-game
./rojo serve
```

You should see:
```
Rojo server listening on port 34872
```

**Keep this terminal running!** Rojo watches for file changes.

### Step 3: Connect from Roblox Studio

1. Open your Cat Sanctuary place in Roblox Studio
2. Click the **Rojo** button in the toolbar (appears after plugin install)
3. Click **Connect** button
4. Rojo will sync all your code automatically! 🎉

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

✅ **No Copy-Paste**: Edit in your favorite editor
✅ **Version Control**: Git tracks all your code changes
✅ **Team Collaboration**: Multiple devs can work on same codebase
✅ **Fast Iteration**: Save file → instantly see in Studio
✅ **Professional Workflow**: Used by all major Roblox studios

## Alternative: Build Place File

If you can't run Rojo server, you can build a `.rbxl` file:

```bash
./rojo build -o CatSanctuary.rbxl
```

This creates a place file you can open directly in Studio (but won't auto-sync changes).

## Resources

- Rojo Docs: https://rojo.space/docs
- Rojo GitHub: https://github.com/rojo-rbx/rojo
- Tutorial Video: https://www.youtube.com/watch?v=xNNuIWFfYqo
