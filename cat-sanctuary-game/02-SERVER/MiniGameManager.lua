--[[
	MiniGameManager.lua
	Orchestrates mini-game competitions between players
	
	COPY TO: ServerScriptService/CatSanctuary/MiniGameManager (ModuleScript)
	COPY ORDER: #8
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Config = require(ReplicatedStorage.Shared.Config)
local Types = require(ReplicatedStorage.Shared.Types)
local Utils = require(ReplicatedStorage.Shared.Utils)

local MiniGameManager = {}
MiniGameManager.__index = MiniGameManager

-- Active game sessions
local activeSessions = {}

-- Remote events
local RemoteEvents = {
	JoinGameRequest = nil,
	LeaveGameRequest = nil,
	GameStarted = nil,
	GameEnded = nil,
	GameUpdate = nil
}

--[=[
	Initialize mini-game manager
	@param dataStore DataStore module
	@param currencyManager CurrencyManager module
	@param catManager CatManager module
	@param trophyManager TrophyManager module
]=]
function MiniGameManager:Initialize(dataStore, currencyManager, catManager, trophyManager)
	self.DataStore = dataStore
	self.CurrencyManager = currencyManager
	self.CatManager = catManager
	self.TrophyManager = trophyManager
	self.GameModules = {}
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "MiniGameRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.JoinGameRequest = Instance.new("RemoteFunction")
	RemoteEvents.JoinGameRequest.Name = "JoinGameRequest"
	RemoteEvents.JoinGameRequest.Parent = remoteFolder
	
	RemoteEvents.LeaveGameRequest = Instance.new("RemoteFunction")
	RemoteEvents.LeaveGameRequest.Name = "LeaveGameRequest"
	RemoteEvents.LeaveGameRequest.Parent = remoteFolder
	
	RemoteEvents.GameStarted = Instance.new("RemoteEvent")
	RemoteEvents.GameStarted.Name = "GameStarted"
	RemoteEvents.GameStarted.Parent = remoteFolder
	
	RemoteEvents.GameEnded = Instance.new("RemoteEvent")
	RemoteEvents.GameEnded.Name = "GameEnded"
	RemoteEvents.GameEnded.Parent = remoteFolder
	
	RemoteEvents.GameUpdate = Instance.new("RemoteEvent")
	RemoteEvents.GameUpdate.Name = "GameUpdate"
	RemoteEvents.GameUpdate.Parent = remoteFolder
	
	-- Handle requests
	RemoteEvents.JoinGameRequest.OnServerInvoke = function(player, gameType, catId)
		return self:JoinGame(player, gameType, catId)
	end
	
	RemoteEvents.LeaveGameRequest.OnServerInvoke = function(player)
		return self:LeaveGame(player)
	end
	
	-- Load game modules
	self:LoadGameModules()
	
	-- Start matchmaking loop
	task.spawn(function()
		self:MatchmakingLoop()
	end)
	
	Utils.DebugPrint("MiniGameManager initialized", "MiniGames")
end

--[=[
	Load mini-game modules
]=]
function MiniGameManager:LoadGameModules()
	-- This will load individual game modules when they're created
	local miniGamesFolder = script.Parent:FindFirstChild("MiniGames")
	if miniGamesFolder then
		for _, module in ipairs(miniGamesFolder:GetChildren()) do
			if module:IsA("ModuleScript") then
				local success, gameModule = pcall(require, module)
				if success and gameModule then
					self.GameModules[module.Name] = gameModule
					Utils.DebugPrint(string.format("Loaded mini-game: %s", module.Name), "MiniGames")
				end
			end
		end
	end
end

--[=[
	Join a mini-game queue
	@param player Player
	@param gameType string
	@param catId string
	@return boolean, string
]=]
function MiniGameManager:JoinGame(player: Player, gameType: string, catId: string)
	-- Validate game type
	local gameConfig = Config.MINI_GAMES[gameType]
	if not gameConfig then
		return false, "Invalid game type"
	end
	
	-- Validate cat
	local cat = self.CatManager:GetCat(player, catId)
	if not cat then
		return false, "Cat not found"
	end
	
	-- Check if player is already in a game
	for _, session in pairs(activeSessions) do
		for _, participant in ipairs(session.Players) do
			if participant.Player == player then
				return false, "Already in a game"
			end
		end
	end
	
	-- Find or create session
	local session = self:FindOrCreateSession(gameType)
	
	-- Add player to session
	table.insert(session.Players, {
		Player = player,
		Cat = cat,
		Score = 0,
		Ready = true
	})
	
	Utils.DebugPrint(
		string.format("%s joined %s game with %s", player.Name, gameType, cat.Name),
		"MiniGames"
	)
	
	return true, string.format("Joined %s queue (%d/%d)", 
		gameConfig.Name, 
		#session.Players, 
		gameConfig.MaxPlayers
	)
end

--[=[
	Leave current game
	@param player Player
	@return boolean, string
]=]
function MiniGameManager:LeaveGame(player: Player)
	for sessionId, session in pairs(activeSessions) do
		for i, participant in ipairs(session.Players) do
			if participant.Player == player then
				table.remove(session.Players, i)
				
				-- If game is running, handle early leave
				if session.Running then
					-- Award participation reward
					self.CurrencyManager:AwardGameReward(
						player,
						99, -- No placement
						participant.Cat.Stats.Cuteness,
						session.GameType
					)
				end
				
				-- Clean up empty sessions
				if #session.Players == 0 then
					activeSessions[sessionId] = nil
				end
				
				Utils.DebugPrint(string.format("%s left game", player.Name), "MiniGames")
				return true, "Left game"
			end
		end
	end
	
	return false, "Not in a game"
end

--[=[
	Find existing session or create new one
	@param gameType string
	@return table
]=]
function MiniGameManager:FindOrCreateSession(gameType: string)
	-- Look for available session
	for _, session in pairs(activeSessions) do
		if session.GameType == gameType and 
		   not session.Running and 
		   #session.Players < Config.MINI_GAMES[gameType].MaxPlayers then
			return session
		end
	end
	
	-- Create new session
	local sessionId = Utils.GenerateId()
	local newSession = {
		Id = sessionId,
		GameType = gameType,
		Players = {},
		Running = false,
		StartTime = nil,
		CreatedAt = os.time()
	}
	
	activeSessions[sessionId] = newSession
	Utils.DebugPrint(string.format("Created new %s session", gameType), "MiniGames")
	
	return newSession
end

--[=[
	Matchmaking loop - starts games when ready
]=]
function MiniGameManager:MatchmakingLoop()
	while true do
		task.wait(2) -- Check every 2 seconds
		
		for sessionId, session in pairs(activeSessions) do
			if not session.Running then
				local gameConfig = Config.MINI_GAMES[session.GameType]
				local playerCount = #session.Players
				
				-- Start if we have minimum players and waited long enough
				local waitTime = os.time() - session.CreatedAt
				local shouldStart = playerCount >= gameConfig.MinPlayers and 
				                   (playerCount >= gameConfig.MaxPlayers or waitTime >= 30)
				
				if shouldStart then
					self:StartGame(session)
				end
			end
		end
	end
end

--[=[
	Start a game session
	@param session table
]=]
function MiniGameManager:StartGame(session)
	session.Running = true
	session.StartTime = os.time()
	
	local gameConfig = Config.MINI_GAMES[session.GameType]
	
	Utils.DebugPrint(
		string.format("Starting %s game with %d players", session.GameType, #session.Players),
		"MiniGames"
	)
	
	-- Notify all players
	for _, participant in ipairs(session.Players) do
		if RemoteEvents.GameStarted then
			RemoteEvents.GameStarted:FireClient(participant.Player, session.GameType, session.Id)
		end
	end
	
	-- Run game logic
	task.spawn(function()
		self:RunGame(session)
	end)
end

--[=[
	Run game logic
	@param session table
]=]
function MiniGameManager:RunGame(session)
	local gameConfig = Config.MINI_GAMES[session.GameType]
	local duration = gameConfig.Duration
	
	-- Simulate game (in real implementation, this would run actual game logic)
	for i = 1, duration do
		task.wait(1)
		
		-- Update game state
		if RemoteEvents.GameUpdate then
			for _, participant in ipairs(session.Players) do
				RemoteEvents.GameUpdate:FireClient(
					participant.Player,
					session.Id,
					duration - i -- Time remaining
				)
			end
		end
	end
	
	-- Game ended, calculate results
	self:EndGame(session)
end

--[=[
	End game and award rewards
	@param session table
]=]
function MiniGameManager:EndGame(session)
	local gameConfig = Config.MINI_GAMES[session.GameType]
	
	-- Calculate scores based on cat stats
	for _, participant in ipairs(session.Players) do
		local cat = participant.Cat
		local performance = Utils.CalculateGamePerformance(
			cat.Stats[gameConfig.PrimaryStat],
			cat.Stats[gameConfig.SecondaryStat]
		)
		
		-- Add some randomness (±10%)
		local randomFactor = 0.9 + (math.random() * 0.2)
		participant.Score = math.floor(performance * randomFactor * 100)
	end
	
	-- Sort by score
	table.sort(session.Players, function(a, b)
		return a.Score > b.Score
	end)
	
	-- Award rewards
	local results = {}
	for place, participant in ipairs(session.Players) do
		local reward = self.CurrencyManager:AwardGameReward(
			participant.Player,
			place,
			participant.Cat.Stats.Cuteness,
			session.GameType
		)
		
		-- Add experience to cat
		local expGain = math.floor(100 / place) -- 100 for 1st, 50 for 2nd, etc.
		self.CatManager:AddExperience(participant.Player, participant.Cat.Id, expGain)
		
		-- Update statistics
		self.DataStore:IncrementStatistic(participant.Player, "GamesPlayed", 1)
		if place == 1 then
			self.DataStore:IncrementStatistic(participant.Player, "GamesWon", 1)
		end
		
		-- Award trophies for competitive mode
		if self.TrophyManager then
			self.TrophyManager:AwardTrophies(participant.Player, place, #session.Players)
		end
		
		table.insert(results, {
			PlayerName = participant.Player.Name,
			CatName = participant.Cat.Name,
			Score = participant.Score,
			Place = place,
			Reward = reward
		})
	end
	
	-- Notify all players
	for _, participant in ipairs(session.Players) do
		if RemoteEvents.GameEnded then
			RemoteEvents.GameEnded:FireClient(participant.Player, results)
		end
	end
	
	Utils.DebugPrint(
		string.format("%s game ended. Winner: %s", session.GameType, results[1].PlayerName),
		"MiniGames"
	)
	
	-- Clean up session
	activeSessions[session.Id] = nil
end

--[=[
	Get active sessions for a game type
	@param gameType string
	@return {table}
]=]
function MiniGameManager:GetActiveSessions(gameType: string?)
	local sessions = {}
	for _, session in pairs(activeSessions) do
		if not gameType or session.GameType == gameType then
			table.insert(sessions, {
				Id = session.Id,
				GameType = session.GameType,
				PlayerCount = #session.Players,
				Running = session.Running
			})
		end
	end
	return sessions
end

return MiniGameManager
