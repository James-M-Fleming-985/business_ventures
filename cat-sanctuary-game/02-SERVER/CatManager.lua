--[[
	CatManager.lua
	Handles cat spawning, management, and skills
	
	COPY TO: ServerScriptService/CatSanctuary/CatManager (ModuleScript)
	COPY ORDER: #6
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Types = require(ReplicatedStorage.Shared.Types)
local Utils = require(ReplicatedStorage.Shared.Utils)

local CatManager = {}
CatManager.__index = CatManager

-- Remote events
local RemoteEvents = {
	CatAdded = nil,
	CatUpdated = nil,
	TrainCatRequest = nil
}

--[=[
	Initialize cat manager
	@param dataStore DataStore module
	@param currencyManager CurrencyManager module
]=]
function CatManager:Initialize(dataStore, currencyManager)
	self.DataStore = dataStore
	self.CurrencyManager = currencyManager
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "CatRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.CatAdded = Instance.new("RemoteEvent")
	RemoteEvents.CatAdded.Name = "CatAdded"
	RemoteEvents.CatAdded.Parent = remoteFolder
	
	RemoteEvents.CatUpdated = Instance.new("RemoteEvent")
	RemoteEvents.CatUpdated.Name = "CatUpdated"
	RemoteEvents.CatUpdated.Parent = remoteFolder
	
	RemoteEvents.TrainCatRequest = Instance.new("RemoteFunction")
	RemoteEvents.TrainCatRequest.Name = "TrainCatRequest"
	RemoteEvents.TrainCatRequest.Parent = remoteFolder
	
	-- Handle training requests
	RemoteEvents.TrainCatRequest.OnServerInvoke = function(player, catId, skillName)
		return self:TrainCat(player, catId, skillName)
	end
	
	Utils.DebugPrint("CatManager initialized", "Cats")
end

--[=[
	Spawn a new homeless cat for a player
	@param player Player
	@param catType string? -- Optional: specify cat type, otherwise random
	@return CatData?, string? -- cat, errorMessage
]=]
function CatManager:SpawnCat(player: Player, catType: string?)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return nil, "Player data not loaded"
	end
	
	-- Check cat capacity
	local maxCats = Config.PLAYER.MaxCats
	if Utils.PlayerOwnsGamePass(player, Config.GAME_PASSES.VIP) then
		maxCats = Config.PLAYER.MaxCatsWithVIP
	end
	
	if #data.Cats >= maxCats then
		return nil, string.format("Cat capacity reached (%d/%d)", #data.Cats, maxCats)
	end
	
	-- Determine cat type (random if not specified)
	local selectedCat
	if catType then
		-- Find specific cat type
		for _, cat in ipairs(Config.CATS) do
			if cat.Id == catType then
				selectedCat = cat
				break
			end
		end
		if not selectedCat then
			return nil, "Invalid cat type"
		end
	else
		-- Random cat based on rarity
		local rarity = Utils.WeightedRandom(Config.RARITY_CHANCES)
		local possibleCats = {}
		for _, cat in ipairs(Config.CATS) do
			if cat.Rarity == rarity then
				table.insert(possibleCats, cat)
			end
		end
		selectedCat = Utils.RandomFromArray(possibleCats)
	end
	
	if not selectedCat then
		return nil, "Failed to select cat"
	end
	
	-- Create cat instance
	local newCat: Types.CatData = {
		Id = Utils.GenerateId(),
		CatType = selectedCat.Id,
		Name = selectedCat.Name, -- Player can rename later
		Level = 1,
		Experience = 0,
		Stats = Utils.DeepCopy(selectedCat.BaseStats),
		Rarity = selectedCat.Rarity,
		Skills = {
			Speed = 0,
			Agility = 0,
			Intelligence = 0,
			Cuteness = 0
		},
		Friendship = 50, -- Starts at 50/100
		TimeAcquired = os.time()
	}
	
	-- Add to player's collection
	table.insert(data.Cats, newCat)
	
	-- Update statistics
	data.Statistics.CatsRescued = data.Statistics.CatsRescued + 1
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.CatAdded then
		RemoteEvents.CatAdded:FireClient(player, newCat)
	end
	
	Utils.DebugPrint(
		string.format("%s rescued a %s (%s)", player.Name, newCat.Name, newCat.Rarity),
		"Cats"
	)
	
	return newCat, nil
end

--[=[
	Get a cat by ID
	@param player Player
	@param catId string
	@return CatData?
]=]
function CatManager:GetCat(player: Player, catId: string): Types.CatData?
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return nil
	end
	
	for _, cat in ipairs(data.Cats) do
		if cat.Id == catId then
			return cat
		end
	end
	
	return nil
end

--[=[
	Get all cats for a player
	@param player Player
	@return {CatData}
]=]
function CatManager:GetAllCats(player: Player): {Types.CatData}
	local data = self.DataStore:GetCachedData(player)
	return data and data.Cats or {}
end

--[=[
	Train a cat's skill
	@param player Player
	@param catId string
	@param skillName string -- "Speed", "Agility", "Intelligence", "Cuteness"
	@return boolean, string -- success, message
]=]
function CatManager:TrainCat(player: Player, catId: string, skillName: string)
	local cat = self:GetCat(player, catId)
	if not cat then
		return false, "Cat not found"
	end
	
	-- Check if skill exists
	local skillConfig = Config.SKILLS[skillName]
	if not skillConfig then
		return false, "Invalid skill"
	end
	
	-- Check if already max level
	local currentLevel = cat.Skills[skillName] or 0
	if currentLevel >= skillConfig.MaxLevel then
		return false, "Skill already at max level"
	end
	
	-- Calculate training cost
	local cost = skillConfig.TrainingCost(currentLevel)
	
	-- Check if player can afford
	if not self.CurrencyManager:CanAfford(player, cost) then
		return false, string.format("Not enough charity (need %d)", cost)
	end
	
	-- Check for speed training game pass
	local hasSpeedTraining = Utils.PlayerOwnsGamePass(player, Config.GAME_PASSES.SpeedTrainer)
	local trainingTime = hasSpeedTraining and 1 or 3 -- Instant vs 3 seconds
	
	-- Remove currency
	local success = self.CurrencyManager:RemoveCurrency(player, cost, string.format("Train %s", skillName))
	if not success then
		return false, "Payment failed"
	end
	
	-- Increase skill
	cat.Skills[skillName] = currentLevel + 1
	
	-- Also increase base stat slightly
	cat.Stats[skillName] = cat.Stats[skillName] + 1
	
	-- Add experience
	local expGain = math.floor(cost / 10)
	self:AddExperience(player, catId, expGain)
	
	-- Update cache
	local data = self.DataStore:GetCachedData(player)
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.CatUpdated then
		RemoteEvents.CatUpdated:FireClient(player, cat)
	end
	
	Utils.DebugPrint(
		string.format("%s trained %s's %s (now level %d)", player.Name, cat.Name, skillName, cat.Skills[skillName]),
		"Cats"
	)
	
	return true, string.format("Trained %s to level %d", skillName, cat.Skills[skillName])
end

--[=[
	Add experience to a cat
	@param player Player
	@param catId string
	@param amount number
]=]
function CatManager:AddExperience(player: Player, catId: string, amount: number)
	local cat = self:GetCat(player, catId)
	if not cat then
		return
	end
	
	cat.Experience = cat.Experience + amount
	
	-- Check for level up
	local expNeeded = Utils.ExperienceForLevel(cat.Level)
	while cat.Experience >= expNeeded do
		cat.Experience = cat.Experience - expNeeded
		cat.Level = cat.Level + 1
		
		-- Bonus stat increase on level up
		for statName, _ in pairs(cat.Stats) do
			cat.Stats[statName] = cat.Stats[statName] + 2
		end
		
		Utils.DebugPrint(
			string.format("%s's %s leveled up to %d!", player.Name, cat.Name, cat.Level),
			"Cats"
		)
		
		expNeeded = Utils.ExperienceForLevel(cat.Level)
	end
	
	-- Update cache
	local data = self.DataStore:GetCachedData(player)
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.CatUpdated then
		RemoteEvents.CatUpdated:FireClient(player, cat)
	end
end

--[=[
	Rename a cat
	@param player Player
	@param catId string
	@param newName string
	@return boolean, string
]=]
function CatManager:RenameCat(player: Player, catId: string, newName: string)
	-- Filter inappropriate names
	local TextService = game:GetService("TextService")
	local success, filteredName = pcall(function()
		return TextService:FilterStringAsync(newName, player.UserId):GetNonChatStringForBroadcastAsync()
	end)
	
	if not success or not filteredName or filteredName == "" then
		return false, "Invalid name"
	end
	
	local cat = self:GetCat(player, catId)
	if not cat then
		return false, "Cat not found"
	end
	
	cat.Name = filteredName
	
	-- Update cache
	local data = self.DataStore:GetCachedData(player)
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.CatUpdated then
		RemoteEvents.CatUpdated:FireClient(player, cat)
	end
	
	return true, "Cat renamed to " .. filteredName
end

--[=[
	Calculate a cat's overall power rating
	@param cat CatData
	@return number
]=]
function CatManager:CalculatePower(cat: Types.CatData): number
	local totalStats = cat.Stats.Speed + cat.Stats.Agility + cat.Stats.Intelligence + cat.Stats.Cuteness
	local totalSkills = (cat.Skills.Speed + cat.Skills.Agility + cat.Skills.Intelligence + cat.Skills.Cuteness) * 2
	local levelBonus = cat.Level * 10
	
	return totalStats + totalSkills + levelBonus
end

--[=[
	Get best cat for a specific mini-game
	@param player Player
	@param gameType string
	@return CatData?
]=]
function CatManager:GetBestCatForGame(player: Player, gameType: string): Types.CatData?
	local gameConfig = Config.MINI_GAMES[gameType]
	if not gameConfig then
		return nil
	end
	
	local cats = self:GetAllCats(player)
	if #cats == 0 then
		return nil
	end
	
	-- Sort cats by performance for this game type
	table.sort(cats, function(a, b)
		local scoreA = Utils.CalculateGamePerformance(
			a.Stats[gameConfig.PrimaryStat],
			a.Stats[gameConfig.SecondaryStat]
		)
		local scoreB = Utils.CalculateGamePerformance(
			b.Stats[gameConfig.PrimaryStat],
			b.Stats[gameConfig.SecondaryStat]
		)
		return scoreA > scoreB
	end)
	
	return cats[1]
end

return CatManager
