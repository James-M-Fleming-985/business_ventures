--[[
	DataStore.lua
	Handles saving and loading player data
	
	COPY TO: ServerScriptService/CatSanctuary/DataStore (ModuleScript)
	COPY ORDER: #4
]]

local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Types = require(ReplicatedStorage.Shared.Types)
local Utils = require(ReplicatedStorage.Shared.Utils)

local DataStore = {}
DataStore.__index = DataStore

-- DataStore keys
local PLAYER_DATA_STORE = DataStoreService:GetDataStore("PlayerData_v1")
local BACKUP_DATA_STORE = DataStoreService:GetDataStore("PlayerDataBackup_v1")

-- Cache for loaded player data
local playerDataCache = {}

--[=[
	Create default player data structure
	@param player Player
	@return PlayerData
]=]
function DataStore.CreateDefaultData(player: Player)
	local defaultData: Types.PlayerData = {
		UserId = player.UserId,
		Currency = Config.DEBUG.Enabled and Config.DEBUG.StartingCurrency or Config.CURRENCY.StartingAmount,
		Cats = {},
		Sanctuary = {
			Buildings = {},
			Decorations = {},
			Material = "Wood",
			PlotSize = 1
		},
		Achievements = {},
		Statistics = {
			TotalEarned = 0,
			TotalSpent = 0,
			GamesPlayed = 0,
			GamesWon = 0,
			CatsRescued = 0,
			TimePlayed = 0,
			HighestLevel = 0
		},
		Settings = {
			MusicEnabled = true,
			SFXEnabled = true,
			NotificationsEnabled = true
		},
		GamePasses = {},
		LastLogin = os.time(),
		-- Trophy system fields
		Trophies = 0,
		HighestTrophies = 0,
		CurrentLeague = "Rookie",
		WinStreak = 0,
		SeasonData = {
			SeasonId = 1,
			StartTrophies = 0,
			HighestThisSeason = 0
		}
	}
	
	Utils.DebugPrint(string.format("Created default data for %s", player.Name), "DataStore")
	return defaultData
end

--[=[
	Load player data from DataStore
	@param player Player
	@return PlayerData?, string? -- data, errorMessage
]=]
function DataStore:LoadData(player: Player)
	local key = "Player_" .. player.UserId
	
	-- Try to load from main DataStore
	local success, result = pcall(function()
		return PLAYER_DATA_STORE:GetAsync(key)
	end)
	
	if success and result then
		-- Validate data structure
		local isValid, errorMsg = Utils.ValidatePlayerData(result)
		if isValid then
			result.LastLogin = os.time()
			playerDataCache[player.UserId] = result
			Utils.DebugPrint(string.format("Loaded data for %s", player.Name), "DataStore")
			return result, nil
		else
			warn(string.format("Invalid data structure for %s: %s", player.Name, errorMsg))
			-- Try backup
			return self:LoadFromBackup(player)
		end
	elseif not success then
		warn(string.format("Failed to load data for %s: %s", player.Name, tostring(result)))
		-- Try backup
		return self:LoadFromBackup(player)
	end
	
	-- No existing data, create new
	local defaultData = DataStore.CreateDefaultData(player)
	playerDataCache[player.UserId] = defaultData
	return defaultData, nil
end

--[=[
	Load player data from backup DataStore
	@param player Player
	@return PlayerData?, string?
]=]
function DataStore:LoadFromBackup(player: Player)
	local key = "Player_" .. player.UserId
	
	local success, result = pcall(function()
		return BACKUP_DATA_STORE:GetAsync(key)
	end)
	
	if success and result then
		local isValid, errorMsg = Utils.ValidatePlayerData(result)
		if isValid then
			Utils.DebugPrint(string.format("Loaded backup data for %s", player.Name), "DataStore")
			playerDataCache[player.UserId] = result
			return result, nil
		else
			warn(string.format("Invalid backup data for %s: %s", player.Name, errorMsg))
		end
	end
	
	-- If backup fails too, create new data
	warn(string.format("Creating new data for %s (no valid save found)", player.Name))
	local defaultData = DataStore.CreateDefaultData(player)
	playerDataCache[player.UserId] = defaultData
	return defaultData, "No existing data found"
end

--[=[
	Save player data to DataStore
	@param player Player
	@param data PlayerData
	@return boolean, string? -- success, errorMessage
]=]
function DataStore:SaveData(player: Player, data: any)
	if not data then
		return false, "No data to save"
	end
	
	-- Validate before saving
	local isValid, errorMsg = Utils.ValidatePlayerData(data)
	if not isValid then
		return false, "Invalid data structure: " .. errorMsg
	end
	
	local key = "Player_" .. player.UserId
	
	-- Save to main DataStore
	local success, errorMessage = pcall(function()
		PLAYER_DATA_STORE:SetAsync(key, data)
	end)
	
	if success then
		Utils.DebugPrint(string.format("Saved data for %s", player.Name), "DataStore")
		
		-- Also save to backup
		pcall(function()
			BACKUP_DATA_STORE:SetAsync(key, data)
		end)
		
		return true, nil
	else
		warn(string.format("Failed to save data for %s: %s", player.Name, tostring(errorMessage)))
		return false, tostring(errorMessage)
	end
end

--[=[
	Get cached player data
	@param player Player
	@return PlayerData?
]=]
function DataStore:GetCachedData(player: Player)
	return playerDataCache[player.UserId]
end

--[=[
	Update cached player data
	@param player Player
	@param data PlayerData
]=]
function DataStore:UpdateCache(player: Player, data: any)
	playerDataCache[player.UserId] = data
end

--[=[
	Clear player data from cache
	@param player Player
]=]
function DataStore:ClearCache(player: Player)
	playerDataCache[player.UserId] = nil
	Utils.DebugPrint(string.format("Cleared cache for %s", player.Name), "DataStore")
end

--[=[
	Save all online players' data
	@return number -- Number of players saved
]=]
function DataStore:SaveAllPlayers()
	local Players = game:GetService("Players")
	local saved = 0
	
	for _, player in ipairs(Players:GetPlayers()) do
		local data = self:GetCachedData(player)
		if data then
			local success = self:SaveData(player, data)
			if success then
				saved = saved + 1
			end
		end
	end
	
	Utils.DebugPrint(string.format("Auto-saved %d players", saved), "DataStore")
	return saved
end

--[=[
	Increment a statistic for a player
	@param player Player
	@param statName string
	@param amount number
]=]
function DataStore:IncrementStatistic(player: Player, statName: string, amount: number)
	local data = self:GetCachedData(player)
	if data and data.Statistics then
		data.Statistics[statName] = (data.Statistics[statName] or 0) + amount
		self:UpdateCache(player, data)
	end
end

--[=[
	Initialize DataStore system
]=]
function DataStore:Initialize()
	local Players = game:GetService("Players")
	
	-- Create remote events for client access
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "DataRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	local getDataRemote = Instance.new("RemoteFunction")
	getDataRemote.Name = "GetData"
	getDataRemote.Parent = remoteFolder
	
	-- Handle client requests for their data
	getDataRemote.OnServerInvoke = function(player)
		return self:GetCachedData(player)
	end
	
	-- Auto-save interval
	task.spawn(function()
		while true do
			task.wait(Config.PLAYER.SaveInterval)
			self:SaveAllPlayers()
		end
	end)
	
	-- Save on server shutdown
	game:BindToClose(function()
		Utils.DebugPrint("Server shutting down, saving all players...", "DataStore")
		self:SaveAllPlayers()
		task.wait(3) -- Give time for saves to complete
	end)
	
	-- Handle player leaving
	Players.PlayerRemoving:Connect(function(player)
		local data = self:GetCachedData(player)
		if data then
			-- Update play time
			local sessionTime = os.time() - data.LastLogin
			data.Statistics.TimePlayed = data.Statistics.TimePlayed + sessionTime
			
			-- Save data
			local success, errorMsg = self:SaveData(player, data)
			if not success then
				warn(string.format("Failed to save %s on leave: %s", player.Name, errorMsg))
			end
			
			-- Clear cache
			self:ClearCache(player)
		end
	end)
	
	Utils.DebugPrint("DataStore initialized", "DataStore")
end

return DataStore
