--[[
	MainServer.lua
	Main server initialization script
	
	COPY TO: ServerScriptService/CatSanctuary/MainServer (Script - NOT ModuleScript!)
	COPY ORDER: #11
	
	⚠️ IMPORTANT: This must be a Script, not a ModuleScript!
]]

local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

-- Wait for shared modules to load
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Utils = require(Shared.Utils)

-- Load server modules
local CatSanctuary = ServerScriptService:WaitForChild("CatSanctuary")
local DataStore = require(CatSanctuary.DataStore)
local CurrencyManager = require(CatSanctuary.CurrencyManager)
local CatManager = require(CatSanctuary.CatManager)
local SanctuaryManager = require(CatSanctuary.SanctuaryManager)
local TrophyManager = require(CatSanctuary.TrophyManager)
local LeaderboardManager = require(CatSanctuary.LeaderboardManager)
local ProfileServer = require(CatSanctuary.ProfileServer)
local MiniGameManager = require(CatSanctuary.MiniGameManager)
local WorldGenerator = require(CatSanctuary.WorldGenerator)

print("═══════════════════════════════════════")
-- Generate world first
Utils.DebugPrint("Generating world environment...", "Server")
WorldGenerator:GenerateWorld()

print("🐱 Cat Sanctuary Server Starting...")
print("═══════════════════════════════════════")
-- Generate world first
Utils.DebugPrint("Generating world environment...", "Server")
WorldGenerator:GenerateWorld()


-- Initialize systems in order
Utils.DebugPrint("Initializing DataStore...", "Server")
DataStore:Initialize()

Utils.DebugPrint("Initializing CurrencyManager...", "Server")
CurrencyManager:Initialize(DataStore)

Utils.DebugPrint("Initializing TrophyManager...", "Server")
TrophyManager:Initialize(DataStore, CurrencyManager)

Utils.DebugPrint("Initializing LeaderboardManager...", "Server")
LeaderboardManager:Initialize(DataStore)

Utils.DebugPrint("Initializing ProfileServer...", "Server")
ProfileServer:Initialize(DataStore, TrophyManager, LeaderboardManager)

Utils.DebugPrint("Initializing CatManager...", "Server")
CatManager:Initialize(DataStore, CurrencyManager)

Utils.DebugPrint("Initializing SanctuaryManager...", "Server")
SanctuaryManager:Initialize(DataStore, CurrencyManager)

Utils.DebugPrint("Initializing MiniGameManager...", "Server")
MiniGameManager:Initialize(DataStore, CurrencyManager, CatManager, TrophyManager)

-- Handle player joining
Players.PlayerAdded:Connect(function(player)
	print(string.format("🎮 Player joined: %s", player.Name))
	
	-- Load player data
	local data, errorMsg = DataStore:LoadData(player)
	if not data then
		warn(string.format("Failed to load data for %s: %s", player.Name, errorMsg))
		player:Kick("Failed to load your data. Please rejoin.")
		return
	end
	
	-- Create leaderstats folder for display
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	leaderstats.Parent = player
	
	local currency = Instance.new("IntValue")
	currency.Name = "Charity"
	currency.Value = data.Currency
	currency.Parent = leaderstats
	
	local cats = Instance.new("IntValue")
	cats.Name = "Cats"
	cats.Value = #data.Cats
	cats.Parent = leaderstats
	
	-- Update leaderstats when currency changes
	local currencyRemotes = ReplicatedStorage:WaitForChild("CurrencyRemotes")
	local currencyChanged = currencyRemotes:WaitForChild("CurrencyChanged")
	currencyChanged.OnServerEvent:Connect(function(plr, newAmount)
		if plr == player then
			currency.Value = newAmount
		end
	end)
	
	-- Give starter cat if new player
	if #data.Cats == 0 then
		Utils.DebugPrint(string.format("New player %s - giving starter cat", player.Name), "Server")
		task.wait(2) -- Small delay
		
		local starterCat, err = CatManager:SpawnCat(player, "tabby")
		if starterCat then
			cats.Value = 1
			print(string.format("✅ %s received starter cat: %s", player.Name, starterCat.Name))
		else
			warn(string.format("Failed to give starter cat to %s: %s", player.Name, err))
		end
	end
	
	print(string.format("✅ %s loaded with %d charity and %d cats", 
		player.Name, 
		data.Currency, 
		#data.Cats
	))
end)

-- Admin commands (for testing)
local function setupAdminCommands()
	Players.PlayerAdded:Connect(function(player)
		player.Chatted:Connect(function(message)
			-- Only allow in debug mode
			if not Config.DEBUG.Enabled then return end
			
			local args = string.split(message, " ")
			local command = args[1]:lower()
			
			if command == "/givemoney" then
				local amount = tonumber(args[2]) or 10000
				CurrencyManager:AddCurrency(player, amount, "Admin command")
				print(string.format("💰 Gave %s %d charity", player.Name, amount))
				
			elseif command == "/givecat" then
				local catType = args[2] or nil
				local cat, err = CatManager:SpawnCat(player, catType)
				if cat then
					print(string.format("🐱 Gave %s a %s", player.Name, cat.Name))
				else
					warn(err)
				end
				
			elseif command == "/levelup" then
				local cats = CatManager:GetAllCats(player)
				if #cats > 0 then
					CatManager:AddExperience(player, cats[1].Id, 10000)
					print(string.format("⬆️ Leveled up %s's first cat", player.Name))
				end
				
			elseif command == "/settrophies" then
				local amount = tonumber(args[2]) or 0
				TrophyManager:SetTrophies(player, amount)
				print(string.format("🏆 Set %s's trophies to %d", player.Name, amount))
				
			elseif command == "/wintrophies" then
				local amount = tonumber(args[2]) or 30
				TrophyManager:AwardTrophies(player, 1, 8) -- Simulate 1st place in 8-player match
				print(string.format("🏆 %s won trophies!", player.Name))
				
			elseif command == "/nextseason" then
				TrophyManager:ProcessSeasonEnd(player)
				print(string.format("🎯 Processed season end for %s", player.Name))
				
			elseif command == "/help" then
				print("Admin Commands:")
				print("/givemoney [amount] - Add charity money")
				print("/givecat [type] - Spawn a cat")
				print("/levelup - Level up first cat")
				print("/settrophies [amount] - Set trophy count")
				print("/wintrophies - Award win trophies (1st place)")
				print("/nextseason - Process season end")
			end
		end)
	end)
end

if Config.DEBUG.Enabled then
	setupAdminCommands()
	print("🔧 Debug mode enabled - admin commands available")
end

print("═══════════════════════════════════════")
-- Generate world first
Utils.DebugPrint("Generating world environment...", "Server")
WorldGenerator:GenerateWorld()

print("✅ Cat Sanctuary Server Ready!")
print(string.format("📊 Game: %s v%s", Config.GAME_NAME, Config.VERSION))
print("═══════════════════════════════════════")
-- Generate world first
Utils.DebugPrint("Generating world environment...", "Server")
WorldGenerator:GenerateWorld()

