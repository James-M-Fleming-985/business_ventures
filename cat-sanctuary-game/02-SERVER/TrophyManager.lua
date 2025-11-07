--[[
	TrophyManager.lua
	Handles trophy/ranking system (like Clash Royale)
	
	COPY TO: ServerScriptService/CatSanctuary/TrophyManager (ModuleScript)
	COPY ORDER: #16 (Add after MiniGameManager)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local TrophyManager = {}
TrophyManager.__index = TrophyManager

-- Remote events
local RemoteEvents = {
	TrophyChanged = nil,
	LeagueChanged = nil,
	WinStreakUpdated = nil
}

--[=[
	Initialize trophy manager
	@param dataStore DataStore module
	@param currencyManager CurrencyManager module
]=]
function TrophyManager:Initialize(dataStore, currencyManager)
	self.DataStore = dataStore
	self.CurrencyManager = currencyManager
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "TrophyRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.TrophyChanged = Instance.new("RemoteEvent")
	RemoteEvents.TrophyChanged.Name = "TrophyChanged"
	RemoteEvents.TrophyChanged.Parent = remoteFolder
	
	RemoteEvents.LeagueChanged = Instance.new("RemoteEvent")
	RemoteEvents.LeagueChanged.Name = "LeagueChanged"
	RemoteEvents.LeagueChanged.Parent = remoteFolder
	
	RemoteEvents.WinStreakUpdated = Instance.new("RemoteEvent")
	RemoteEvents.WinStreakUpdated.Name = "WinStreakUpdated"
	RemoteEvents.WinStreakUpdated.Parent = remoteFolder
	
	Utils.DebugPrint("TrophyManager initialized", "Trophies")
end

--[=[
	Get player's current trophies
	@param player Player
	@return number
]=]
function TrophyManager:GetTrophies(player: Player): number
	local data = self.DataStore:GetCachedData(player)
	return data and data.Trophies or 0
end

--[=[
	Award trophies based on game placement
	@param player Player
	@param place number -- 1st, 2nd, 3rd, etc.
	@param totalPlayers number
	@return number -- Trophy change
]=]
function TrophyManager:AwardTrophies(player: Player, place: number, totalPlayers: number): number
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return 0
	end
	
	-- Calculate trophy change
	local trophyChange = Utils.CalculateTrophyChange(place, totalPlayers)
	
	-- Check for win streak bonus (only on wins)
	if place == 1 then
		data.WinStreak = (data.WinStreak or 0) + 1
		
		-- Award streak bonuses
		for streak, bonus in pairs(Config.TROPHIES.WinStreakBonus) do
			if data.WinStreak == streak then
				trophyChange = trophyChange + bonus
				Utils.DebugPrint(
					string.format("%s earned %d streak bonus! (%d wins)", player.Name, bonus, streak),
					"Trophies"
				)
			end
		end
		
		-- Notify client of win streak
		if RemoteEvents.WinStreakUpdated then
			RemoteEvents.WinStreakUpdated:FireClient(player, data.WinStreak)
		end
	else
		-- Reset win streak on non-1st place
		if data.WinStreak > 0 then
			Utils.DebugPrint(
				string.format("%s's win streak of %d ended", player.Name, data.WinStreak),
				"Trophies"
			)
			data.WinStreak = 0
		end
	end
	
	-- Apply trophy change (can't go below 0)
	local oldTrophies = data.Trophies or 0
	local oldLeague = data.CurrentLeague or "Rookie"
	
	data.Trophies = math.max(Config.TROPHIES.MinTrophies, oldTrophies + trophyChange)
	
	-- Update highest trophies
	if data.Trophies > (data.HighestTrophies or 0) then
		data.HighestTrophies = data.Trophies
	end
	
	-- Update season stats
	if data.SeasonData and data.Trophies > data.SeasonData.HighestThisSeason then
		data.SeasonData.HighestThisSeason = data.Trophies
	end
	
	-- Check for league change
	local newLeague = Utils.GetLeagueFromTrophies(data.Trophies)
	if newLeague and newLeague.Name ~= oldLeague then
		self:OnLeagueChanged(player, oldLeague, newLeague.Name)
		data.CurrentLeague = newLeague.Name
	end
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.TrophyChanged then
		RemoteEvents.TrophyChanged:FireClient(player, data.Trophies, trophyChange)
	end
	
	Utils.DebugPrint(
		string.format("%s: %+d trophies (now %d) - Place %d/%d", 
			player.Name, trophyChange, data.Trophies, place, totalPlayers),
		"Trophies"
	)
	
	return trophyChange
end

--[=[
	Handle league promotion/demotion
	@param player Player
	@param oldLeague string
	@param newLeague string
]=]
function TrophyManager:OnLeagueChanged(player: Player, oldLeague: string, newLeague: string)
	-- Find new league config
	local leagueConfig
	for _, league in ipairs(Config.LEAGUES) do
		if league.Name == newLeague then
			leagueConfig = league
			break
		end
	end
	
	if not leagueConfig then
		return
	end
	
	-- Determine if promotion or demotion
	local oldIndex = self:GetLeagueIndex(oldLeague)
	local newIndex = self:GetLeagueIndex(newLeague)
	local isPromotion = newIndex > oldIndex
	
	-- Award league reward (only on promotion)
	if isPromotion then
		self.CurrencyManager:AddCurrency(
			player,
			leagueConfig.Reward,
			string.format("Promoted to %s", newLeague)
		)
	end
	
	-- Notify client
	if RemoteEvents.LeagueChanged then
		RemoteEvents.LeagueChanged:FireClient(player, newLeague, oldLeague, isPromotion)
	end
	
	Utils.DebugPrint(
		string.format("%s %s to %s! (from %s)", 
			player.Name,
			isPromotion and "promoted" or "demoted",
			newLeague,
			oldLeague
		),
		"Trophies"
	)
end

--[=[
	Get league index for comparison
	@param leagueName string
	@return number
]=]
function TrophyManager:GetLeagueIndex(leagueName: string): number
	for i, league in ipairs(Config.LEAGUES) do
		if league.Name == leagueName then
			return i
		end
	end
	return 1 -- Default to first league
end

--[=[
	Get player's current league
	@param player Player
	@return string
]=]
function TrophyManager:GetLeague(player: Player): string
	local trophies = self:GetTrophies(player)
	local league = Utils.GetLeagueFromTrophies(trophies)
	return league and league.Name or "Rookie"
end

--[=[
	Get player's win streak
	@param player Player
	@return number
]=]
function TrophyManager:GetWinStreak(player: Player): number
	local data = self.DataStore:GetCachedData(player)
	return data and data.WinStreak or 0
end

--[=[
	Get current season ID
	@return number
]=]
function TrophyManager:GetCurrentSeasonId(): number
	if not Config.SEASONS.Enabled then
		return 0
	end
	
	-- Calculate season based on game launch date
	-- In production, store this in a DataStore
	local gameStartTime = 1699315200 -- Nov 7, 2025 (example)
	local currentTime = os.time()
	local secondsPerSeason = Config.SEASONS.DurationDays * 24 * 60 * 60
	
	return math.floor((currentTime - gameStartTime) / secondsPerSeason) + 1
end

--[=[
	Process season end for a player
	@param player Player
]=]
function TrophyManager:ProcessSeasonEnd(player: Player)
	local data = self.DataStore:GetCachedData(player)
	if not data or not Config.SEASONS.Enabled then
		return
	end
	
	local currentSeasonId = self:GetCurrentSeasonId()
	
	-- Check if player needs season update
	if data.SeasonData.SeasonId >= currentSeasonId then
		return -- Already processed
	end
	
	-- Award season end rewards based on highest league reached
	local league = Utils.GetLeagueFromTrophies(data.SeasonData.HighestThisSeason)
	if league and Config.SEASONS.EndRewards[league.Name] then
		local reward = Config.SEASONS.EndRewards[league.Name]
		self.CurrencyManager:AddCurrency(
			player,
			reward.Currency,
			string.format("Season %d reward (%s)", data.SeasonData.SeasonId, league.Name)
		)
	end
	
	-- Apply trophy decay
	local trophiesBeforeDecay = data.Trophies
	if data.Trophies > Config.SEASONS.DecayThreshold then
		local excessTrophies = data.Trophies - Config.SEASONS.DecayThreshold
		local decayedTrophies = excessTrophies * Config.SEASONS.TrophyDecay
		data.Trophies = Config.SEASONS.DecayThreshold + decayedTrophies
		
		Utils.DebugPrint(
			string.format("%s trophies decayed: %d → %d", player.Name, trophiesBeforeDecay, data.Trophies),
			"Trophies"
		)
	end
	
	-- Update season data
	data.SeasonData = {
		SeasonId = currentSeasonId,
		StartTrophies = data.Trophies,
		HighestThisSeason = data.Trophies
	}
	
	-- Update league
	local newLeague = Utils.GetLeagueFromTrophies(data.Trophies)
	data.CurrentLeague = newLeague and newLeague.Name or "Rookie"
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	Utils.DebugPrint(
		string.format("%s season updated to Season %d", player.Name, currentSeasonId),
		"Trophies"
	)
end

--[=[
	Admin: Set player trophies
	@param player Player
	@param amount number
]=]
function TrophyManager:SetTrophies(player: Player, amount: number)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false
	end
	
	local oldLeague = data.CurrentLeague or "Rookie"
	data.Trophies = math.max(Config.TROPHIES.MinTrophies, amount)
	
	-- Update highest
	if data.Trophies > (data.HighestTrophies or 0) then
		data.HighestTrophies = data.Trophies
	end
	
	-- Update league
	local newLeague = Utils.GetLeagueFromTrophies(data.Trophies)
	if newLeague and newLeague.Name ~= oldLeague then
		self:OnLeagueChanged(player, oldLeague, newLeague.Name)
		data.CurrentLeague = newLeague.Name
	end
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.TrophyChanged then
		RemoteEvents.TrophyChanged:FireClient(player, data.Trophies, 0)
	end
	
	return true
end

return TrophyManager
