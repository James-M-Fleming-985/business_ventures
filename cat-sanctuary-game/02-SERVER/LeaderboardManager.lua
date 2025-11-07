--[[
	LeaderboardManager.lua
	Global and friend leaderboards
	
	COPY TO: ServerScriptService/CatSanctuary/LeaderboardManager (ModuleScript)
	COPY ORDER: #17 (Add after TrophyManager)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local LeaderboardManager = {}
LeaderboardManager.__index = LeaderboardManager

-- Cached leaderboard data
local leaderboardCache = {
	Trophies = {},
	TotalCurrency = {},
	CatsRescued = {},
	GamesWon = {},
	LastUpdate = 0
}

-- Remote events
local RemoteEvents = {
	GetLeaderboard = nil,
	GetPlayerRank = nil
}

--[=[
	Initialize leaderboard manager
	@param dataStore DataStore module
]=]
function LeaderboardManager:Initialize(dataStore)
	self.DataStore = dataStore
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "LeaderboardRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.GetLeaderboard = Instance.new("RemoteFunction")
	RemoteEvents.GetLeaderboard.Name = "GetLeaderboard"
	RemoteEvents.GetLeaderboard.Parent = remoteFolder
	
	RemoteEvents.GetPlayerRank = Instance.new("RemoteFunction")
	RemoteEvents.GetPlayerRank.Name = "GetPlayerRank"
	RemoteEvents.GetPlayerRank.Parent = remoteFolder
	
	-- Handle remote requests
	RemoteEvents.GetLeaderboard.OnServerInvoke = function(player, category, friendsOnly)
		return self:GetLeaderboardData(category, friendsOnly, player)
	end
	
	RemoteEvents.GetPlayerRank.OnServerInvoke = function(player, category)
		return self:GetPlayerRank(player, category)
	end
	
	-- Start update loop
	task.spawn(function()
		self:UpdateLoop()
	end)
	
	Utils.DebugPrint("LeaderboardManager initialized", "Leaderboard")
end

--[=[
	Update leaderboards periodically
]=]
function LeaderboardManager:UpdateLoop()
	while true do
		task.wait(Config.LEADERBOARDS.UpdateInterval)
		self:UpdateLeaderboards()
	end
end

--[=[
	Update all leaderboard caches
]=]
function LeaderboardManager:UpdateLeaderboards()
	-- Collect data from all online players
	local playerData = {}
	
	for _, player in ipairs(Players:GetPlayers()) do
		local data = self.DataStore:GetCachedData(player)
		if data then
			table.insert(playerData, {
				UserId = player.UserId,
				DisplayName = player.DisplayName,
				Trophies = data.Trophies or 0,
				TotalCurrency = data.Statistics.TotalEarned or 0,
				CatsRescued = data.Statistics.CatsRescued or 0,
				GamesWon = data.Statistics.GamesWon or 0,
			})
		end
	end
	
	-- Sort by each category
	for _, category in ipairs(Config.LEADERBOARDS.Categories) do
		local sorted = Utils.DeepCopy(playerData)
		
		table.sort(sorted, function(a, b)
			return (a[category] or 0) > (b[category] or 0)
		end)
		
		-- Keep only top players
		local topPlayers = {}
		for i = 1, math.min(#sorted, Config.LEADERBOARDS.TopPlayersShown) do
			table.insert(topPlayers, {
				Rank = i,
				UserId = sorted[i].UserId,
				DisplayName = sorted[i].DisplayName,
				Value = sorted[i][category] or 0
			})
		end
		
		leaderboardCache[category] = topPlayers
	end
	
	leaderboardCache.LastUpdate = os.time()
	
	Utils.DebugPrint("Leaderboards updated", "Leaderboard")
end

--[=[
	Get leaderboard data
	@param category string
	@param friendsOnly boolean
	@param player Player?
	@return {table}
]=]
function LeaderboardManager:GetLeaderboardData(category: string, friendsOnly: boolean, player: Player?)
	if not leaderboardCache[category] then
		return {}
	end
	
	local data = leaderboardCache[category]
	
	-- Filter to friends only
	if friendsOnly and player then
		local friendData = {}
		
		for _, entry in ipairs(data) do
			-- Check if player is friend
			local isFriend = player.UserId == entry.UserId or self:IsFriend(player, entry.UserId)
			
			if isFriend then
				table.insert(friendData, entry)
			end
			
			-- Limit to configured amount
			if #friendData >= Config.LEADERBOARDS.FriendsShown then
				break
			end
		end
		
		return friendData
	end
	
	return data
end

--[=[
	Check if userId is friends with player
	@param player Player
	@param userId number
	@return boolean
]=]
function LeaderboardManager:IsFriend(player: Player, userId: number): boolean
	-- In real implementation, use FriendsService
	-- For now, simple check
	local success, isFriend = pcall(function()
		return player:IsFriendsWith(userId)
	end)
	
	return success and isFriend
end

--[=[
	Get player's rank in a category
	@param player Player
	@param category string
	@return number, number -- rank, totalPlayers
]=]
function LeaderboardManager:GetPlayerRank(player: Player, category: string): (number, number)
	if not leaderboardCache[category] then
		return 0, 0
	end
	
	local data = leaderboardCache[category]
	
	-- Find player's position
	for i, entry in ipairs(data) do
		if entry.UserId == player.UserId then
			return i, #data
		end
	end
	
	-- Not in top players
	return 0, #data
end

--[=[
	Get top players for display
	@param category string
	@param count number
	@return {table}
]=]
function LeaderboardManager:GetTopPlayers(category: string, count: number): {any}
	if not leaderboardCache[category] then
		return {}
	end
	
	local data = leaderboardCache[category]
	local topPlayers = {}
	
	for i = 1, math.min(count, #data) do
		table.insert(topPlayers, data[i])
	end
	
	return topPlayers
end

--[=[
	Get player's position near them on leaderboard
	@param player Player
	@param category string
	@param range number -- How many above/below to show
	@return {table}
]=]
function LeaderboardManager:GetNearbyPlayers(player: Player, category: string, range: number): {any}
	if not leaderboardCache[category] then
		return {}
	end
	
	local data = leaderboardCache[category]
	local playerIndex = 0
	
	-- Find player
	for i, entry in ipairs(data) do
		if entry.UserId == player.UserId then
			playerIndex = i
			break
		end
	end
	
	if playerIndex == 0 then
		return {} -- Player not on leaderboard
	end
	
	-- Get range around player
	local startIndex = math.max(1, playerIndex - range)
	local endIndex = math.min(#data, playerIndex + range)
	
	local nearbyPlayers = {}
	for i = startIndex, endIndex do
		table.insert(nearbyPlayers, data[i])
	end
	
	return nearbyPlayers
end

--[=[
	Format leaderboard entry for display
	@param entry table
	@param category string
	@return string
]=]
function LeaderboardManager:FormatEntry(entry: any, category: string): string
	local rank = entry.Rank
	local name = entry.DisplayName
	local value = entry.Value
	
	-- Format value based on category
	local formattedValue = value
	if category == "Trophies" then
		formattedValue = Utils.FormatTrophies(value)
	elseif category == "TotalCurrency" then
		formattedValue = string.format("$%s", Utils.FormatNumber(value))
	else
		formattedValue = Utils.FormatNumber(value)
	end
	
	-- Medal for top 3
	local medal = ""
	if rank == 1 then
		medal = "🥇 "
	elseif rank == 2 then
		medal = "🥈 "
	elseif rank == 3 then
		medal = "🥉 "
	end
	
	return string.format("%s#%d - %s: %s", medal, rank, name, formattedValue)
end

return LeaderboardManager
