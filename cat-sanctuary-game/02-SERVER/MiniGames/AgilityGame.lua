--[[
	AgilityGame.lua
	Agility course mini-game logic
	
	COPY TO: ServerScriptService/CatSanctuary/MiniGames/AgilityGame (ModuleScript)
	COPY ORDER: #10
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local AgilityGame = {}

--[=[
	Get game configuration
	@return table
]=]
function AgilityGame.GetConfig()
	return Config.MINI_GAMES.Agility
end

--[=[
	Calculate agility course score
	@param cat CatData
	@return number -- Score 0-1000
]=]
function AgilityGame.CalculateScore(cat)
	-- Base score calculation
	local agilityScore = cat.Stats.Agility * 5 -- 0-500
	local speedScore = cat.Stats.Speed * 3     -- 0-300
	local intelligenceScore = cat.Stats.Intelligence * 2 -- 0-200
	
	local baseScore = agilityScore + speedScore + intelligenceScore
	
	-- Add skill bonus
	local skillBonus = (cat.Skills.Agility or 0) * 10
	baseScore = baseScore + skillBonus
	
	-- Add level bonus
	local levelBonus = cat.Level * 5
	baseScore = baseScore + levelBonus
	
	return math.min(baseScore, 1000)
end

--[=[
	Generate obstacle course
	@param difficulty number -- 1-10
	@return {table} -- Array of obstacles
]=]
function AgilityGame.GenerateCourse(difficulty: number)
	local obstacles = {}
	local obstacleTypes = {"Jump", "Tunnel", "Weave", "Balance", "Climb"}
	
	local obstacleCount = 5 + (difficulty * 2)
	
	for i = 1, obstacleCount do
		local obstacleType = Utils.RandomFromArray(obstacleTypes)
		table.insert(obstacles, {
			Type = obstacleType,
			Position = i,
			Difficulty = math.random(1, difficulty)
		})
	end
	
	return obstacles
end

--[=[
	Simulate cat navigating obstacle
	@param cat CatData
	@param obstacle table
	@return boolean, number -- success, timeSpent
]=]
function AgilityGame.NavigateObstacle(cat, obstacle)
	local successChance = 0.7 -- Base 70% success rate
	
	-- Adjust based on relevant stats
	if obstacle.Type == "Jump" then
		successChance = successChance + (cat.Stats.Agility / 200)
	elseif obstacle.Type == "Tunnel" then
		successChance = successChance + (cat.Stats.Speed / 200)
	elseif obstacle.Type == "Weave" then
		successChance = successChance + (cat.Stats.Agility / 200)
	elseif obstacle.Type == "Balance" then
		successChance = successChance + (cat.Stats.Intelligence / 200)
	elseif obstacle.Type == "Climb" then
		successChance = successChance + (cat.Stats.Agility / 200)
	end
	
	-- Add skill level bonus
	successChance = successChance + ((cat.Skills.Agility or 0) / 200)
	
	-- Clamp between 0.1 and 0.95
	successChance = Utils.Clamp(successChance, 0.1, 0.95)
	
	-- Roll for success
	local success = math.random() < successChance
	
	-- Calculate time spent (faster cats spend less time)
	local baseTime = 3 -- 3 seconds per obstacle
	local speedModifier = 1 - (cat.Stats.Speed / 200) -- Up to 50% faster
	local timeSpent = baseTime * speedModifier
	
	if not success then
		timeSpent = timeSpent * 1.5 -- Failure adds time
	end
	
	return success, timeSpent
end

--[=[
	Simulate full agility course
	@param participants {table}
	@param updateCallback function
]=]
function AgilityGame.SimulateCourse(participants, updateCallback)
	local courseResults = {}
	local obstacles = AgilityGame.GenerateCourse(5) -- Medium difficulty
	
	-- Run each cat through the course
	for _, participant in ipairs(participants) do
		local totalTime = 0
		local successfulObstacles = 0
		local obstacleResults = {}
		
		for _, obstacle in ipairs(obstacles) do
			local success, timeSpent = AgilityGame.NavigateObstacle(participant.Cat, obstacle)
			totalTime = totalTime + timeSpent
			
			if success then
				successfulObstacles = successfulObstacles + 1
			end
			
			table.insert(obstacleResults, {
				Obstacle = obstacle,
				Success = success,
				Time = timeSpent
			})
			
			-- Small delay for animation
			task.wait(0.2)
		end
		
		-- Calculate final score
		local completionBonus = (successfulObstacles / #obstacles) * 500
		local timeBonus = math.max(0, 500 - (totalTime * 5))
		local finalScore = completionBonus + timeBonus
		
		table.insert(courseResults, {
			Participant = participant,
			Score = finalScore,
			TotalTime = totalTime,
			SuccessRate = successfulObstacles / #obstacles,
			ObstacleResults = obstacleResults
		})
		
		-- Send progress update
		if updateCallback then
			updateCallback(courseResults)
		end
	end
	
	-- Sort by score
	table.sort(courseResults, function(a, b)
		return a.Score > b.Score
	end)
	
	return courseResults
end

return AgilityGame
