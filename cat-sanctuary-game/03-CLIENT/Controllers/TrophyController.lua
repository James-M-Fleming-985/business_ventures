--[[
	TrophyController.lua
	Client-side controller for trophy and league UI
	
	COPY TO: StarterPlayer/StarterPlayerScripts/Controllers/TrophyController (ModuleScript)
	COPY ORDER: #15
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

-- Remote events
local TrophyRemotes = ReplicatedStorage:WaitForChild("TrophyRemotes")
local TrophyChanged = TrophyRemotes:WaitForChild("TrophyChanged")
local LeagueChanged = TrophyRemotes:WaitForChild("LeagueChanged")
local WinStreakUpdated = TrophyRemotes:WaitForChild("WinStreakUpdated")

local TrophyController = {}

-- UI elements
local trophyDisplay = nil
local leagueDisplay = nil
local winStreakDisplay = nil

-- Current values
local currentTrophies = 0
local currentLeague = "Rookie"
local currentWinStreak = 0

--[=[
	Initialize trophy controller
]=]
function TrophyController:Initialize()
	-- Listen for trophy updates
	TrophyChanged.OnClientEvent:Connect(function(trophies, change, reason)
		self:OnTrophyChanged(trophies, change, reason)
	end)
	
	-- Listen for league updates
	LeagueChanged.OnClientEvent:Connect(function(newLeague, oldLeague, reward)
		self:OnLeagueChanged(newLeague, oldLeague, reward)
	end)
	
	-- Listen for win streak updates
	WinStreakUpdated.OnClientEvent:Connect(function(winStreak, bonus)
		self:OnWinStreakUpdated(winStreak, bonus)
	end)
	
	print("TrophyController initialized")
end

--[=[
	Handle trophy change
	@param trophies number
	@param change number
	@param reason string
]=]
function TrophyController:OnTrophyChanged(trophies: number, change: number, reason: string)
	currentTrophies = trophies
	
	-- Update display if it exists
	if trophyDisplay then
		self:UpdateTrophyDisplay()
	end
	
	-- Show notification
	if math.abs(change) > 0 then
		local color = change > 0 and Color3.fromRGB(85, 255, 127) or Color3.fromRGB(255, 85, 85)
		local prefix = change > 0 and "+" or ""
		self:ShowNotification(
			string.format("%s%d Trophies", prefix, change),
			reason,
			color
		)
	end
	
	print(string.format("🏆 Trophies: %d (%+d)", trophies, change))
end

--[=[
	Handle league change
	@param newLeague string
	@param oldLeague string
	@param reward number
]=]
function TrophyController:OnLeagueChanged(newLeague: string, oldLeague: string, reward: number)
	currentLeague = newLeague
	
	-- Update display if it exists
	if leagueDisplay then
		self:UpdateLeagueDisplay()
	end
	
	-- Determine if promotion or demotion
	local oldIndex = self:GetLeagueIndex(oldLeague)
	local newIndex = self:GetLeagueIndex(newLeague)
	
	if newIndex > oldIndex then
		-- Promotion!
		self:ShowLeaguePromotion(newLeague, reward)
	elseif newIndex < oldIndex then
		-- Demotion
		self:ShowLeagueDemotion(newLeague)
	end
	
	print(string.format("🎖️ League changed: %s → %s", oldLeague, newLeague))
end

--[=[
	Handle win streak update
	@param winStreak number
	@param bonus number
]=]
function TrophyController:OnWinStreakUpdated(winStreak: number, bonus: number)
	currentWinStreak = winStreak
	
	-- Update display if it exists
	if winStreakDisplay then
		self:UpdateWinStreakDisplay()
	end
	
	-- Show bonus notification if applicable
	if bonus > 0 then
		self:ShowNotification(
			string.format("🔥 %d Win Streak!", winStreak),
			string.format("+%d Bonus Trophies", bonus),
			Color3.fromRGB(255, 170, 0)
		)
	end
	
	print(string.format("🔥 Win streak: %d (bonus: +%d)", winStreak, bonus))
end

--[=[
	Get league index for comparison
	@param leagueName string
	@return number
]=]
function TrophyController:GetLeagueIndex(leagueName: string): number
	for i, league in ipairs(Config.LEAGUES) do
		if league.Name == leagueName then
			return i
		end
	end
	return 1
end

--[=[
	Update trophy display
]=]
function TrophyController:UpdateTrophyDisplay()
	if not trophyDisplay then return end
	
	trophyDisplay.Text = Utils.FormatTrophies(currentTrophies)
end

--[=[
	Update league display
]=]
function TrophyController:UpdateLeagueDisplay()
	if not leagueDisplay then return end
	
	local league = Utils.GetLeagueFromTrophies(currentTrophies)
	if league then
		leagueDisplay.Text = string.format("%s %s", league.Icon, league.Name)
		leagueDisplay.TextColor3 = league.Color
	end
end

--[=[
	Update win streak display
]=]
function TrophyController:UpdateWinStreakDisplay()
	if not winStreakDisplay then return end
	
	if currentWinStreak > 0 then
		winStreakDisplay.Visible = true
		winStreakDisplay.Text = string.format("🔥 %d", currentWinStreak)
	else
		winStreakDisplay.Visible = false
	end
end

--[=[
	Show league promotion screen
	@param newLeague string
	@param reward number
]=]
function TrophyController:ShowLeaguePromotion(newLeague: string, reward: number)
	-- Create promotion screen
	local promotionGui = Instance.new("ScreenGui")
	promotionGui.Name = "LeaguePromotion"
	promotionGui.Parent = playerGui
	promotionGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	
	-- Background overlay
	local overlay = Instance.new("Frame")
	overlay.Size = UDim2.new(1, 0, 1, 0)
	overlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	overlay.BackgroundTransparency = 0.5
	overlay.Parent = promotionGui
	
	-- Promotion card
	local card = Instance.new("Frame")
	card.Size = UDim2.new(0, 400, 0, 300)
	card.Position = UDim2.new(0.5, 0, 0.5, 0)
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
	card.BorderSizePixel = 0
	card.Parent = promotionGui
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 12)
	corner.Parent = card
	
	-- Title
	local title = Instance.new("TextLabel")
	title.Size = UDim2.new(1, -40, 0, 50)
	title.Position = UDim2.new(0, 20, 0, 20)
	title.BackgroundTransparency = 1
	title.Text = "🎉 PROMOTED!"
	title.Font = Enum.Font.GothamBold
	title.TextSize = 32
	title.TextColor3 = Color3.fromRGB(85, 255, 127)
	title.Parent = card
	
	-- League info
	local league = Utils.GetLeagueFromTrophies(currentTrophies)
	if league then
		local leagueIcon = Instance.new("TextLabel")
		leagueIcon.Size = UDim2.new(1, -40, 0, 80)
		leagueIcon.Position = UDim2.new(0, 20, 0, 90)
		leagueIcon.BackgroundTransparency = 1
		leagueIcon.Text = league.Icon
		leagueIcon.Font = Enum.Font.Gotham
		leagueIcon.TextSize = 64
		leagueIcon.Parent = card
		
		local leagueName = Instance.new("TextLabel")
		leagueName.Size = UDim2.new(1, -40, 0, 30)
		leagueName.Position = UDim2.new(0, 20, 0, 170)
		leagueName.BackgroundTransparency = 1
		leagueName.Text = league.Name
		leagueName.Font = Enum.Font.GothamBold
		leagueName.TextSize = 24
		leagueName.TextColor3 = league.Color
		leagueName.Parent = card
	end
	
	-- Reward text
	local rewardText = Instance.new("TextLabel")
	rewardText.Size = UDim2.new(1, -40, 0, 30)
	rewardText.Position = UDim2.new(0, 20, 0, 210)
	rewardText.BackgroundTransparency = 1
	rewardText.Text = string.format("Reward: $%s", Utils.FormatNumber(reward))
	rewardText.Font = Enum.Font.Gotham
	rewardText.TextSize = 18
	rewardText.TextColor3 = Color3.fromRGB(255, 215, 0)
	rewardText.Parent = card
	
	-- Close button
	local closeButton = Instance.new("TextButton")
	closeButton.Size = UDim2.new(0, 100, 0, 40)
	closeButton.Position = UDim2.new(0.5, 0, 1, -60)
	closeButton.AnchorPoint = Vector2.new(0.5, 0)
	closeButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
	closeButton.Text = "Continue"
	closeButton.Font = Enum.Font.GothamBold
	closeButton.TextSize = 16
	closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
	closeButton.Parent = card
	
	local closeCorner = Instance.new("UICorner")
	closeCorner.CornerRadius = UDim.new(0, 8)
	closeCorner.Parent = closeButton
	
	closeButton.MouseButton1Click:Connect(function()
		promotionGui:Destroy()
	end)
	
	-- Auto-close after 5 seconds
	task.delay(5, function()
		if promotionGui then
			promotionGui:Destroy()
		end
	end)
end

--[=[
	Show league demotion notification
	@param newLeague string
]=]
function TrophyController:ShowLeagueDemotion(newLeague: string)
	self:ShowNotification(
		"Demoted",
		string.format("New league: %s", newLeague),
		Color3.fromRGB(255, 85, 85)
	)
end

--[=[
	Show generic notification
	@param title string
	@param message string
	@param color Color3
]=]
function TrophyController:ShowNotification(title: string, message: string, color: Color3)
	-- Simple notification - in real game, this would be more polished
	local notification = Instance.new("ScreenGui")
	notification.Name = "TrophyNotification"
	notification.Parent = playerGui
	
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(0, 300, 0, 80)
	frame.Position = UDim2.new(1, -320, 0, 20)
	frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
	frame.BorderSizePixel = 0
	frame.Parent = notification
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 8)
	corner.Parent = frame
	
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(1, -20, 0, 30)
	titleLabel.Position = UDim2.new(0, 10, 0, 10)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = title
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 18
	titleLabel.TextColor3 = color
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = frame
	
	local messageLabel = Instance.new("TextLabel")
	messageLabel.Size = UDim2.new(1, -20, 0, 25)
	messageLabel.Position = UDim2.new(0, 10, 0, 45)
	messageLabel.BackgroundTransparency = 1
	messageLabel.Text = message
	messageLabel.Font = Enum.Font.Gotham
	messageLabel.TextSize = 14
	messageLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	messageLabel.TextXAlignment = Enum.TextXAlignment.Left
	messageLabel.Parent = frame
	
	-- Auto-remove after 3 seconds
	task.delay(3, function()
		if notification then
			notification:Destroy()
		end
	end)
end

--[=[
	Set trophy display element (called by MainUI)
	@param element TextLabel
]=]
function TrophyController:SetTrophyDisplay(element)
	trophyDisplay = element
	self:UpdateTrophyDisplay()
end

--[=[
	Set league display element (called by MainUI)
	@param element TextLabel
]=]
function TrophyController:SetLeagueDisplay(element)
	leagueDisplay = element
	self:UpdateLeagueDisplay()
end

--[=[
	Set win streak display element (called by MainUI)
	@param element TextLabel
]=]
function TrophyController:SetWinStreakDisplay(element)
	winStreakDisplay = element
	self:UpdateWinStreakDisplay()
end

return TrophyController
