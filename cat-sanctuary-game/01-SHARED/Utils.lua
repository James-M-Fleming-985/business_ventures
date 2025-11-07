--[[
	Utils.lua
	Utility functions used throughout the game
	
	COPY TO: ReplicatedStorage/Shared/Utils (ModuleScript)
	COPY ORDER: #3
]]

local Utils = {}

--[=[
	Generate a unique ID for game objects
	@return string -- Unique identifier
]=]
function Utils.GenerateId(): string
	local HttpService = game:GetService("HttpService")
	return HttpService:GenerateGUID(false)
end

--[=[
	Format a number with commas (1000 -> 1,000)
	@param number number
	@return string
]=]
function Utils.FormatNumber(number: number): string
	local formatted = tostring(number)
	local k
	while true do
		formatted, k = string.gsub(formatted, "^(-?%d+)(%d%d%d)", '%1,%2')
		if k == 0 then
			break
		end
	end
	return formatted
end

--[=[
	Format large numbers with suffixes (1000 -> 1K, 1000000 -> 1M)
	@param number number
	@return string
]=]
function Utils.FormatNumberShort(number: number): string
	local suffixes = {"", "K", "M", "B", "T", "Qa", "Qi"}
	local suffixIndex = 1
	
	while number >= 1000 and suffixIndex < #suffixes do
		number = number / 1000
		suffixIndex = suffixIndex + 1
	end
	
	if suffixIndex == 1 then
		return tostring(math.floor(number))
	else
		return string.format("%.1f%s", number, suffixes[suffixIndex])
	end
end

--[=[
	Format time in seconds to readable format
	@param seconds number
	@return string
]=]
function Utils.FormatTime(seconds: number): string
	if seconds < 60 then
		return string.format("%ds", seconds)
	elseif seconds < 3600 then
		local minutes = math.floor(seconds / 60)
		local secs = math.floor(seconds % 60)
		return string.format("%dm %ds", minutes, secs)
	elseif seconds < 86400 then
		local hours = math.floor(seconds / 3600)
		local minutes = math.floor((seconds % 3600) / 60)
		return string.format("%dh %dm", hours, minutes)
	else
		local days = math.floor(seconds / 86400)
		local hours = math.floor((seconds % 86400) / 3600)
		return string.format("%dd %dh", days, hours)
	end
end

--[=[
	Deep copy a table (recursive)
	@param original table
	@return table
]=]
function Utils.DeepCopy(original: any): any
	local copy
	if type(original) == 'table' then
		copy = {}
		for key, value in pairs(original) do
			copy[Utils.DeepCopy(key)] = Utils.DeepCopy(value)
		end
		setmetatable(copy, Utils.DeepCopy(getmetatable(original)))
	else
		copy = original
	end
	return copy
end

--[=[
	Merge two tables (shallow merge)
	@param t1 table
	@param t2 table
	@return table
]=]
function Utils.MergeTables(t1: {[any]: any}, t2: {[any]: any}): {[any]: any}
	local result = Utils.DeepCopy(t1)
	for key, value in pairs(t2) do
		result[key] = value
	end
	return result
end

--[=[
	Get random item from array
	@param array table
	@return any
]=]
function Utils.RandomFromArray(array: {any}): any
	if #array == 0 then return nil end
	return array[math.random(1, #array)]
end

--[=[
	Weighted random selection based on chances table
	Example: {Common = 70, Rare = 30} -> 70% Common, 30% Rare
	@param chances table
	@return string -- Selected key
]=]
function Utils.WeightedRandom(chances: {[string]: number}): string
	local total = 0
	for _, weight in pairs(chances) do
		total = total + weight
	end
	
	local roll = math.random() * total
	local current = 0
	
	for key, weight in pairs(chances) do
		current = current + weight
		if roll <= current then
			return key
		end
	end
	
	-- Fallback (shouldn't reach here)
	return next(chances)
end

--[=[
	Clamp a number between min and max
	@param value number
	@param min number
	@param max number
	@return number
]=]
function Utils.Clamp(value: number, min: number, max: number): number
	return math.max(min, math.min(max, value))
end

--[=[
	Linear interpolation
	@param a number
	@param b number
	@param t number -- 0 to 1
	@return number
]=]
function Utils.Lerp(a: number, b: number, t: number): number
	return a + (b - a) * t
end

--[=[
	Check if a player owns a game pass
	@param player Player
	@param gamePassId number
	@return boolean
]=]
function Utils.PlayerOwnsGamePass(player: Player, gamePassId: number): boolean
	if gamePassId == 0 then return false end -- Not configured yet
	
	local MarketplaceService = game:GetService("MarketplaceService")
	local success, owns = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, gamePassId)
	end)
	
	return success and owns
end

--[=[
	Safe wait with timeout
	@param condition function -- Returns true when done
	@param timeout number -- Max seconds to wait
	@return boolean -- True if condition met, false if timeout
]=]
function Utils.WaitForCondition(condition: () -> boolean, timeout: number): boolean
	local startTime = tick()
	while not condition() do
		if tick() - startTime > timeout then
			return false
		end
		task.wait(0.1)
	end
	return true
end

--[=[
	Calculate experience needed for next level
	@param level number
	@return number
]=]
function Utils.ExperienceForLevel(level: number): number
	-- Exponential curve: 100 * (1.1 ^ level)
	return math.floor(100 * (1.1 ^ level))
end

--[=[
	Calculate total experience needed to reach a level
	@param targetLevel number
	@return number
]=]
function Utils.TotalExperienceForLevel(targetLevel: number): number
	local total = 0
	for level = 1, targetLevel - 1 do
		total = total + Utils.ExperienceForLevel(level)
	end
	return total
end

--[=[
	Get level from total experience
	@param experience number
	@return number -- Current level
]=]
function Utils.GetLevelFromExperience(experience: number): number
	local level = 1
	local totalNeeded = 0
	
	while experience >= totalNeeded do
		totalNeeded = totalNeeded + Utils.ExperienceForLevel(level)
		if experience >= totalNeeded then
			level = level + 1
		end
	end
	
	return level
end

--[=[
	Calculate stat effectiveness in a mini-game
	@param primaryStat number -- Main stat value
	@param secondaryStat number -- Secondary stat value
	@return number -- Combined effectiveness (0-100)
]=]
function Utils.CalculateGamePerformance(primaryStat: number, secondaryStat: number): number
	-- 70% primary, 30% secondary
	local performance = (primaryStat * 0.7) + (secondaryStat * 0.3)
	return Utils.Clamp(performance, 0, 100)
end

--[=[
	Get rarity color
	@param rarity string
	@return Color3
]=]
function Utils.GetRarityColor(rarity: string): Color3
	local colors = {
		Common = Color3.fromRGB(255, 255, 255),      -- White
		Uncommon = Color3.fromRGB(76, 175, 80),      -- Green
		Rare = Color3.fromRGB(33, 150, 243),         -- Blue
		Epic = Color3.fromRGB(156, 39, 176),         -- Purple
		Legendary = Color3.fromRGB(255, 193, 7)      -- Gold
	}
	return colors[rarity] or colors.Common
end

--[=[
	Get league info from trophy count
	@param trophies number
	@return table? -- League config
]=]
function Utils.GetLeagueFromTrophies(trophies: number): any
	local Config = require(game.ReplicatedStorage.Shared.Config)
	
	for _, league in ipairs(Config.LEAGUES) do
		if trophies >= league.MinTrophies and trophies <= league.MaxTrophies then
			return league
		end
	end
	
	-- Default to last league (Champion) if above all thresholds
	return Config.LEAGUES[#Config.LEAGUES]
end

--[=[
	Format trophy count with icon
	@param trophies number
	@return string
]=]
function Utils.FormatTrophies(trophies: number): string
	return string.format("🏆 %s", Utils.FormatNumber(trophies))
end

--[=[
	Calculate trophies gained/lost
	@param place number
	@param totalPlayers number
	@return number -- Positive = gain, Negative = loss
]=]
function Utils.CalculateTrophyChange(place: number, totalPlayers: number): number
	local Config = require(game.ReplicatedStorage.Shared.Config)
	
	-- Check for direct reward
	if Config.TROPHIES.Rewards[place] then
		return Config.TROPHIES.Rewards[place]
	end
	
	-- Calculate loss for poor placement
	return -Config.TROPHIES.LossAmount(place, totalPlayers)
end

--[=[
	Print debug message (only if debug enabled)
	@param message string
	@param category string
]=]
function Utils.DebugPrint(message: string, category: string?)
	local Config = require(game.ReplicatedStorage.Shared.Config)
	if Config.DEBUG.Enabled then
		local prefix = category and string.format("[%s]", category) or "[DEBUG]"
		print(prefix, message)
	end
end

--[=[
	Validate player data structure
	@param data table
	@return boolean, string? -- isValid, errorMessage
]=]
function Utils.ValidatePlayerData(data: any): (boolean, string?)
	if type(data) ~= "table" then
		return false, "Data is not a table"
	end
	
	local required = {"UserId", "Currency", "Cats", "Sanctuary", "Statistics"}
	for _, field in ipairs(required) do
		if data[field] == nil then
			return false, string.format("Missing required field: %s", field)
		end
	end
	
	return true, nil
end

return Utils
