--[[
	WorldGenerator.lua
	Procedurally generates the Cat Sanctuary world environment
	
	COPY TO: ServerScriptService/Server/WorldGenerator (ModuleScript)
	COPY ORDER: #19 (Before MainServer initialization)
	
	Generates:
	- Backyard sanctuary ground/terrain
	- Fenced boundaries
	- Spawn area
	- Cat rescue zones
	- Building plots
	- Mini-game arenas (Race track, Agility course)
	- Decorative elements (trees, gardens)
]]

local WorldGenerator = {}

-- World Configuration
local WORLD_CONFIG = {
	-- Main sanctuary area (backyard)
	SanctuarySize = Vector3.new(300, 1, 300), -- Large backyard
	SanctuaryPosition = Vector3.new(0, 0, 0),
	GroundColor = Color3.fromRGB(107, 163, 83), -- Grass green
	
	-- Fence/boundary
	FenceHeight = 8,
	FenceThickness = 1,
	FenceColor = Color3.fromRGB(139, 90, 43), -- Wood brown
	
	-- Spawn area (near house)
	SpawnPosition = Vector3.new(-100, 3, -100),
	
	-- Cat rescue zones (4 corners of yard)
	CatSpawnZones = {
		{Position = Vector3.new(-120, 2, 120), Size = Vector3.new(20, 1, 20)},
		{Position = Vector3.new(120, 2, 120), Size = Vector3.new(20, 1, 20)},
		{Position = Vector3.new(-120, 2, -120), Size = Vector3.new(20, 1, 20)},
		{Position = Vector3.new(120, 2, -120), Size = Vector3.new(20, 1, 20)},
	},
	
	-- Building plots (center-left area)
	BuildingPlots = {
		{Position = Vector3.new(-80, 1, 0), Size = Vector3.new(30, 1, 30), Name = "Plot1"},
		{Position = Vector3.new(-80, 1, 40), Size = Vector3.new(30, 1, 30), Name = "Plot2"},
		{Position = Vector3.new(-80, 1, -40), Size = Vector3.new(30, 1, 30), Name = "Plot3"},
		{Position = Vector3.new(-40, 1, 0), Size = Vector3.new(30, 1, 30), Name = "Plot4"},
		{Position = Vector3.new(-40, 1, 40), Size = Vector3.new(30, 1, 30), Name = "Plot5"},
		{Position = Vector3.new(-40, 1, -40), Size = Vector3.new(30, 1, 30), Name = "Plot6"},
	},
	
	-- Race track (right side)
	RaceTrack = {
		Position = Vector3.new(80, 1, 0),
		Size = Vector3.new(80, 1, 200), -- Long straight track
		Color = Color3.fromRGB(180, 180, 180), -- Gray track
	},
	
	-- Agility course (bottom center)
	AgilityCourse = {
		Position = Vector3.new(0, 1, -100),
		Size = Vector3.new(100, 1, 60),
		Color = Color3.fromRGB(205, 175, 149), -- Sand color
	},
	
	-- Decorations
	TreePositions = {
		Vector3.new(-130, 0, 130),
		Vector3.new(130, 0, 130),
		Vector3.new(-130, 0, -130),
		Vector3.new(130, 0, -130),
		Vector3.new(0, 0, 140),
		Vector3.new(0, 0, -140),
		Vector3.new(-140, 0, 0),
		Vector3.new(140, 0, 0),
	},
}

-- Helper function to create a part
local function CreatePart(name, size, position, color, parent, anchored, transparency, canCollide)
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.Position = position
	part.Color = color or Color3.fromRGB(163, 162, 165)
	part.Anchored = anchored ~= false -- Default true
	part.Transparency = transparency or 0
	part.CanCollide = canCollide ~= false -- Default true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Material = Enum.Material.SmoothPlastic
	part.Parent = parent
	return part
end

-- Generate main ground
function WorldGenerator:GenerateGround(workspace)
	print("[WorldGenerator] Creating sanctuary ground...")
	
	local ground = CreatePart(
		"SanctuaryGround",
		WORLD_CONFIG.SanctuarySize,
		WORLD_CONFIG.SanctuaryPosition,
		WORLD_CONFIG.GroundColor,
		workspace,
		true,
		0,
		true
	)
	ground.Material = Enum.Material.Grass
	
	return ground
end

-- Generate fence boundary
function WorldGenerator:GenerateFence(workspace)
	print("[WorldGenerator] Building fence boundary...")
	
	local fenceFolder = Instance.new("Folder")
	fenceFolder.Name = "Fence"
	fenceFolder.Parent = workspace
	
	local halfSize = WORLD_CONFIG.SanctuarySize.X / 2
	local height = WORLD_CONFIG.FenceHeight
	
	-- North fence
	CreatePart(
		"FenceNorth",
		Vector3.new(WORLD_CONFIG.SanctuarySize.X, height, WORLD_CONFIG.FenceThickness),
		Vector3.new(0, height/2, halfSize),
		WORLD_CONFIG.FenceColor,
		fenceFolder,
		true,
		0,
		true
	)
	
	-- South fence
	CreatePart(
		"FenceSouth",
		Vector3.new(WORLD_CONFIG.SanctuarySize.X, height, WORLD_CONFIG.FenceThickness),
		Vector3.new(0, height/2, -halfSize),
		WORLD_CONFIG.FenceColor,
		fenceFolder,
		true,
		0,
		true
	)
	
	-- East fence
	CreatePart(
		"FenceEast",
		Vector3.new(WORLD_CONFIG.FenceThickness, height, WORLD_CONFIG.SanctuarySize.Z),
		Vector3.new(halfSize, height/2, 0),
		WORLD_CONFIG.FenceColor,
		fenceFolder,
		true,
		0,
		true
	)
	
	-- West fence
	CreatePart(
		"FenceWest",
		Vector3.new(WORLD_CONFIG.FenceThickness, height, WORLD_CONFIG.SanctuarySize.Z),
		Vector3.new(-halfSize, height/2, 0),
		WORLD_CONFIG.FenceColor,
		fenceFolder,
		true,
		0,
		true
	)
	
	return fenceFolder
end

-- Generate spawn location
function WorldGenerator:GenerateSpawn(workspace)
	print("[WorldGenerator] Creating player spawn...")
	
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "PlayerSpawn"
	spawn.Size = Vector3.new(12, 1, 12)
	spawn.Position = WORLD_CONFIG.SpawnPosition
	spawn.Anchored = true
	spawn.CanCollide = true
	spawn.Transparency = 0.5
	spawn.BrickColor = BrickColor.new("Bright blue")
	spawn.TopSurface = Enum.SurfaceType.Smooth
	spawn.BottomSurface = Enum.SurfaceType.Smooth
	spawn.Parent = workspace
	
	-- Add spawn sign
	local sign = CreatePart(
		"SpawnSign",
		Vector3.new(8, 6, 0.5),
		WORLD_CONFIG.SpawnPosition + Vector3.new(0, 4, -8),
		Color3.fromRGB(255, 255, 255),
		workspace,
		true,
		0,
		false
	)
	
	local text = Instance.new("SurfaceGui")
	text.Parent = sign
	text.Face = Enum.NormalId.Front
	
	local label = Instance.new("TextLabel")
	label.Parent = text
	label.Size = UDim2.new(1, 0, 1, 0)
	label.BackgroundTransparency = 1
	label.Text = "🐱 Cat Sanctuary\nWelcome!"
	label.TextSize = 48
	label.TextColor3 = Color3.fromRGB(0, 0, 0)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	
	return spawn
end

-- Generate cat spawn zones
function WorldGenerator:GenerateCatZones(workspace)
	print("[WorldGenerator] Creating cat rescue zones...")
	
	local zonesFolder = Instance.new("Folder")
	zonesFolder.Name = "CatSpawnZones"
	zonesFolder.Parent = workspace
	
	for i, zone in ipairs(WORLD_CONFIG.CatSpawnZones) do
		local zonePart = CreatePart(
			"CatZone" .. i,
			zone.Size,
			zone.Position,
			Color3.fromRGB(255, 200, 100), -- Orange-ish for cat zones
			zonesFolder,
			true,
			0.7, -- Semi-transparent
			false -- Don't block movement
		)
		zonePart.Material = Enum.Material.Neon
	end
	
	return zonesFolder
end

-- Generate building plots
function WorldGenerator:GenerateBuildingPlots(workspace)
	print("[WorldGenerator] Creating building plots...")
	
	local plotsFolder = Instance.new("Folder")
	plotsFolder.Name = "BuildingPlots"
	plotsFolder.Parent = workspace
	
	for i, plot in ipairs(WORLD_CONFIG.BuildingPlots) do
		local plotPart = CreatePart(
			plot.Name,
			plot.Size,
			plot.Position,
			Color3.fromRGB(139, 115, 85), -- Dirt brown
			plotsFolder,
			true,
			0.3,
			false
		)
		plotPart.Material = Enum.Material.Ground
		
		-- Add plot marker
		local marker = CreatePart(
			plot.Name .. "_Marker",
			Vector3.new(2, 0.5, 2),
			plot.Position + Vector3.new(0, 1, 0),
			Color3.fromRGB(255, 255, 255),
			plotsFolder,
			true,
			0,
			false
		)
	end
	
	return plotsFolder
end

-- Generate race track
function WorldGenerator:GenerateRaceTrack(workspace)
	print("[WorldGenerator] Building race track...")
	
	local track = CreatePart(
		"RaceTrack",
		WORLD_CONFIG.RaceTrack.Size,
		WORLD_CONFIG.RaceTrack.Position,
		WORLD_CONFIG.RaceTrack.Color,
		workspace,
		true,
		0,
		true
	)
	track.Material = Enum.Material.Concrete
	
	-- Add start line
	local startLine = CreatePart(
		"RaceStart",
		Vector3.new(WORLD_CONFIG.RaceTrack.Size.X, 0.5, 5),
		WORLD_CONFIG.RaceTrack.Position + Vector3.new(0, 0.5, -95),
		Color3.fromRGB(0, 255, 0), -- Green
		workspace,
		true,
		0,
		false
	)
	startLine.Material = Enum.Material.Neon
	
	-- Add finish line
	local finishLine = CreatePart(
		"RaceFinish",
		Vector3.new(WORLD_CONFIG.RaceTrack.Size.X, 0.5, 5),
		WORLD_CONFIG.RaceTrack.Position + Vector3.new(0, 0.5, 95),
		Color3.fromRGB(255, 0, 0), -- Red
		workspace,
		true,
		0,
		false
	)
	finishLine.Material = Enum.Material.Neon
	
	return track
end

-- Generate agility course
function WorldGenerator:GenerateAgilityCourse(workspace)
	print("[WorldGenerator] Building agility course...")
	
	local course = CreatePart(
		"AgilityCourse",
		WORLD_CONFIG.AgilityCourse.Size,
		WORLD_CONFIG.AgilityCourse.Position,
		WORLD_CONFIG.AgilityCourse.Color,
		workspace,
		true,
		0,
		true
	)
	course.Material = Enum.Material.Sand
	
	-- Add obstacles (hurdles)
	for i = 1, 5 do
		local xPos = -40 + (i * 20)
		local hurdle = CreatePart(
			"Hurdle" .. i,
			Vector3.new(15, 4, 2),
			WORLD_CONFIG.AgilityCourse.Position + Vector3.new(xPos, 2, 0),
			Color3.fromRGB(255, 170, 0), -- Orange
			workspace,
			true,
			0,
			true
		)
	end
	
	return course
end

-- Generate decorative trees
function WorldGenerator:GenerateTrees(workspace)
	print("[WorldGenerator] Planting decorative trees...")
	
	local treesFolder = Instance.new("Folder")
	treesFolder.Name = "Trees"
	treesFolder.Parent = workspace
	
	for i, pos in ipairs(WORLD_CONFIG.TreePositions) do
		-- Tree trunk
		local trunk = CreatePart(
			"TreeTrunk" .. i,
			Vector3.new(3, 12, 3),
			pos + Vector3.new(0, 6, 0),
			Color3.fromRGB(91, 59, 31), -- Brown
			treesFolder,
			true,
			0,
			true
		)
		trunk.Material = Enum.Material.Wood
		
		-- Tree foliage
		local foliage = CreatePart(
			"TreeFoliage" .. i,
			Vector3.new(12, 12, 12),
			pos + Vector3.new(0, 15, 0),
			Color3.fromRGB(0, 128, 0), -- Dark green
			treesFolder,
			true,
			0,
			false
		)
		foliage.Shape = Enum.PartType.Ball
		foliage.Material = Enum.Material.Grass
	end
	
	return treesFolder
end

-- Generate sky and lighting
function WorldGenerator:GenerateLighting(game)
	print("[WorldGenerator] Setting up lighting...")
	
	local lighting = game:GetService("Lighting")
	
	-- Time of day (afternoon)
	lighting.TimeOfDay = "14:00:00"
	lighting.Brightness = 2
	lighting.Ambient = Color3.fromRGB(150, 150, 150)
	lighting.OutdoorAmbient = Color3.fromRGB(127, 127, 127)
	
	-- Add sky
	local sky = Instance.new("Sky")
	sky.Name = "SanctuarySky"
	sky.SkyboxBk = "rbxasset://sky/sky512_bk.jpg"
	sky.SkyboxDn = "rbxasset://sky/sky512_dn.jpg"
	sky.SkyboxFt = "rbxasset://sky/sky512_ft.jpg"
	sky.SkyboxLf = "rbxasset://sky/sky512_lf.jpg"
	sky.SkyboxRt = "rbxasset://sky/sky512_rt.jpg"
	sky.SkyboxUp = "rbxasset://sky/sky512_up.jpg"
	sky.Parent = lighting
	
	-- Add atmosphere
	local atmosphere = Instance.new("Atmosphere")
	atmosphere.Density = 0.3
	atmosphere.Offset = 0.5
	atmosphere.Color = Color3.fromRGB(199, 199, 199)
	atmosphere.Decay = Color3.fromRGB(106, 112, 125)
	atmosphere.Glare = 0
	atmosphere.Haze = 0
	atmosphere.Parent = lighting
end

-- Main generation function
function WorldGenerator:GenerateWorld()
	print("\n[WorldGenerator] ========================================")
	print("[WorldGenerator] Starting Cat Sanctuary world generation...")
	print("[WorldGenerator] ========================================\n")
	
	local workspace = game:GetService("Workspace")
	
	-- Clear existing workspace (except default objects)
	for _, child in ipairs(workspace:GetChildren()) do
		if child.Name ~= "Camera" and child.Name ~= "Terrain" then
			child:Destroy()
		end
	end
	
	-- Generate all world elements
	self:GenerateGround(workspace)
	self:GenerateFence(workspace)
	self:GenerateSpawn(workspace)
	self:GenerateCatZones(workspace)
	self:GenerateBuildingPlots(workspace)
	self:GenerateRaceTrack(workspace)
	self:GenerateAgilityCourse(workspace)
	self:GenerateTrees(workspace)
	self:GenerateLighting(game)
	
	print("\n[WorldGenerator] ========================================")
	print("[WorldGenerator] World generation complete!")
	print("[WorldGenerator] - Sanctuary ground: ✓")
	print("[WorldGenerator] - Boundary fence: ✓")
	print("[WorldGenerator] - Player spawn: ✓")
	print("[WorldGenerator] - Cat zones: ✓")
	print("[WorldGenerator] - Building plots: ✓")
	print("[WorldGenerator] - Race track: ✓")
	print("[WorldGenerator] - Agility course: ✓")
	print("[WorldGenerator] - Trees & decorations: ✓")
	print("[WorldGenerator] - Lighting: ✓")
	print("[WorldGenerator] ========================================\n")
	
	return true
end

return WorldGenerator
