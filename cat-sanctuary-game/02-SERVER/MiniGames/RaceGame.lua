--[[
	RaceGame.lua
	Racing mini-game logic
	
	COPY TO: ServerScriptService/CatSanctuary/MiniGames/RaceGame (ModuleScript)
	COPY ORDER: #9
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local RaceGame = {}

--[=[
	Get game configuration
	@return table
]=]
function RaceGame.GetConfig()
	return Config.MINI_GAMES.Race
end

--[=[
	Calculate race time based on cat stats
	@param cat CatData
	@return number -- Time in seconds
]=]
function RaceGame.CalculateRaceTime(cat)
	-- Base time is 60 seconds
	-- Speed reduces time, agility helps with obstacles
	local baseTime = 60
	
	local speedBonus = cat.Stats.Speed / 100 -- 0 to 1
	local agilityBonus = cat.Stats.Agility / 200 -- 0 to 0.5
	
	local totalBonus = speedBonus + agilityBonus
	local finalTime = baseTime * (1 - (totalBonus * 0.5)) -- Up to 50% faster
	
	-- Add skill level bonus
	local skillBonus = (cat.Skills.Speed or 0) * 0.1
	finalTime = finalTime * (1 - (skillBonus / 100))
	
	return math.max(finalTime, 10) -- Minimum 10 seconds
end

--[=[
	Generate race waypoints
	@param trackLength number
	@return {Vector3}
]=]
function RaceGame.GenerateTrack(trackLength: number)
	local waypoints = {}
	local currentPos = Vector3.new(0, 0, 0)
	
	for i = 1, trackLength do
		-- Create zigzag pattern
		local offset = math.sin(i * 0.5) * 20
		currentPos = Vector3.new(offset, 0, i * 10)
		table.insert(waypoints, currentPos)
	end
	
	return waypoints
end

--[=[
	Simulate race progress
	@param participants {table} -- Array of {Player, Cat}
	@param updateCallback function -- Called with progress updates
]=]
function RaceGame.SimulateRace(participants, updateCallback)
	local raceData = {}
	
	-- Initialize race data for each participant
	for _, participant in ipairs(participants) do
		local raceTime = RaceGame.CalculateRaceTime(participant.Cat)
		table.insert(raceData, {
			Participant = participant,
			TotalTime = raceTime,
			Progress = 0,
			Finished = false,
			FinishTime = nil
		})
	end
	
	-- Run race simulation
	local elapsedTime = 0
	local allFinished = false
	
	while not allFinished do
		task.wait(0.1)
		elapsedTime = elapsedTime + 0.1
		allFinished = true
		
		for _, data in ipairs(raceData) do
			if not data.Finished then
				data.Progress = math.min(elapsedTime / data.TotalTime, 1)
				
				if data.Progress >= 1 then
					data.Finished = true
					data.FinishTime = elapsedTime
				else
					allFinished = false
				end
			end
		end
		
		-- Send progress update
		if updateCallback then
			updateCallback(raceData)
		end
	end
	
	-- Sort by finish time
	table.sort(raceData, function(a, b)
		return a.FinishTime < b.FinishTime
	end)
	
	return raceData
end

return RaceGame
