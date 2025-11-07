--[[
	ProfileViewerUI.lua
	View other players' profiles
	Browse, search, and inspect other players
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/UI/ProfileViewerUI (LocalScript)
	COPY ORDER: #20
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local ProfileViewerUI = {}

-- Current viewing state
local currentViewingPlayer = nil
local viewerGui = nil
local contentFrame = nil
local currentTab = "Cats"

--[=[
	Initialize profile viewer
]=]
function ProfileViewerUI:Initialize()
	self:CreateViewerUI()
	self:SetupPlayerClickDetection()
	print("👥 ProfileViewerUI initialized")
end

--[=[
	Create viewer UI structure
]=]
function ProfileViewerUI:CreateViewerUI()
	local playerGui = Player:WaitForChild("PlayerGui")
	
	-- Main viewer GUI
	viewerGui = Instance.new("ScreenGui")
	viewerGui.Name = "ProfileViewerUI"
	viewerGui.ResetOnSpawn = false
	viewerGui.Enabled = false
	viewerGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	viewerGui.Parent = playerGui
	
	-- Background overlay
	local overlay = Instance.new("Frame")
	overlay.Name = "Overlay"
	overlay.Size = UDim2.new(1, 0, 1, 0)
	overlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	overlay.BackgroundTransparency = 0.3
	overlay.BorderSizePixel = 0
	overlay.Parent = viewerGui
	
	overlay.InputBegan:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			self:Hide()
		end
	end)
	
	-- Main window
	local viewerWindow = Instance.new("Frame")
	viewerWindow.Name = "ViewerWindow"
	viewerWindow.Size = UDim2.new(0, 1000, 0, 700)
	viewerWindow.Position = UDim2.new(0.5, 0, 0.5, 0)
	viewerWindow.AnchorPoint = Vector2.new(0.5, 0.5)
	viewerWindow.BackgroundColor3 = Config.UI.Colors.Primary
	viewerWindow.BorderSizePixel = 0
	viewerWindow.Parent = viewerGui
	
	local windowCorner = Instance.new("UICorner")
	windowCorner.CornerRadius = UDim.new(0, 12)
	windowCorner.Parent = viewerWindow
	
	-- Title bar
	local titleBar = Instance.new("Frame")
	titleBar.Name = "TitleBar"
	titleBar.Size = UDim2.new(1, 0, 0, 60)
	titleBar.BackgroundColor3 = Config.UI.Colors.Secondary
	titleBar.BorderSizePixel = 0
	titleBar.Parent = viewerWindow
	
	local titleCorner = Instance.new("UICorner")
	titleCorner.CornerRadius = UDim.new(0, 12)
	titleCorner.Parent = titleBar
	
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Name = "TitleLabel"
	titleLabel.Size = UDim2.new(1, -120, 1, 0)
	titleLabel.Position = UDim2.new(0, 20, 0, 0)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = "👤 Loading..."
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
	
	-- Tab bar
	local tabBar = Instance.new("Frame")
	tabBar.Name = "TabBar"
	tabBar.Size = UDim2.new(1, -40, 0, 50)
	tabBar.Position = UDim2.new(0, 20, 0, 70)
	tabBar.BackgroundTransparency = 1
	tabBar.Parent = viewerWindow
	
	local tabLayout = Instance.new("UIListLayout")
	tabLayout.FillDirection = Enum.FillDirection.Horizontal
	tabLayout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	tabLayout.Padding = UDim.new(0, 10)
	tabLayout.Parent = tabBar
	
	-- Create tabs
	local tabs = {"Cats", "Stats", "Trophies"}
	for _, tabName in ipairs(tabs) do
		self:CreateTab(tabBar, tabName)
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
	contentFrame.Parent = viewerWindow
	
	local contentCorner = Instance.new("UICorner")
	contentCorner.CornerRadius = UDim.new(0, 8)
	contentCorner.Parent = contentFrame
end

--[=[
	Create tab button
]=]
function ProfileViewerUI:CreateTab(parent, tabName: string)
	local tabButton = Instance.new("TextButton")
	tabButton.Name = tabName .. "Tab"
	tabButton.Size = UDim2.new(0, 150, 1, 0)
	tabButton.BackgroundColor3 = Config.UI.Colors.Secondary
	tabButton.Text = tabName
	tabButton.Font = Enum.Font.GothamBold
	tabButton.TextSize = 18
	tabButton.TextColor3 = Color3.new(1, 1, 1)
	tabButton.Parent = parent
	
	local tabCorner = Instance.new("UICorner")
	tabCorner.CornerRadius = UDim.new(0, 8)
	tabCorner.Parent = tabButton
	
	tabButton.MouseButton1Click:Connect(function()
		self:ShowTab(tabName)
	end)
end

--[=[
	Setup player click detection
]=]
function ProfileViewerUI:SetupPlayerClickDetection()
	local mouse = Player:GetMouse()
	
	mouse.Button1Down:Connect(function()
		local target = mouse.Target
		if not target then return end
		
		-- Check if clicked on a player character
		local character = target:FindFirstAncestorOfClass("Model")
		if not character then return end
		
		local clickedPlayer = Players:GetPlayerFromCharacter(character)
		if clickedPlayer and clickedPlayer ~= Player then
			-- Clicked on another player
			self:ViewPlayer(clickedPlayer)
		end
	end)
end

--[=[
	View a player's profile
	@param targetPlayer Player
]=]
function ProfileViewerUI:ViewPlayer(targetPlayer: Player)
	currentViewingPlayer = targetPlayer
	
	-- Update title
	local titleLabel = viewerGui.ViewerWindow.TitleBar.TitleLabel
	titleLabel.Text = string.format("👤 %s's Profile", targetPlayer.DisplayName)
	
	-- Show viewer
	viewerGui.Enabled = true
	
	-- Load default tab
	self:ShowTab("Cats")
end

--[=[
	View player by UserId (for leaderboard clicks)
	@param userId number
	@param displayName string
]=]
function ProfileViewerUI:ViewPlayerById(userId: number, displayName: string)
	-- Find player if online
	local targetPlayer = nil
	for _, player in ipairs(Players:GetPlayers()) do
		if player.UserId == userId then
			targetPlayer = player
			break
		end
	end
	
	if targetPlayer then
		self:ViewPlayer(targetPlayer)
	else
		-- Player offline - show message
		local titleLabel = viewerGui.ViewerWindow.TitleBar.TitleLabel
		titleLabel.Text = string.format("👤 %s (Offline)", displayName)
		
		viewerGui.Enabled = true
		self:ShowOfflineMessage()
	end
end

--[=[
	Show tab content
]=]
function ProfileViewerUI:ShowTab(tabName: string)
	currentTab = tabName
	
	if not currentViewingPlayer then return end
	
	-- Update tab colors
	local tabBar = viewerGui.ViewerWindow.TabBar
	for _, child in ipairs(tabBar:GetChildren()) do
		if child:IsA("TextButton") then
			if child.Name == tabName .. "Tab" then
				child.BackgroundColor3 = Config.UI.Colors.Accent
			else
				child.BackgroundColor3 = Config.UI.Colors.Secondary
			end
		end
	end
	
	-- Clear content
	for _, child in ipairs(contentFrame:GetChildren()) do
		if not child:IsA("UICorner") and not child:IsA("UIListLayout") and not child:IsA("UIGridLayout") then
			child:Destroy()
		end
	end
	
	-- Load content
	if tabName == "Cats" then
		self:ShowCatsTab()
	elseif tabName == "Stats" then
		self:ShowStatsTab()
	elseif tabName == "Trophies" then
		self:ShowTrophiesTab()
	end
end

--[=[
	Show cats tab
]=]
function ProfileViewerUI:ShowCatsTab()
	-- Request player's cats
	local profileRemotes = ReplicatedStorage:WaitForChild("ProfileRemotes")
	local getPlayerCats = profileRemotes:WaitForChild("GetPlayerCats")
	
	local cats = getPlayerCats:InvokeServer(currentViewingPlayer.UserId)
	
	if not cats then
		self:ShowError("Unable to load cats")
		return
	end
	
	-- Create grid layout
	local gridLayout = Instance.new("UIGridLayout")
	gridLayout.CellSize = UDim2.new(0, 280, 0, 250)
	gridLayout.CellPadding = UDim2.new(0, 15, 0, 15)
	gridLayout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
	gridLayout.Parent = contentFrame
	
	-- Sort by rarity
	table.sort(cats, function(a, b)
		local rarityA = Config.CAT_TYPES[a.Type].Rarity
		local rarityB = Config.CAT_TYPES[b.Type].Rarity
		if rarityA == rarityB then
			return a.Level > b.Level
		end
		return rarityA > rarityB
	end)
	
	-- Create cards (simplified view)
	for i, cat in ipairs(cats) do
		self:CreateSimpleCatCard(cat, i)
	end
	
	-- Update canvas
	local rows = math.ceil(#cats / 3)
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, (rows * 250) + ((rows - 1) * 15) + 20)
end

--[=[
	Create simplified cat card for viewing
]=]
function ProfileViewerUI:CreateSimpleCatCard(cat, index: number)
	local catType = Config.CAT_TYPES[cat.Type]
	
	local card = Instance.new("Frame")
	card.Name = "CatCard_" .. cat.Id
	card.BackgroundColor3 = Config.UI.Colors.Secondary
	card.BorderSizePixel = 0
	card.LayoutOrder = index
	card.Parent = contentFrame
	
	local cardCorner = Instance.new("UICorner")
	cardCorner.CornerRadius = UDim.new(0, 10)
	cardCorner.Parent = card
	
	-- Rarity border
	local rarityBorder = Instance.new("Frame")
	rarityBorder.Size = UDim2.new(1, 0, 0, 5)
	rarityBorder.BackgroundColor3 = self:GetRarityColor(catType.Rarity)
	rarityBorder.BorderSizePixel = 0
	rarityBorder.Parent = card
	
	local borderCorner = Instance.new("UICorner")
	borderCorner.CornerRadius = UDim.new(0, 10)
	borderCorner.Parent = rarityBorder
	
	-- Cat name
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(1, -20, 0, 30)
	nameLabel.Position = UDim2.new(0, 10, 0, 10)
	nameLabel.BackgroundTransparency = 1
	nameLabel.Text = string.format("%s %s", catType.Icon, cat.Name)
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.TextSize = 18
	nameLabel.TextColor3 = Color3.new(1, 1, 1)
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.Parent = card
	
	-- Level and rarity
	local levelLabel = Instance.new("TextLabel")
	levelLabel.Size = UDim2.new(1, -20, 0, 20)
	levelLabel.Position = UDim2.new(0, 10, 0, 40)
	levelLabel.BackgroundTransparency = 1
	levelLabel.Text = string.format("Level %d | %s", cat.Level, catType.Rarity)
	levelLabel.Font = Enum.Font.Gotham
	levelLabel.TextSize = 14
	levelLabel.TextColor3 = self:GetRarityColor(catType.Rarity)
	levelLabel.TextXAlignment = Enum.TextXAlignment.Left
	levelLabel.Parent = card
	
	-- Stats preview (compact)
	local statsLabel = Instance.new("TextLabel")
	statsLabel.Size = UDim2.new(1, -20, 0, 120)
	statsLabel.Position = UDim2.new(0, 10, 0, 70)
	statsLabel.BackgroundTransparency = 1
	statsLabel.Text = string.format(
		"💪 Strength: %d\n⚡ Speed: %d\n🎯 Agility: %d\n💖 Cuteness: %d\n\nTotal Power: %d",
		cat.Stats.Strength,
		cat.Stats.Speed,
		cat.Stats.Agility,
		cat.Stats.Cuteness,
		cat.Stats.Strength + cat.Stats.Speed + cat.Stats.Agility + cat.Stats.Cuteness
	)
	statsLabel.Font = Enum.Font.Gotham
	statsLabel.TextSize = 13
	statsLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	statsLabel.TextXAlignment = Enum.TextXAlignment.Left
	statsLabel.TextYAlignment = Enum.TextYAlignment.Top
	statsLabel.Parent = card
	
	-- Friendship
	local friendshipLabel = Instance.new("TextLabel")
	friendshipLabel.Size = UDim2.new(1, -20, 0, 25)
	friendshipLabel.Position = UDim2.new(0, 10, 1, -35)
	friendshipLabel.BackgroundTransparency = 1
	friendshipLabel.Text = string.format("💝 Friendship: %d%%", cat.Friendship)
	friendshipLabel.Font = Enum.Font.Gotham
	friendshipLabel.TextSize = 12
	friendshipLabel.TextColor3 = Color3.fromRGB(255, 170, 0)
	friendshipLabel.TextXAlignment = Enum.TextXAlignment.Left
	friendshipLabel.Parent = card
end

--[=[
	Show stats tab
]=]
function ProfileViewerUI:ShowStatsTab()
	local profileRemotes = ReplicatedStorage:WaitForChild("ProfileRemotes")
	local getPlayerStats = profileRemotes:WaitForChild("GetPlayerStats")
	
	local stats = getPlayerStats:InvokeServer(currentViewingPlayer.UserId)
	
	if not stats then
		self:ShowError("Unable to load stats")
		return
	end
	
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 15)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Trophy stats
	self:CreateStatSection("Trophy Stats", {
		{"Current Trophies", Utils.FormatTrophies(stats.Trophies or 0)},
		{"Highest Trophies", Utils.FormatTrophies(stats.HighestTrophies or 0)},
		{"Current League", stats.CurrentLeague or "Rookie"},
		{"Win Streak", string.format("🔥 %d", stats.WinStreak or 0)}
	}, 1)
	
	-- Game stats
	local winRate = stats.GamesPlayed > 0 
		and (stats.GamesWon / stats.GamesPlayed * 100) 
		or 0
	
	self:CreateStatSection("Game Statistics", {
		{"Games Played", Utils.FormatNumber(stats.GamesPlayed)},
		{"Games Won", Utils.FormatNumber(stats.GamesWon)},
		{"Win Rate", string.format("%.1f%%", winRate)},
		{"Time Played", Utils.FormatTime(stats.TimePlayed)}
	}, 2)
	
	-- Collection
	self:CreateStatSection("Collection", {
		{"Cats Rescued", Utils.FormatNumber(stats.CatsRescued)},
		{"Highest Cat Level", Utils.FormatNumber(stats.HighestLevel or 0)},
		{"Buildings Owned", Utils.FormatNumber(stats.BuildingsCount or 0)},
		{"Sanctuary Material", stats.Material or "Wood"}
	}, 3)
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 600)
end

--[=[
	Show trophies tab with rankings
]=]
function ProfileViewerUI:ShowTrophiesTab()
	local profileRemotes = ReplicatedStorage:WaitForChild("ProfileRemotes")
	local getPlayerTrophyInfo = profileRemotes:WaitForChild("GetPlayerTrophyInfo")
	
	local trophyInfo = getPlayerTrophyInfo:InvokeServer(currentViewingPlayer.UserId)
	
	if not trophyInfo then
		self:ShowError("Unable to load trophy info")
		return
	end
	
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 15)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Trophy overview
	local overviewFrame = Instance.new("Frame")
	overviewFrame.Name = "Overview"
	overviewFrame.Size = UDim2.new(1, -20, 0, 200)
	overviewFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	overviewFrame.BorderSizePixel = 0
	overviewFrame.LayoutOrder = 1
	overviewFrame.Parent = contentFrame
	
	local overviewCorner = Instance.new("UICorner")
	overviewCorner.CornerRadius = UDim.new(0, 10)
	overviewCorner.Parent = overviewFrame
	
	local league = Utils.GetLeagueFromTrophies(trophyInfo.Trophies)
	
	-- League icon (large)
	local leagueIcon = Instance.new("TextLabel")
	leagueIcon.Size = UDim2.new(1, 0, 0, 80)
	leagueIcon.Position = UDim2.new(0, 0, 0, 20)
	leagueIcon.BackgroundTransparency = 1
	leagueIcon.Text = league and league.Icon or "🥉"
	leagueIcon.Font = Enum.Font.Gotham
	leagueIcon.TextSize = 64
	leagueIcon.Parent = overviewFrame
	
	-- League name
	local leagueName = Instance.new("TextLabel")
	leagueName.Size = UDim2.new(1, 0, 0, 30)
	leagueName.Position = UDim2.new(0, 0, 0, 100)
	leagueName.BackgroundTransparency = 1
	leagueName.Text = league and league.Name or "Rookie"
	leagueName.Font = Enum.Font.GothamBold
	leagueName.TextSize = 24
	leagueName.TextColor3 = league and league.Color or Color3.fromRGB(150, 150, 150)
	leagueName.Parent = overviewFrame
	
	-- Trophy count
	local trophyCount = Instance.new("TextLabel")
	trophyCount.Size = UDim2.new(1, 0, 0, 30)
	trophyCount.Position = UDim2.new(0, 0, 0, 135)
	trophyCount.BackgroundTransparency = 1
	trophyCount.Text = Utils.FormatTrophies(trophyInfo.Trophies)
	trophyCount.Font = Enum.Font.GothamBold
	trophyCount.TextSize = 28
	trophyCount.TextColor3 = Color3.new(1, 1, 1)
	trophyCount.Parent = overviewFrame
	
	-- Global rank
	local rankLabel = Instance.new("TextLabel")
	rankLabel.Size = UDim2.new(1, 0, 0, 25)
	rankLabel.Position = UDim2.new(0, 0, 0, 170)
	rankLabel.BackgroundTransparency = 1
	rankLabel.Text = string.format("Global Rank: #%d", trophyInfo.GlobalRank or 0)
	rankLabel.Font = Enum.Font.Gotham
	rankLabel.TextSize = 16
	rankLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	rankLabel.Parent = overviewFrame
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 250)
end

--[=[
	Create stat section
]=]
function ProfileViewerUI:CreateStatSection(title: string, stats: {{string}}, order: number)
	local section = Instance.new("Frame")
	section.Name = title
	section.Size = UDim2.new(1, -20, 0, 180)
	section.BackgroundColor3 = Config.UI.Colors.Secondary
	section.BorderSizePixel = 0
	section.LayoutOrder = order
	section.Parent = contentFrame
	
	local sectionCorner = Instance.new("UICorner")
	sectionCorner.CornerRadius = UDim.new(0, 10)
	sectionCorner.Parent = section
	
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(1, -20, 0, 40)
	titleLabel.Position = UDim2.new(0, 10, 0, 10)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = title
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 20
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = section
	
	for i, stat in ipairs(stats) do
		local statFrame = Instance.new("Frame")
		statFrame.Size = UDim2.new(0.48, 0, 0, 50)
		statFrame.Position = UDim2.new(
			(i - 1) % 2 == 0 and 0.02 or 0.5,
			0,
			0.3 + (math.floor((i - 1) / 2) * 0.35),
			0
		)
		statFrame.BackgroundColor3 = Config.UI.Colors.Background
		statFrame.BorderSizePixel = 0
		statFrame.Parent = section
		
		local statCorner = Instance.new("UICorner")
		statCorner.CornerRadius = UDim.new(0, 6)
		statCorner.Parent = statFrame
		
		local statName = Instance.new("TextLabel")
		statName.Size = UDim2.new(1, -10, 0, 20)
		statName.Position = UDim2.new(0, 5, 0, 5)
		statName.BackgroundTransparency = 1
		statName.Text = stat[1]
		statName.Font = Enum.Font.Gotham
		statName.TextSize = 13
		statName.TextColor3 = Color3.fromRGB(170, 170, 170)
		statName.TextXAlignment = Enum.TextXAlignment.Left
		statName.Parent = statFrame
		
		local statValue = Instance.new("TextLabel")
		statValue.Size = UDim2.new(1, -10, 0, 22)
		statValue.Position = UDim2.new(0, 5, 0, 23)
		statValue.BackgroundTransparency = 1
		statValue.Text = stat[2]
		statValue.Font = Enum.Font.GothamBold
		statValue.TextSize = 18
		statValue.TextColor3 = Color3.new(1, 1, 1)
		statValue.TextXAlignment = Enum.TextXAlignment.Left
		statValue.Parent = statFrame
	end
end

--[=[
	Show error message
]=]
function ProfileViewerUI:ShowError(message: string)
	local errorLabel = Instance.new("TextLabel")
	errorLabel.Size = UDim2.new(1, -40, 0, 100)
	errorLabel.Position = UDim2.new(0, 20, 0, 20)
	errorLabel.BackgroundTransparency = 1
	errorLabel.Text = "⚠️ " .. message
	errorLabel.Font = Enum.Font.GothamBold
	errorLabel.TextSize = 20
	errorLabel.TextColor3 = Color3.fromRGB(255, 85, 85)
	errorLabel.Parent = contentFrame
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 150)
end

--[=[
	Show offline message
]=]
function ProfileViewerUI:ShowOfflineMessage()
	for _, child in ipairs(contentFrame:GetChildren()) do
		if not child:IsA("UICorner") then
			child:Destroy()
		end
	end
	
	local offlineLabel = Instance.new("TextLabel")
	offlineLabel.Size = UDim2.new(1, -40, 0, 100)
	offlineLabel.Position = UDim2.new(0, 20, 0, 20)
	offlineLabel.BackgroundTransparency = 1
	offlineLabel.Text = "This player is currently offline.\nProfile data not available."
	offlineLabel.Font = Enum.Font.Gotham
	offlineLabel.TextSize = 18
	offlineLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	offlineLabel.Parent = contentFrame
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 150)
end

--[=[
	Get rarity color
]=]
function ProfileViewerUI:GetRarityColor(rarity: string): Color3
	local colors = {
		Common = Color3.fromRGB(150, 150, 150),
		Uncommon = Color3.fromRGB(85, 255, 127),
		Rare = Color3.fromRGB(0, 170, 255),
		["Ultra Rare"] = Color3.fromRGB(170, 85, 255),
		Legendary = Color3.fromRGB(255, 215, 0)
	}
	return colors[rarity] or Color3.fromRGB(255, 255, 255)
end

--[=[
	Show viewer
]=]
function ProfileViewerUI:Show()
	if viewerGui then
		viewerGui.Enabled = true
	end
end

--[=[
	Hide viewer
]=]
function ProfileViewerUI:Hide()
	if viewerGui then
		viewerGui.Enabled = false
		currentViewingPlayer = nil
	end
end

return ProfileViewerUI
