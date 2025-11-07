--[[
	LeaderboardUI.lua
	Display leaderboards with profile viewing
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/UI/LeaderboardUI (LocalScript)
	COPY ORDER: #21
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

-- UI Modules
local UIFolder = script.Parent
local ProfileViewerUI = require(UIFolder:WaitForChild("ProfileViewerUI"))

local LeaderboardUI = {}

-- UI references
local leaderboardGui = nil
local contentFrame = nil
local currentCategory = "Trophies"

--[=[
	Initialize leaderboard UI
]=]
function LeaderboardUI:Initialize()
	self:CreateLeaderboardUI()
	print("🏆 LeaderboardUI initialized")
end

--[=[
	Create leaderboard UI
]=]
function LeaderboardUI:CreateLeaderboardUI()
	local playerGui = Player:WaitForChild("PlayerGui")
	
	leaderboardGui = Instance.new("ScreenGui")
	leaderboardGui.Name = "LeaderboardUI"
	leaderboardGui.ResetOnSpawn = false
	leaderboardGui.Enabled = false
	leaderboardGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	leaderboardGui.Parent = playerGui
	
	-- Overlay
	local overlay = Instance.new("Frame")
	overlay.Name = "Overlay"
	overlay.Size = UDim2.new(1, 0, 1, 0)
	overlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	overlay.BackgroundTransparency = 0.3
	overlay.BorderSizePixel = 0
	overlay.Parent = leaderboardGui
	
	overlay.InputBegan:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			self:Hide()
		end
	end)
	
	-- Main window
	local window = Instance.new("Frame")
	window.Name = "Window"
	window.Size = UDim2.new(0, 800, 0, 650)
	window.Position = UDim2.new(0.5, 0, 0.5, 0)
	window.AnchorPoint = Vector2.new(0.5, 0.5)
	window.BackgroundColor3 = Config.UI.Colors.Primary
	window.BorderSizePixel = 0
	window.Parent = leaderboardGui
	
	local windowCorner = Instance.new("UICorner")
	windowCorner.CornerRadius = UDim.new(0, 12)
	windowCorner.Parent = window
	
	-- Title bar
	local titleBar = Instance.new("Frame")
	titleBar.Name = "TitleBar"
	titleBar.Size = UDim2.new(1, 0, 0, 60)
	titleBar.BackgroundColor3 = Config.UI.Colors.Secondary
	titleBar.BorderSizePixel = 0
	titleBar.Parent = window
	
	local titleCorner = Instance.new("UICorner")
	titleCorner.CornerRadius = UDim.new(0, 12)
	titleCorner.Parent = titleBar
	
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(1, -120, 1, 0)
	titleLabel.Position = UDim2.new(0, 20, 0, 0)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = "🏆 Global Leaderboards"
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 28
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = titleBar
	
	-- Close button
	local closeButton = Instance.new("TextButton")
	closeButton.Name = "CloseButton"
	closeButton.Size = UDim2.new(0, 40, 0, 40)
	closeButton.Position = UDim2.new(1, -50, 0.5, -20)
	closeButton.BackgroundColor3 = Color3.fromRGB(255, 85, 85)
	closeButton.Text = "✕"
	closeButton.Font = Enum.Font.GothamBold
	closeButton.TextSize = 24
	closeButton.TextColor3 = Color3.new(1, 1, 1)
	closeButton.Parent = titleBar
	
	local closeCorner = Instance.new("UICorner")
	closeCorner.CornerRadius = UDim.new(0, 8)
	closeCorner.Parent = closeButton
	
	closeButton.MouseButton1Click:Connect(function()
		self:Hide()
	end)
	
	-- Category tabs
	local tabBar = Instance.new("Frame")
	tabBar.Name = "TabBar"
	tabBar.Size = UDim2.new(1, -40, 0, 50)
	tabBar.Position = UDim2.new(0, 20, 0, 70)
	tabBar.BackgroundTransparency = 1
	tabBar.Parent = window
	
	local tabLayout = Instance.new("UIListLayout")
	tabLayout.FillDirection = Enum.FillDirection.Horizontal
	tabLayout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	tabLayout.Padding = UDim.new(0, 8)
	tabLayout.Parent = tabBar
	
	-- Create category tabs
	for _, category in ipairs(Config.LEADERBOARDS.Categories) do
		self:CreateCategoryTab(tabBar, category)
	end
	
	-- Content frame
	contentFrame = Instance.new("ScrollingFrame")
	contentFrame.Name = "ContentFrame"
	contentFrame.Size = UDim2.new(1, -40, 1, -150)
	contentFrame.Position = UDim2.new(0, 20, 0, 130)
	contentFrame.BackgroundColor3 = Config.UI.Colors.Background
	contentFrame.BorderSizePixel = 0
	contentFrame.ScrollBarThickness = 8
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 0)
	contentFrame.Parent = window
	
	local contentCorner = Instance.new("UICorner")
	contentCorner.CornerRadius = UDim.new(0, 8)
	contentCorner.Parent = contentFrame
end

--[=[
	Create category tab
]=]
function LeaderboardUI:CreateCategoryTab(parent, category: string)
	local tabButton = Instance.new("TextButton")
	tabButton.Name = category .. "Tab"
	tabButton.Size = UDim2.new(0, 140, 1, 0)
	tabButton.BackgroundColor3 = Config.UI.Colors.Secondary
	tabButton.Text = category
	tabButton.Font = Enum.Font.GothamBold
	tabButton.TextSize = 16
	tabButton.TextColor3 = Color3.new(1, 1, 1)
	tabButton.Parent = parent
	
	local tabCorner = Instance.new("UICorner")
	tabCorner.CornerRadius = UDim.new(0, 8)
	tabCorner.Parent = tabButton
	
	tabButton.MouseButton1Click:Connect(function()
		self:ShowCategory(category)
	end)
end

--[=[
	Show category
]=]
function LeaderboardUI:ShowCategory(category: string)
	currentCategory = category
	
	-- Update tab colors
	local tabBar = leaderboardGui.Window.TabBar
	for _, child in ipairs(tabBar:GetChildren()) do
		if child:IsA("TextButton") then
			if child.Name == category .. "Tab" then
				child.BackgroundColor3 = Config.UI.Colors.Accent
			else
				child.BackgroundColor3 = Config.UI.Colors.Secondary
			end
		end
	end
	
	-- Clear content
	for _, child in ipairs(contentFrame:GetChildren()) do
		if not child:IsA("UICorner") and not child:IsA("UIListLayout") then
			child:Destroy()
		end
	end
	
	-- Load leaderboard data
	self:LoadLeaderboardData(category)
end

--[=[
	Load leaderboard data
]=]
function LeaderboardUI:LoadLeaderboardData(category: string)
	local leaderboardRemotes = ReplicatedStorage:WaitForChild("LeaderboardRemotes")
	local getLeaderboard = leaderboardRemotes:WaitForChild("GetLeaderboard")
	
	local data = getLeaderboard:InvokeServer(category, false)
	
	if not data or #data == 0 then
		self:ShowEmptyMessage()
		return
	end
	
	-- Create list layout
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 5)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Create entries
	for i, entry in ipairs(data) do
		self:CreateLeaderboardEntry(entry, category, i)
	end
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, (#data * 55) + (#data * 5) + 10)
end

--[=[
	Create leaderboard entry
]=]
function LeaderboardUI:CreateLeaderboardEntry(entry, category: string, index: number)
	local entryFrame = Instance.new("Frame")
	entryFrame.Name = "Entry_" .. entry.UserId
	entryFrame.Size = UDim2.new(1, -20, 0, 50)
	entryFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	entryFrame.BorderSizePixel = 0
	entryFrame.LayoutOrder = index
	entryFrame.Parent = contentFrame
	
	local entryCorner = Instance.new("UICorner")
	entryCorner.CornerRadius = UDim.new(0, 8)
	entryCorner.Parent = entryFrame
	
	-- Highlight player's own entry
	if entry.UserId == Player.UserId then
		entryFrame.BackgroundColor3 = Color3.fromRGB(50, 120, 50)
	end
	
	-- Rank
	local rankLabel = Instance.new("TextLabel")
	rankLabel.Size = UDim2.new(0, 60, 1, 0)
	rankLabel.Position = UDim2.new(0, 10, 0, 0)
	rankLabel.BackgroundTransparency = 1
	rankLabel.Text = self:GetRankText(entry.Rank)
	rankLabel.Font = Enum.Font.GothamBold
	rankLabel.TextSize = 20
	rankLabel.TextColor3 = self:GetRankColor(entry.Rank)
	rankLabel.Parent = entryFrame
	
	-- Player name
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(0, 400, 1, 0)
	nameLabel.Position = UDim2.new(0, 80, 0, 0)
	nameLabel.BackgroundTransparency = 1
	nameLabel.Text = entry.DisplayName
	nameLabel.Font = Enum.Font.Gotham
	nameLabel.TextSize = 18
	nameLabel.TextColor3 = Color3.new(1, 1, 1)
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.Parent = entryFrame
	
	-- Value
	local valueLabel = Instance.new("TextLabel")
	valueLabel.Size = UDim2.new(0, 200, 1, 0)
	valueLabel.Position = UDim2.new(0, 490, 0, 0)
	valueLabel.BackgroundTransparency = 1
	valueLabel.Text = self:FormatValue(entry.Value, category)
	valueLabel.Font = Enum.Font.GothamBold
	valueLabel.TextSize = 18
	valueLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
	valueLabel.TextXAlignment = Enum.TextXAlignment.Right
	valueLabel.Parent = entryFrame
	
	-- View profile button
	local viewButton = Instance.new("TextButton")
	viewButton.Size = UDim2.new(0, 40, 0, 30)
	viewButton.Position = UDim2.new(1, -50, 0.5, -15)
	viewButton.BackgroundColor3 = Color3.fromRGB(100, 85, 255)
	viewButton.Text = "👤"
	viewButton.Font = Enum.Font.GothamBold
	viewButton.TextSize = 18
	viewButton.TextColor3 = Color3.new(1, 1, 1)
	viewButton.Parent = entryFrame
	
	local viewCorner = Instance.new("UICorner")
	viewCorner.CornerRadius = UDim.new(0, 6)
	viewCorner.Parent = viewButton
	
	viewButton.MouseButton1Click:Connect(function()
		ProfileViewerUI:ViewPlayerById(entry.UserId, entry.DisplayName)
	end)
end

--[=[
	Get rank display text
]=]
function LeaderboardUI:GetRankText(rank: number): string
	if rank == 1 then
		return "🥇"
	elseif rank == 2 then
		return "🥈"
	elseif rank == 3 then
		return "🥉"
	else
		return string.format("#%d", rank)
	end
end

--[=[
	Get rank color
]=]
function LeaderboardUI:GetRankColor(rank: number): Color3
	if rank == 1 then
		return Color3.fromRGB(255, 215, 0)
	elseif rank == 2 then
		return Color3.fromRGB(192, 192, 192)
	elseif rank == 3 then
		return Color3.fromRGB(205, 127, 50)
	else
		return Color3.fromRGB(200, 200, 200)
	end
end

--[=[
	Format value based on category
]=]
function LeaderboardUI:FormatValue(value: number, category: string): string
	if category == "Trophies" then
		return Utils.FormatTrophies(value)
	elseif category == "TotalCurrency" then
		return string.format("$%s", Utils.FormatNumber(value))
	else
		return Utils.FormatNumber(value)
	end
end

--[=[
	Show empty message
]=]
function LeaderboardUI:ShowEmptyMessage()
	local emptyLabel = Instance.new("TextLabel")
	emptyLabel.Size = UDim2.new(1, -40, 0, 100)
	emptyLabel.Position = UDim2.new(0, 20, 0, 20)
	emptyLabel.BackgroundTransparency = 1
	emptyLabel.Text = "No leaderboard data yet.\nPlay some games to appear here!"
	emptyLabel.Font = Enum.Font.Gotham
	emptyLabel.TextSize = 18
	emptyLabel.TextColor3 = Color3.fromRGB(150, 150, 150)
	emptyLabel.Parent = contentFrame
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 150)
end

--[=[
	Show leaderboard
]=]
function LeaderboardUI:Show()
	if leaderboardGui then
		leaderboardGui.Enabled = true
		self:ShowCategory(currentCategory)
	end
end

--[=[
	Hide leaderboard
]=]
function LeaderboardUI:Hide()
	if leaderboardGui then
		leaderboardGui.Enabled = false
	end
end

--[=[
	Toggle leaderboard
]=]
function LeaderboardUI:Toggle()
	if leaderboardGui then
		if leaderboardGui.Enabled then
			self:Hide()
		else
			self:Show()
		end
	end
end

return LeaderboardUI
