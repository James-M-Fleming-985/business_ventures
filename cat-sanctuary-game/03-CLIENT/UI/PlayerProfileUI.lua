--[[
	PlayerProfileUI.lua
	Player profile and collection viewer
	Shows cats, stats, inventory, achievements, and progress
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/UI/PlayerProfileUI (LocalScript)
	COPY ORDER: #16
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local PlayerProfileUI = {}

-- Current tab
local currentTab = "Cats"

-- UI References
local profileGui = nil
local contentFrame = nil

--[=[
	Initialize player profile UI
]=]
function PlayerProfileUI:Initialize()
	self:CreateProfileUI()
	print("📊 PlayerProfileUI initialized")
end

--[=[
	Create main profile UI structure
]=]
function PlayerProfileUI:CreateProfileUI()
	local playerGui = Player:WaitForChild("PlayerGui")
	
	-- Main profile GUI
	profileGui = Instance.new("ScreenGui")
	profileGui.Name = "PlayerProfileUI"
	profileGui.ResetOnSpawn = false
	profileGui.Enabled = false -- Hidden by default
	profileGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	profileGui.Parent = playerGui
	
	-- Background overlay
	local overlay = Instance.new("Frame")
	overlay.Name = "Overlay"
	overlay.Size = UDim2.new(1, 0, 1, 0)
	overlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	overlay.BackgroundTransparency = 0.3
	overlay.BorderSizePixel = 0
	overlay.Parent = profileGui
	
	-- Main profile window
	local profileWindow = Instance.new("Frame")
	profileWindow.Name = "ProfileWindow"
	profileWindow.Size = UDim2.new(0, 1000, 0, 700)
	profileWindow.Position = UDim2.new(0.5, 0, 0.5, 0)
	profileWindow.AnchorPoint = Vector2.new(0.5, 0.5)
	profileWindow.BackgroundColor3 = Config.UI.Colors.Primary
	profileWindow.BorderSizePixel = 0
	profileWindow.Parent = profileGui
	
	local windowCorner = Instance.new("UICorner")
	windowCorner.CornerRadius = UDim.new(0, 12)
	windowCorner.Parent = profileWindow
	
	-- Title bar
	local titleBar = Instance.new("Frame")
	titleBar.Name = "TitleBar"
	titleBar.Size = UDim2.new(1, 0, 0, 60)
	titleBar.BackgroundColor3 = Config.UI.Colors.Secondary
	titleBar.BorderSizePixel = 0
	titleBar.Parent = profileWindow
	
	local titleCorner = Instance.new("UICorner")
	titleCorner.CornerRadius = UDim.new(0, 12)
	titleCorner.Parent = titleBar
	
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(1, -120, 1, 0)
	titleLabel.Position = UDim2.new(0, 20, 0, 0)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = string.format("👤 %s's Profile", Player.DisplayName)
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
	
	-- Tab buttons
	local tabBar = Instance.new("Frame")
	tabBar.Name = "TabBar"
	tabBar.Size = UDim2.new(1, -40, 0, 50)
	tabBar.Position = UDim2.new(0, 20, 0, 70)
	tabBar.BackgroundTransparency = 1
	tabBar.Parent = profileWindow
	
	local tabLayout = Instance.new("UIListLayout")
	tabLayout.FillDirection = Enum.FillDirection.Horizontal
	tabLayout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	tabLayout.Padding = UDim.new(0, 10)
	tabLayout.Parent = tabBar
	
	-- Create tabs
	local tabs = {"Cats", "Stats", "Inventory", "Achievements"}
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
	contentFrame.Parent = profileWindow
	
	local contentCorner = Instance.new("UICorner")
	contentCorner.CornerRadius = UDim.new(0, 8)
	contentCorner.Parent = contentFrame
	
	-- Show initial tab
	self:ShowTab("Cats")
end

--[=[
	Create tab button
	@param parent Frame
	@param tabName string
]=]
function PlayerProfileUI:CreateTab(parent, tabName: string)
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
	
	return tabButton
end

--[=[
	Show specific tab
	@param tabName string
]=]
function PlayerProfileUI:ShowTab(tabName: string)
	currentTab = tabName
	
	-- Update tab button colors
	local tabBar = profileGui.ProfileWindow.TabBar
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
		if not child:IsA("UICorner") and not child:IsA("UIListLayout") then
			child:Destroy()
		end
	end
	
	-- Load tab content
	if tabName == "Cats" then
		self:ShowCatsTab()
	elseif tabName == "Stats" then
		self:ShowStatsTab()
	elseif tabName == "Inventory" then
		self:ShowInventoryTab()
	elseif tabName == "Achievements" then
		self:ShowAchievementsTab()
	end
end

--[=[
	Show cats collection tab
]=]
function PlayerProfileUI:ShowCatsTab()
	-- Get player's cats
	local catRemotes = ReplicatedStorage:WaitForChild("CatRemotes")
	local getAllCats = catRemotes:WaitForChild("GetAllCats")
	
	local cats = getAllCats:InvokeServer()
	
	-- Create grid layout
	local gridLayout = Instance.new("UIGridLayout")
	gridLayout.CellSize = UDim2.new(0, 280, 0, 320)
	gridLayout.CellPadding = UDim2.new(0, 15, 0, 15)
	gridLayout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
	gridLayout.Parent = contentFrame
	
	-- Sort cats by rarity then level
	table.sort(cats, function(a, b)
		local rarityA = Config.CAT_TYPES[a.Type].Rarity
		local rarityB = Config.CAT_TYPES[b.Type].Rarity
		if rarityA == rarityB then
			return a.Level > b.Level
		end
		return rarityA > rarityB
	end)
	
	-- Create cat cards
	for i, cat in ipairs(cats) do
		self:CreateCatCard(cat, i)
	end
	
	-- Update canvas size
	local rows = math.ceil(#cats / 3)
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, (rows * 320) + ((rows - 1) * 15) + 20)
	
	-- Summary at top
	self:CreateCatSummary(cats)
end

--[=[
	Create cat summary section
	@param cats table
]=]
function PlayerProfileUI:CreateCatSummary(cats)
	local summaryFrame = Instance.new("Frame")
	summaryFrame.Name = "Summary"
	summaryFrame.Size = UDim2.new(1, -20, 0, 100)
	summaryFrame.Position = UDim2.new(0, 10, 0, 10)
	summaryFrame.BackgroundColor3 = Config.UI.Colors.Secondary
	summaryFrame.BorderSizePixel = 0
	summaryFrame.ZIndex = 2
	summaryFrame.LayoutOrder = -1
	summaryFrame.Parent = contentFrame
	
	local summaryCorner = Instance.new("UICorner")
	summaryCorner.CornerRadius = UDim.new(0, 8)
	summaryCorner.Parent = summaryFrame
	
	-- Count by rarity
	local rarityCounts = {Common = 0, Uncommon = 0, Rare = 0, ["Ultra Rare"] = 0, Legendary = 0}
	for _, cat in ipairs(cats) do
		local rarity = Config.CAT_TYPES[cat.Type].Rarity
		rarityCounts[rarity] = (rarityCounts[rarity] or 0) + 1
	end
	
	local summaryText = string.format(
		"📊 Collection: %d Cats Total\n" ..
		"⚪ Common: %d | 🟢 Uncommon: %d | 🔵 Rare: %d | 🟣 Ultra Rare: %d | 🟡 Legendary: %d",
		#cats,
		rarityCounts.Common,
		rarityCounts.Uncommon,
		rarityCounts.Rare,
		rarityCounts["Ultra Rare"],
		rarityCounts.Legendary
	)
	
	local summaryLabel = Instance.new("TextLabel")
	summaryLabel.Size = UDim2.new(1, -20, 1, -20)
	summaryLabel.Position = UDim2.new(0, 10, 0, 10)
	summaryLabel.BackgroundTransparency = 1
	summaryLabel.Text = summaryText
	summaryLabel.Font = Enum.Font.Gotham
	summaryLabel.TextSize = 16
	summaryLabel.TextColor3 = Color3.new(1, 1, 1)
	summaryLabel.TextXAlignment = Enum.TextXAlignment.Left
	summaryLabel.TextYAlignment = Enum.TextYAlignment.Top
	summaryLabel.Parent = summaryFrame
end

--[=[
	Create cat card
	@param cat CatData
	@param index number
]=]
function PlayerProfileUI:CreateCatCard(cat, index: number)
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
	rarityBorder.Position = UDim2.new(0, 0, 0, 0)
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
	
	-- Stats section
	local statsFrame = Instance.new("Frame")
	statsFrame.Size = UDim2.new(1, -20, 0, 120)
	statsFrame.Position = UDim2.new(0, 10, 0, 70)
	statsFrame.BackgroundColor3 = Config.UI.Colors.Background
	statsFrame.BorderSizePixel = 0
	statsFrame.Parent = card
	
	local statsCorner = Instance.new("UICorner")
	statsCorner.CornerRadius = UDim.new(0, 6)
	statsCorner.Parent = statsFrame
	
	-- Display stats
	local statsList = {
		{"💪 Strength", cat.Stats.Strength},
		{"⚡ Speed", cat.Stats.Speed},
		{"🎯 Agility", cat.Stats.Agility},
		{"💖 Cuteness", cat.Stats.Cuteness}
	}
	
	for i, statData in ipairs(statsList) do
		local statLabel = Instance.new("TextLabel")
		statLabel.Size = UDim2.new(0.5, -15, 0, 25)
		statLabel.Position = UDim2.new(
			(i - 1) % 2 == 0 and 0 or 0.5,
			(i - 1) % 2 == 0 and 5 or 5,
			math.floor((i - 1) / 2) * 0.5,
			5
		)
		statLabel.BackgroundTransparency = 1
		statLabel.Text = string.format("%s: %d", statData[1], statData[2])
		statLabel.Font = Enum.Font.Gotham
		statLabel.TextSize = 13
		statLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
		statLabel.TextXAlignment = Enum.TextXAlignment.Left
		statLabel.Parent = statsFrame
	end
	
	-- Skills section
	local skillsLabel = Instance.new("TextLabel")
	skillsLabel.Size = UDim2.new(1, -20, 0, 80)
	skillsLabel.Position = UDim2.new(0, 10, 0, 200)
	skillsLabel.BackgroundTransparency = 1
	skillsLabel.Font = Enum.Font.Gotham
	skillsLabel.TextSize = 12
	skillsLabel.TextColor3 = Color3.fromRGB(170, 170, 170)
	skillsLabel.TextXAlignment = Enum.TextXAlignment.Left
	skillsLabel.TextYAlignment = Enum.TextYAlignment.Top
	skillsLabel.TextWrapped = true
	skillsLabel.Parent = card
	
	-- List skills by level
	local skillText = "🎓 Skills:\n"
	local hasSkills = false
	for skillName, level in pairs(cat.Skills) do
		if level > 0 then
			skillText = skillText .. string.format("  • %s (Lvl %d)\n", skillName, level)
			hasSkills = true
		end
	end
	if not hasSkills then
		skillText = skillText .. "  No skills trained yet"
	end
	skillsLabel.Text = skillText
	
	-- Friendship meter
	local friendshipFrame = Instance.new("Frame")
	friendshipFrame.Size = UDim2.new(1, -20, 0, 20)
	friendshipFrame.Position = UDim2.new(0, 10, 1, -30)
	friendshipFrame.BackgroundColor3 = Config.UI.Colors.Background
	friendshipFrame.BorderSizePixel = 0
	friendshipFrame.Parent = card
	
	local friendshipCorner = Instance.new("UICorner")
	friendshipCorner.CornerRadius = UDim.new(0, 4)
	friendshipCorner.Parent = friendshipFrame
	
	local friendshipBar = Instance.new("Frame")
	friendshipBar.Size = UDim2.new(cat.Friendship / 100, 0, 1, 0)
	friendshipBar.BackgroundColor3 = Color3.fromRGB(255, 170, 0)
	friendshipBar.BorderSizePixel = 0
	friendshipBar.Parent = friendshipFrame
	
	local friendshipBarCorner = Instance.new("UICorner")
	friendshipBarCorner.CornerRadius = UDim.new(0, 4)
	friendshipBarCorner.Parent = friendshipBar
	
	local friendshipLabel = Instance.new("TextLabel")
	friendshipLabel.Size = UDim2.new(1, 0, 1, 0)
	friendshipLabel.BackgroundTransparency = 1
	friendshipLabel.Text = string.format("💝 Friendship: %d%%", cat.Friendship)
	friendshipLabel.Font = Enum.Font.GothamBold
	friendshipLabel.TextSize = 12
	friendshipLabel.TextColor3 = Color3.new(1, 1, 1)
	friendshipLabel.Parent = friendshipFrame
end

--[=[
	Show player stats tab
]=]
function PlayerProfileUI:ShowStatsTab()
	-- Get player data
	local dataRemotes = ReplicatedStorage:WaitForChild("DataRemotes")
	local getData = dataRemotes:WaitForChild("GetData")
	
	local playerData = getData:InvokeServer()
	if not playerData then return end
	
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 15)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Trophy stats
	self:CreateStatSection("Trophy Stats", {
		{"Current Trophies", Utils.FormatTrophies(playerData.Trophies or 0)},
		{"Highest Trophies", Utils.FormatTrophies(playerData.HighestTrophies or 0)},
		{"Current League", (playerData.CurrentLeague or "Rookie")},
		{"Win Streak", string.format("🔥 %d", playerData.WinStreak or 0)}
	}, 1)
	
	-- Game stats
	self:CreateStatSection("Game Statistics", {
		{"Games Played", Utils.FormatNumber(playerData.Statistics.GamesPlayed)},
		{"Games Won", Utils.FormatNumber(playerData.Statistics.GamesWon)},
		{"Win Rate", string.format("%.1f%%", 
			playerData.Statistics.GamesPlayed > 0 
			and (playerData.Statistics.GamesWon / playerData.Statistics.GamesPlayed * 100) 
			or 0)},
		{"Time Played", Utils.FormatTime(playerData.Statistics.TimePlayed)}
	}, 2)
	
	-- Currency stats
	self:CreateStatSection("Currency Statistics", {
		{"Current Balance", string.format("$%s", Utils.FormatNumber(playerData.Currency))},
		{"Total Earned", string.format("$%s", Utils.FormatNumber(playerData.Statistics.TotalEarned))},
		{"Total Spent", string.format("$%s", Utils.FormatNumber(playerData.Statistics.TotalSpent))},
		{"Net Profit", string.format("$%s", Utils.FormatNumber(
			playerData.Statistics.TotalEarned - playerData.Statistics.TotalSpent
		))}
	}, 3)
	
	-- Cat stats
	self:CreateStatSection("Cat Collection", {
		{"Cats Rescued", Utils.FormatNumber(playerData.Statistics.CatsRescued)},
		{"Highest Cat Level", Utils.FormatNumber(playerData.Statistics.HighestLevel or 0)},
		{"Buildings Owned", Utils.FormatNumber(#playerData.Sanctuary.Buildings)},
		{"Sanctuary Material", playerData.Sanctuary.Material}
	}, 4)
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 800)
end

--[=[
	Create stat section
	@param title string
	@param stats table
	@param order number
]=]
function PlayerProfileUI:CreateStatSection(title: string, stats: {{string}}, order: number)
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
	
	-- Title
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
	
	-- Stats grid
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
	Show inventory tab
]=]
function PlayerProfileUI:ShowInventoryTab()
	-- Get player data
	local dataRemotes = ReplicatedStorage:WaitForChild("DataRemotes")
	local getData = dataRemotes:WaitForChild("GetData")
	
	local playerData = getData:InvokeServer()
	if not playerData then return end
	
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 15)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Buildings
	self:CreateInventorySection("Buildings", playerData.Sanctuary.Buildings, 1)
	
	-- Current sanctuary material
	self:CreateMaterialSection(playerData.Sanctuary.Material, 2)
	
	-- Game passes
	self:CreateGamePassSection(playerData.GamePasses, 3)
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 1000)
end

--[=[
	Create inventory section
	@param title string
	@param items table
	@param order number
]=]
function PlayerProfileUI:CreateInventorySection(title: string, items: {any}, order: number)
	local section = Instance.new("Frame")
	section.Name = title
	section.Size = UDim2.new(1, -20, 0, math.max(200, 100 + (#items * 40)))
	section.BackgroundColor3 = Config.UI.Colors.Secondary
	section.BorderSizePixel = 0
	section.LayoutOrder = order
	section.Parent = contentFrame
	
	local sectionCorner = Instance.new("UICorner")
	sectionCorner.CornerRadius = UDim.new(0, 10)
	sectionCorner.Parent = section
	
	-- Title
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.new(1, -20, 0, 40)
	titleLabel.Position = UDim2.new(0, 10, 0, 10)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Text = string.format("%s (%d)", title, #items)
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 20
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = section
	
	-- Item list
	if #items == 0 then
		local emptyLabel = Instance.new("TextLabel")
		emptyLabel.Size = UDim2.new(1, -20, 0, 30)
		emptyLabel.Position = UDim2.new(0, 10, 0, 60)
		emptyLabel.BackgroundTransparency = 1
		emptyLabel.Text = "No items yet"
		emptyLabel.Font = Enum.Font.Gotham
		emptyLabel.TextSize = 16
		emptyLabel.TextColor3 = Color3.fromRGB(150, 150, 150)
		emptyLabel.TextXAlignment = Enum.TextXAlignment.Left
		emptyLabel.Parent = section
	else
		for i, item in ipairs(items) do
			local buildingType = Config.BUILDINGS[item.Type]
			
			local itemFrame = Instance.new("Frame")
			itemFrame.Size = UDim2.new(1, -40, 0, 35)
			itemFrame.Position = UDim2.new(0, 20, 0, 50 + ((i - 1) * 40))
			itemFrame.BackgroundColor3 = Config.UI.Colors.Background
			itemFrame.BorderSizePixel = 0
			itemFrame.Parent = section
			
			local itemCorner = Instance.new("UICorner")
			itemCorner.CornerRadius = UDim.new(0, 6)
			itemCorner.Parent = itemFrame
			
			local itemLabel = Instance.new("TextLabel")
			itemLabel.Size = UDim2.new(1, -10, 1, 0)
			itemLabel.Position = UDim2.new(0, 5, 0, 0)
			itemLabel.BackgroundTransparency = 1
			itemLabel.Text = string.format("%s %s - Level %d (%s)", 
				buildingType.Icon, 
				buildingType.Name,
				item.Level,
				item.Material
			)
			itemLabel.Font = Enum.Font.Gotham
			itemLabel.TextSize = 15
			itemLabel.TextColor3 = Color3.new(1, 1, 1)
			itemLabel.TextXAlignment = Enum.TextXAlignment.Left
			itemLabel.Parent = itemFrame
		end
	end
end

--[=[
	Create material section
	@param material string
	@param order number
]=]
function PlayerProfileUI:CreateMaterialSection(material: string, order: number)
	local section = Instance.new("Frame")
	section.Name = "CurrentMaterial"
	section.Size = UDim2.new(1, -20, 0, 120)
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
	titleLabel.Text = "Sanctuary Material"
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 20
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = section
	
	local materialConfig = Config.MATERIALS[material]
	local materialLabel = Instance.new("TextLabel")
	materialLabel.Size = UDim2.new(1, -20, 0, 50)
	materialLabel.Position = UDim2.new(0, 10, 0, 55)
	materialLabel.BackgroundTransparency = 1
	materialLabel.Text = string.format("%s %s\n%s", 
		materialConfig.Icon,
		materialConfig.Name,
		materialConfig.Description
	)
	materialLabel.Font = Enum.Font.Gotham
	materialLabel.TextSize = 16
	materialLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	materialLabel.TextXAlignment = Enum.TextXAlignment.Left
	materialLabel.TextYAlignment = Enum.TextYAlignment.Top
	materialLabel.TextWrapped = true
	materialLabel.Parent = section
end

--[=[
	Create game pass section
	@param gamePasses table
	@param order number
]=]
function PlayerProfileUI:CreateGamePassSection(gamePasses: {any}, order: number)
	local section = Instance.new("Frame")
	section.Name = "GamePasses"
	section.Size = UDim2.new(1, -20, 0, 150)
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
	titleLabel.Text = string.format("Game Passes (%d)", #gamePasses)
	titleLabel.Font = Enum.Font.GothamBold
	titleLabel.TextSize = 20
	titleLabel.TextColor3 = Color3.new(1, 1, 1)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Parent = section
	
	local passText = #gamePasses > 0 
		and "You own: " .. table.concat(gamePasses, ", ")
		or "No game passes purchased yet"
	
	local passLabel = Instance.new("TextLabel")
	passLabel.Size = UDim2.new(1, -20, 0, 80)
	passLabel.Position = UDim2.new(0, 10, 0, 55)
	passLabel.BackgroundTransparency = 1
	passLabel.Text = passText
	passLabel.Font = Enum.Font.Gotham
	passLabel.TextSize = 16
	passLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	passLabel.TextXAlignment = Enum.TextXAlignment.Left
	passLabel.TextYAlignment = Enum.TextYAlignment.Top
	passLabel.TextWrapped = true
	passLabel.Parent = section
end

--[=[
	Show achievements tab
]=]
function PlayerProfileUI:ShowAchievementsTab()
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 10)
	listLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = contentFrame
	
	-- Coming soon message
	local comingSoon = Instance.new("TextLabel")
	comingSoon.Size = UDim2.new(1, -40, 0, 100)
	comingSoon.BackgroundColor3 = Config.UI.Colors.Secondary
	comingSoon.BorderSizePixel = 0
	comingSoon.Text = "🏆 Achievements System\n\nComing Soon!"
	comingSoon.Font = Enum.Font.GothamBold
	comingSoon.TextSize = 24
	comingSoon.TextColor3 = Color3.fromRGB(200, 200, 200)
	comingSoon.Parent = contentFrame
	
	local comingCorner = Instance.new("UICorner")
	comingCorner.CornerRadius = UDim.new(0, 10)
	comingCorner.Parent = comingSoon
	
	contentFrame.CanvasSize = UDim2.new(0, 0, 0, 150)
end

--[=[
	Get rarity color
	@param rarity string
	@return Color3
]=]
function PlayerProfileUI:GetRarityColor(rarity: string): Color3
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
	Show profile UI
]=]
function PlayerProfileUI:Show()
	if profileGui then
		profileGui.Enabled = true
		self:ShowTab(currentTab) -- Refresh current tab
	end
end

--[=[
	Hide profile UI
]=]
function PlayerProfileUI:Hide()
	if profileGui then
		profileGui.Enabled = false
	end
end

--[=[
	Toggle profile UI
]=]
function PlayerProfileUI:Toggle()
	if profileGui then
		if profileGui.Enabled then
			self:Hide()
		else
			self:Show()
		end
	end
end

return PlayerProfileUI
