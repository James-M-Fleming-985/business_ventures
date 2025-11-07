--[[
	ProfileServer.lua
	Server-side handler for profile viewing
	Provides player data to other players
	
	COPY TO: ServerScriptService/CatSanctuary/ProfileServer (ModuleScript)
	COPY ORDER: #18
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local ProfileServer = {}
ProfileServer.__index = ProfileServer

--[=[
	Initialize profile server
	@param dataStore DataStore module
	@param trophyManager TrophyManager module
	@param leaderboardManager LeaderboardManager module
]=]
function ProfileServer:Initialize(dataStore, trophyManager, leaderboardManager)
	self.DataStore = dataStore
	self.TrophyManager = trophyManager
	self.LeaderboardManager = leaderboardManager
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "ProfileRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	local getPlayerCats = Instance.new("RemoteFunction")
	getPlayerCats.Name = "GetPlayerCats"
	getPlayerCats.Parent = remoteFolder
	
	local getPlayerStats = Instance.new("RemoteFunction")
	getPlayerStats.Name = "GetPlayerStats"
	getPlayerStats.Parent = remoteFolder
	
	local getPlayerTrophyInfo = Instance.new("RemoteFunction")
	getPlayerTrophyInfo.Name = "GetPlayerTrophyInfo"
	getPlayerTrophyInfo.Parent = remoteFolder
	
	-- Handle remote requests
	getPlayerCats.OnServerInvoke = function(player, targetUserId)
		return self:GetPlayerCats(player, targetUserId)
	end
	
	getPlayerStats.OnServerInvoke = function(player, targetUserId)
		return self:GetPlayerStats(player, targetUserId)
	end
	
	getPlayerTrophyInfo.OnServerInvoke = function(player, targetUserId)
		return self:GetPlayerTrophyInfo(player, targetUserId)
	end
	
	Utils.DebugPrint("ProfileServer initialized", "Profile")
end

--[=[
	Get player's cats (public view)
	@param requestingPlayer Player
	@param targetUserId number
	@return {CatData}
]=]
function ProfileServer:GetPlayerCats(requestingPlayer: Player, targetUserId: number)
	-- Find target player
	local targetPlayer = self:GetPlayerByUserId(targetUserId)
	if not targetPlayer then
		return nil
	end
	
	-- Get their data
	local data = self.DataStore:GetCachedData(targetPlayer)
	if not data then
		return nil
	end
	
	-- Return cats (without sensitive info like IDs)
	local publicCats = {}
	for _, cat in ipairs(data.Cats) do
		table.insert(publicCats, {
			Id = cat.Id,
			Name = cat.Name,
			Type = cat.Type,
			Level = cat.Level,
			Stats = Utils.DeepCopy(cat.Stats),
			Friendship = cat.Friendship,
			Skills = Utils.DeepCopy(cat.Skills)
		})
	end
	
	return publicCats
end

--[=[
	Get player's public stats
	@param requestingPlayer Player
	@param targetUserId number
	@return table
]=]
function ProfileServer:GetPlayerStats(requestingPlayer: Player, targetUserId: number)
	local targetPlayer = self:GetPlayerByUserId(targetUserId)
	if not targetPlayer then
		return nil
	end
	
	local data = self.DataStore:GetCachedData(targetPlayer)
	if not data then
		return nil
	end
	
	-- Return public statistics
	return {
		-- Trophy stats
		Trophies = data.Trophies or 0,
		HighestTrophies = data.HighestTrophies or 0,
		CurrentLeague = data.CurrentLeague or "Rookie",
		WinStreak = data.WinStreak or 0,
		
		-- Game stats
		GamesPlayed = data.Statistics.GamesPlayed,
		GamesWon = data.Statistics.GamesWon,
		TimePlayed = data.Statistics.TimePlayed,
		
		-- Collection stats
		CatsRescued = data.Statistics.CatsRescued,
		HighestLevel = data.Statistics.HighestLevel or 0,
		BuildingsCount = #data.Sanctuary.Buildings,
		Material = data.Sanctuary.Material
	}
end

--[=[
	Get player's trophy information
	@param requestingPlayer Player
	@param targetUserId number
	@return table
]=]
function ProfileServer:GetPlayerTrophyInfo(requestingPlayer: Player, targetUserId: number)
	local targetPlayer = self:GetPlayerByUserId(targetUserId)
	if not targetPlayer then
		return nil
	end
	
	local data = self.DataStore:GetCachedData(targetPlayer)
	if not data then
		return nil
	end
	
	-- Get global rank
	local rank, totalPlayers = self.LeaderboardManager:GetPlayerRank(targetPlayer, "Trophies")
	
	return {
		Trophies = data.Trophies or 0,
		HighestTrophies = data.HighestTrophies or 0,
		CurrentLeague = data.CurrentLeague or "Rookie",
		WinStreak = data.WinStreak or 0,
		GlobalRank = rank > 0 and rank or nil,
		TotalPlayers = totalPlayers
	}
end

--[=[
	Get player by UserId
	@param userId number
	@return Player?
]=]
function ProfileServer:GetPlayerByUserId(userId: number): Player?
	for _, player in ipairs(Players:GetPlayers()) do
		if player.UserId == userId then
			return player
		end
	end
	return nil
end

return ProfileServer
