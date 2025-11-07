--[[
	MainUI.lua
	Main HUD and interface
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/UI/MainUI (LocalScript)
	COPY ORDER: #15
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

-- Controllers
local ControllersFolder = script.Parent.Parent.Controllers
local CatController = require(ControllersFolder:WaitForChild("CatController"))
local SanctuaryController = require(ControllersFolder:WaitForChild("SanctuaryController"))
local MiniGameController = require(ControllersFolder:WaitForChild("MiniGameController"))
local TrophyController = require(ControllersFolder:WaitForChild("TrophyController"))

-- UI Modules
local UIFolder = script.Parent
local PlayerProfileUI = require(UIFolder:WaitForChild("PlayerProfileUI"))
local ProfileViewerUI = require(UIFolder:WaitForChild("ProfileViewerUI"))
local LeaderboardUI = require(UIFolder:WaitForChild("LeaderboardUI"))

local MainUI = {}

--[=[
	Initialize main UI
]=]
function MainUI:Initialize()
	-- Initialize trophy controller
	TrophyController:Initialize()
	
	-- Initialize profile UI
	PlayerProfileUI:Initialize()
	
	-- Initialize profile viewer UI
	ProfileViewerUI:Initialize()
	
	-- Initialize leaderboard UI
	LeaderboardUI:Initialize()
	
	-- Create main UI
	self:CreateMainHUD()
	
	-- Update currency display
	local currencyRemotes = ReplicatedStorage:WaitForChild("CurrencyRemotes")
	local currencyChanged = currencyRemotes:WaitForChild("CurrencyChanged")
	
	currencyChanged.OnClientEvent:Connect(function(newAmount, changeAmount)
		self:UpdateCurrencyDisplay(newAmount, changeAmount)
	end)
	
	print("🖥️ MainUI initialized")
end

--[=[
	Create main HUD
]=]
function MainUI:CreateMainHUD()
	local playerGui = Player:WaitForChild("PlayerGui")
	
	-- Main screen GUI
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "CatSanctuaryUI"
	screenGui.ResetOnSpawn = false
	screenGui.Parent = playerGui
	
	-- Top bar
	local topBar = Instance.new("Frame")
	topBar.Name = "TopBar"
	topBar.Size = UDim2.new(1, 0, 0, 60)
	topBar.Position = UDim2.new(0, 0, 0, 0)
	topBar.BackgroundColor3 = Config.UI.Colors.Primary
	topBar.BorderSizePixel = 0
	topBar.Parent = screenGui
	
	-- Currency display
	local currencyFrame = Instance.new("Frame")
	currencyFrame.Name = "CurrencyFrame"
	currencyFrame.Size = UDim2.new(0, 250, 0, 40)
	currencyFrame.Position = UDim2.new(0, 10, 0.5, -20)
	currencyFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	currencyFrame.Parent = topBar
	
	local currencyCorner = Instance.new("UICorner")
	currencyCorner.CornerRadius = UDim.new(0, 10)
	currencyCorner.Parent = currencyFrame
	
	local currencyLabel = Instance.new("TextLabel")
	currencyLabel.Name = "CurrencyLabel"
	currencyLabel.Size = UDim2.new(1, -20, 1, 0)
	currencyLabel.Position = UDim2.new(0, 10, 0, 0)
	currencyLabel.BackgroundTransparency = 1
	currencyLabel.Text = "💰 Charity: 0"
	currencyLabel.TextColor3 = Color3.new(1, 1, 1)
	currencyLabel.TextSize = 24
	currencyLabel.Font = Enum.Font.GothamBold
	currencyLabel.TextXAlignment = Enum.TextXAlignment.Left
	currencyLabel.Parent = currencyFrame
	
	-- Trophy display
	local trophyFrame = Instance.new("Frame")
	trophyFrame.Name = "TrophyFrame"
	trophyFrame.Size = UDim2.new(0, 200, 0, 40)
	trophyFrame.Position = UDim2.new(0, 270, 0.5, -20)
	trophyFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	trophyFrame.Parent = topBar
	
	local trophyCorner = Instance.new("UICorner")
	trophyCorner.CornerRadius = UDim.new(0, 10)
	trophyCorner.Parent = trophyFrame
	
	local trophyLabel = Instance.new("TextLabel")
	trophyLabel.Name = "TrophyLabel"
	trophyLabel.Size = UDim2.new(1, -20, 1, 0)
	trophyLabel.Position = UDim2.new(0, 10, 0, 0)
	trophyLabel.BackgroundTransparency = 1
	trophyLabel.Text = "🏆 0"
	trophyLabel.TextColor3 = Color3.new(1, 1, 1)
	trophyLabel.TextSize = 22
	trophyLabel.Font = Enum.Font.GothamBold
	trophyLabel.TextXAlignment = Enum.TextXAlignment.Left
	trophyLabel.Parent = trophyFrame
	
	-- League display
	local leagueFrame = Instance.new("Frame")
	leagueFrame.Name = "LeagueFrame"
	leagueFrame.Size = UDim2.new(0, 180, 0, 40)
	leagueFrame.Position = UDim2.new(0, 480, 0.5, -20)
	leagueFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	leagueFrame.Parent = topBar
	
	local leagueCorner = Instance.new("UICorner")
	leagueCorner.CornerRadius = UDim.new(0, 10)
	leagueCorner.Parent = leagueFrame
	
	local leagueLabel = Instance.new("TextLabel")
	leagueLabel.Name = "LeagueLabel"
	leagueLabel.Size = UDim2.new(1, -20, 1, 0)
	leagueLabel.Position = UDim2.new(0, 10, 0, 0)
	leagueLabel.BackgroundTransparency = 1
	leagueLabel.Text = "🥉 Rookie"
	leagueLabel.TextColor3 = Color3.fromRGB(150, 150, 150)
	leagueLabel.TextSize = 20
	leagueLabel.Font = Enum.Font.GothamBold
	leagueLabel.TextXAlignment = Enum.TextXAlignment.Left
	leagueLabel.Parent = leagueFrame
	
	-- Set trophy controller display elements
	TrophyController:SetTrophyDisplay(trophyLabel)
	TrophyController:SetLeagueDisplay(leagueLabel)
	
	-- Profile button
	local profileButton = Instance.new("TextButton")
	profileButton.Name = "ProfileButton"
	profileButton.Size = UDim2.new(0, 140, 0, 40)
	profileButton.Position = UDim2.new(1, -310, 0.5, -20)
	profileButton.BackgroundColor3 = Color3.fromRGB(100, 85, 255)
	profileButton.Text = "👤 Profile"
	profileButton.TextColor3 = Color3.new(1, 1, 1)
	profileButton.TextSize = 18
	profileButton.Font = Enum.Font.GothamBold
	profileButton.Parent = topBar
	
	local profileCorner = Instance.new("UICorner")
	profileCorner.CornerRadius = UDim.new(0, 10)
	profileCorner.Parent = profileButton
	
	profileButton.MouseButton1Click:Connect(function()
		self:ToggleProfile()
	end)
	
	-- Game title
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(0, 300, 1, 0)
	titleLabel.Position = UDim2.new(0.5, -150, 0, 0)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = "🐱 " .. Config.GAME_NAME
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextSize = 28
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.Parent = topBar
	
	-- Side panel button
	local menuButton = Instance.new("TextButton")
	menuButton.Name = "MenuButton"
	menuButton.Size = UDim2.new(0, 150, 0, 40)
	menuButton.Position = UDim2.new(1, -160, 0.5, -20)
	menuButton.BackgroundColor3 = Config.UI.Colors.Accent
	menuButton.Text = "📋 Menu"
	menuButton.TextColor3 = Color3.new(1, 1, 1)
	menuButton.TextSize = 20
	menuButton.Font = Enum.Font.GothamBold
	menuButton.Parent = topBar
	
	local menuCorner = Instance.new("UICorner")
	menuCorner.CornerRadius = UDim.new(0, 10)
	menuCorner.Parent = menuButton
	
	menuButton.MouseButton1Click:Connect(function()
		self:ToggleMenu()
	end)
	
	-- Create side menu (hidden by default)
	self:CreateSideMenu(screenGui)
	
	-- Quick action buttons
	self:CreateQuickActions(screenGui)
end

--[=[
	Create side menu
	@param parent ScreenGui
]=]
function MainUI:CreateSideMenu(parent)
	local menu = Instance.new("Frame")
	menu.Name = "SideMenu"
	menu.Size = UDim2.new(0, 300, 1, -60)
	menu.Position = UDim2.new(1, 0, 0, 60) -- Start off-screen
	menu.BackgroundColor3 = Config.UI.Colors.Secondary
	menu.BorderSizePixel = 0
	menu.Parent = parent
	
	-- List layout
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 10)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.Parent = menu
	
	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 20)
	padding.PaddingLeft = UDim.new(0, 10)
	padding.PaddingRight = UDim.new(0, 10)
	padding.Parent = menu
	
	-- Menu buttons
	local buttons = {
		{Text = "🐱 My Cats", Callback = function() self:OpenCatsMenu() end},
		{Text = "🏡 Build", Callback = function() self:OpenBuildMenu() end},
		{Text = "🎮 Mini-Games", Callback = function() self:OpenGameMenu() end},
		{Text = "🏆 Leaderboard", Callback = function() self:OpenLeaderboard() end},
		{Text = "⚙️ Settings", Callback = function() self:OpenSettings() end},
	}
	
	for _, buttonData in ipairs(buttons) do
		local button = Instance.new("TextButton")
		button.Size = UDim2.new(1, -20, 0, 50)
		button.BackgroundColor3 = Config.UI.Colors.Accent
		button.Text = buttonData.Text
		button.TextColor3 = Color3.new(1, 1, 1)
		button.TextSize = 20
		button.Font = Enum.Font.GothamBold
		button.Parent = menu
		
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, 10)
		corner.Parent = button
		
		button.MouseButton1Click:Connect(buttonData.Callback)
	end
end

--[=[
	Create quick action buttons
	@param parent ScreenGui
]=]
function MainUI:CreateQuickActions(parent)
	local actionsFrame = Instance.new("Frame")
	actionsFrame.Name = "QuickActions"
	actionsFrame.Size = UDim2.new(0, 80, 0, 300)
	actionsFrame.Position = UDim2.new(1, -90, 0.5, -150)
	actionsFrame.BackgroundTransparency = 1
	actionsFrame.Parent = parent
	
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 10)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.Parent = actionsFrame
	
	-- Quick buttons
	local quickButtons = {
		{Icon = "🐱", Tooltip = "Cats", Callback = function() self:OpenCatsMenu() end},
		{Icon = "🏠", Tooltip = "Build", Callback = function() self:OpenBuildMenu() end},
		{Icon = "🎮", Tooltip = "Play", Callback = function() self:OpenGameMenu() end},
	}
	
	for _, btnData in ipairs(quickButtons) do
		local button = Instance.new("TextButton")
		button.Size = UDim2.new(0, 70, 0, 70)
		button.BackgroundColor3 = Config.UI.Colors.Accent
		button.Text = btnData.Icon
		button.TextSize = 32
		button.Font = Enum.Font.GothamBold
		button.Parent = actionsFrame
		
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, 12)
		corner.Parent = button
		
		button.MouseButton1Click:Connect(btnData.Callback)
	end
end

--[=[
	Toggle side menu
]=]
function MainUI:ToggleMenu()
	local playerGui = Player.PlayerGui
	local ui = playerGui:FindFirstChild("CatSanctuaryUI")
	if not ui then return end
	
	local menu = ui:FindFirstChild("SideMenu")
	if not menu then return end
	
	local isOpen = menu.Position.X.Scale < 1
	
	local targetPos = isOpen and 
		UDim2.new(1, 0, 0, 60) or  -- Closed
		UDim2.new(1, -300, 0, 60)  -- Open
	
	menu:TweenPosition(targetPos, Enum.EasingDirection.Out, Enum.EasingStyle.Quad, 0.3, true)
end

--[=[
	Update currency display
	@param newAmount number
	@param changeAmount number
]=]
function MainUI:UpdateCurrencyDisplay(newAmount: number, changeAmount: number)
	local playerGui = Player.PlayerGui
	local ui = playerGui:FindFirstChild("CatSanctuaryUI")
	if not ui then return end
	
	local currencyLabel = ui:FindFirstChild("TopBar"):FindFirstChild("CurrencyFrame"):FindFirstChild("CurrencyLabel")
	if not currencyLabel then return end
	
	currencyLabel.Text = string.format("💰 Charity: %s", Utils.FormatNumber(newAmount))
	
	-- Show change notification
	if changeAmount ~= 0 then
		local changeText = changeAmount > 0 and 
			string.format("+%s", Utils.FormatNumber(changeAmount)) or
			Utils.FormatNumber(changeAmount)
		
		-- TODO: Animate change notification
	end
end

--[=[
	Open cats menu
]=]
function MainUI:OpenCatsMenu()
	print("Opening cats menu...")
	-- TODO: Implement full cats menu UI
end

--[=[
	Open build menu
]=]
function MainUI:OpenBuildMenu()
	print("Opening build menu...")
	-- TODO: Implement full build menu UI
end

--[=[
	Open game menu
]=]
function MainUI:OpenGameMenu()
	print("Opening game menu...")
	-- TODO: Implement full game menu UI
end

--[=[
	Open leaderboard
]=]
function MainUI:OpenLeaderboard()
	LeaderboardUI:Show()
end

--[=[
	Open settings
]=]
function MainUI:OpenSettings()
	print("Opening settings...")
	-- TODO: Implement settings UI
end

--[=[
	Toggle player profile UI
]=]
function MainUI:ToggleProfile()
	PlayerProfileUI:Toggle()
end

-- Initialize when script runs
MainUI:Initialize()

return MainUI
