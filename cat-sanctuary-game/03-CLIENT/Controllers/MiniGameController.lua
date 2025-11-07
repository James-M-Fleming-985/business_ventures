--[[
	MiniGameController.lua
	Client-side mini-game participation
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/Controllers/MiniGameController (LocalScript)
	COPY ORDER: #14
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local MiniGameController = {}

-- Game state
local inGame = false
local currentGameType = nil
local currentSessionId = nil

-- Remote events
local miniGameRemotes = ReplicatedStorage:WaitForChild("MiniGameRemotes")
local joinGameRequest = miniGameRemotes:WaitForChild("JoinGameRequest")
local leaveGameRequest = miniGameRemotes:WaitForChild("LeaveGameRequest")
local gameStarted = miniGameRemotes:WaitForChild("GameStarted")
local gameEnded = miniGameRemotes:WaitForChild("GameEnded")
local gameUpdate = miniGameRemotes:WaitForChild("GameUpdate")

--[=[
	Initialize mini-game controller
]=]
function MiniGameController:Initialize()
	-- Listen for game events
	gameStarted.OnClientEvent:Connect(function(gameType, sessionId)
		self:OnGameStarted(gameType, sessionId)
	end)
	
	gameEnded.OnClientEvent:Connect(function(results)
		self:OnGameEnded(results)
	end)
	
	gameUpdate.OnClientEvent:Connect(function(sessionId, timeRemaining)
		self:OnGameUpdate(sessionId, timeRemaining)
	end)
	
	print("🎮 MiniGameController initialized")
end

--[=[
	Join a mini-game queue
	@param gameType string
	@param catId string
]=]
function MiniGameController:JoinGame(gameType: string, catId: string)
	if inGame then
		warn("Already in a game")
		return false
	end
	
	local success, message = joinGameRequest:InvokeServer(gameType, catId)
	
	if success then
		print("✅ Joined game:", message)
		self:ShowQueueUI(gameType)
	else
		warn("❌ Failed to join game:", message)
	end
	
	return success
end

--[=[
	Leave current game
]=]
function MiniGameController:LeaveGame()
	if not inGame then
		return false
	end
	
	local success, message = leaveGameRequest:InvokeServer()
	
	if success then
		print("Left game")
		inGame = false
		currentGameType = nil
		currentSessionId = nil
		self:HideGameUI()
	end
	
	return success
end

--[=[
	Handle game started event
	@param gameType string
	@param sessionId string
]=]
function MiniGameController:OnGameStarted(gameType: string, sessionId: string)
	inGame = true
	currentGameType = gameType
	currentSessionId = sessionId
	
	print(string.format("🎮 Game started: %s", gameType))
	
	-- Show game UI
	self:ShowGameUI(gameType)
	
	-- Show notification
	local gameConfig = Config.MINI_GAMES[gameType]
	self:ShowNotification(
		string.format("%s starting now!", gameConfig.Name),
		Config.UI.Colors.Accent
	)
end

--[=[
	Handle game ended event
	@param results table
]=]
function MiniGameController:OnGameEnded(results)
	print("🏁 Game ended!")
	
	-- Show results UI
	self:ShowResultsUI(results)
	
	-- Reset state
	task.delay(5, function()
		inGame = false
		currentGameType = nil
		currentSessionId = nil
		self:HideGameUI()
	end)
end

--[=[
	Handle game update event
	@param sessionId string
	@param timeRemaining number
]=]
function MiniGameController:OnGameUpdate(sessionId: string, timeRemaining: number)
	if sessionId ~= currentSessionId then return end
	
	-- Update timer UI
	local timerLabel = Player.PlayerGui:FindFirstChild("GameUI")
	if timerLabel then
		local timer = timerLabel:FindFirstChild("Timer")
		if timer then
			timer.Text = string.format("Time: %s", Utils.FormatTime(timeRemaining))
		end
	end
end

--[=[
	Show queue waiting UI
	@param gameType string
]=]
function MiniGameController:ShowQueueUI(gameType: string)
	local playerGui = Player:WaitForChild("PlayerGui")
	
	local queueUI = Instance.new("ScreenGui")
	queueUI.Name = "QueueUI"
	queueUI.ResetOnSpawn = false
	queueUI.Parent = playerGui
	
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(0, 300, 0, 100)
	frame.Position = UDim2.new(0.5, -150, 0.8, 0)
	frame.BackgroundColor3 = Config.UI.Colors.Primary
	frame.Parent = queueUI
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = frame
	
	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, 0, 1, 0)
	label.BackgroundTransparency = 1
	label.Text = string.format("In Queue: %s\nWaiting for players...", gameType)
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Parent = frame
end

--[=[
	Show game UI during match
	@param gameType string
]=]
function MiniGameController:ShowGameUI(gameType: string)
	-- Remove queue UI
	local queueUI = Player.PlayerGui:FindFirstChild("QueueUI")
	if queueUI then
		queueUI:Destroy()
	end
	
	local playerGui = Player:WaitForChild("PlayerGui")
	
	local gameUI = Instance.new("ScreenGui")
	gameUI.Name = "GameUI"
	gameUI.ResetOnSpawn = false
	gameUI.Parent = playerGui
	
	-- Timer
	local timer = Instance.new("TextLabel")
	timer.Name = "Timer"
	timer.Size = UDim2.new(0, 200, 0, 50)
	timer.Position = UDim2.new(0.5, -100, 0.05, 0)
	timer.BackgroundColor3 = Config.UI.Colors.Secondary
	timer.Text = "Time: --:--"
	timer.TextColor3 = Color3.new(1, 1, 1)
	timer.TextScaled = true
	timer.Font = Enum.Font.GothamBold
	timer.Parent = gameUI
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = timer
end

--[=[
	Show results UI after game
	@param results table
]=]
function MiniGameController:ShowResultsUI(results)
	self:HideGameUI()
	
	local playerGui = Player:WaitForChild("PlayerGui")
	
	local resultsUI = Instance.new("ScreenGui")
	resultsUI.Name = "ResultsUI"
	resultsUI.ResetOnSpawn = false
	resultsUI.Parent = playerGui
	
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(0, 500, 0, 400)
	frame.Position = UDim2.new(0.5, -250, 0.5, -200)
	frame.BackgroundColor3 = Config.UI.Colors.Primary
	frame.Parent = resultsUI
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 15)
	corner.Parent = frame
	
	-- Title
	local title = Instance.new("TextLabel")
	title.Size = UDim2.new(1, 0, 0, 60)
	title.BackgroundTransparency = 1
	title.Text = "🏆 Game Results 🏆"
	title.TextColor3 = Color3.new(1, 1, 1)
	title.TextSize = 32
	title.Font = Enum.Font.GothamBold
	title.Parent = frame
	
	-- Results list
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 10)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	
	local resultsFrame = Instance.new("Frame")
	resultsFrame.Size = UDim2.new(0.9, 0, 0.7, 0)
	resultsFrame.Position = UDim2.new(0.05, 0, 0.2, 0)
	resultsFrame.BackgroundTransparency = 1
	resultsFrame.Parent = frame
	listLayout.Parent = resultsFrame
	
	-- Add each result
	for _, result in ipairs(results) do
		local resultLabel = Instance.new("TextLabel")
		resultLabel.Size = UDim2.new(1, 0, 0, 40)
		resultLabel.BackgroundColor3 = Config.UI.Colors.Secondary
		resultLabel.Text = string.format("#%d: %s (%s) - %d pts - +%d charity",
			result.Place,
			result.PlayerName,
			result.CatName,
			result.Score,
			result.Reward
		)
		resultLabel.TextColor3 = Color3.new(1, 1, 1)
		resultLabel.TextScaled = true
		resultLabel.Font = Enum.Font.Gotham
		resultLabel.Parent = resultsFrame
		
		local resultCorner = Instance.new("UICorner")
		resultCorner.CornerRadius = UDim.new(0, 8)
		resultCorner.Parent = resultLabel
	end
	
	-- Auto-close after 10 seconds
	task.delay(10, function()
		if resultsUI then
			resultsUI:Destroy()
		end
	end)
end

--[=[
	Hide game UI
]=]
function MiniGameController:HideGameUI()
	local playerGui = Player:WaitForChild("PlayerGui")
	
	local gameUI = playerGui:FindFirstChild("GameUI")
	if gameUI then
		gameUI:Destroy()
	end
	
	local queueUI = playerGui:FindFirstChild("QueueUI")
	if queueUI then
		queueUI:Destroy()
	end
end

--[=[
	Show notification
	@param message string
	@param color Color3
]=]
function MiniGameController:ShowNotification(message: string, color: Color3?)
	local CatController = require(script.Parent.CatController)
	CatController:ShowNotification(message, color)
end

-- Initialize when script runs
MiniGameController:Initialize()

return MiniGameController
