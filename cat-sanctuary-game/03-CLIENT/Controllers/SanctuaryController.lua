--[[
	SanctuaryController.lua
	Client-side sanctuary management
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/Controllers/SanctuaryController (LocalScript)
	COPY ORDER: #12
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local SanctuaryController = {}

-- Building placement state
local placementMode = false
local currentBuilding = nil
local previewModel = nil

-- Remote events
local sanctuaryRemotes = ReplicatedStorage:WaitForChild("SanctuaryRemotes")
local placeBuildingRequest = sanctuaryRemotes:WaitForChild("PlaceBuildingRequest")
local removeBuildingRequest = sanctuaryRemotes:WaitForChild("RemoveBuildingRequest")
local buildingPlaced = sanctuaryRemotes:WaitForChild("BuildingPlaced")
local buildingRemoved = sanctuaryRemotes:WaitForChild("BuildingRemoved")

--[=[
	Initialize sanctuary controller
]=]
function SanctuaryController:Initialize()
	-- Listen for building placement from server
	buildingPlaced.OnClientEvent:Connect(function(buildingData)
		self:CreateBuildingModel(buildingData)
	end)
	
	buildingRemoved.OnClientEvent:Connect(function(buildingId)
		self:RemoveBuildingModel(buildingId)
	end)
	
	-- Handle input for building placement
	UserInputService.InputBegan:Connect(function(input, gameProcessed)
		if gameProcessed then return end
		
		if placementMode and input.UserInputType == Enum.UserInputType.MouseButton1 then
			self:PlaceBuilding()
		elseif input.KeyCode == Enum.KeyCode.Escape and placementMode then
			self:CancelPlacement()
		end
	end)
	
	-- Update preview position
	game:GetService("RunService").RenderStepped:Connect(function()
		if placementMode and previewModel then
			self:UpdatePreviewPosition()
		end
	end)
	
	print("🏡 SanctuaryController initialized")
end

--[=[
	Start building placement mode
	@param buildingType string
]=]
function SanctuaryController:StartPlacement(buildingType: string)
	if placementMode then
		self:CancelPlacement()
	end
	
	currentBuilding = buildingType
	placementMode = true
	
	-- Create preview model
	self:CreatePreviewModel(buildingType)
	
	print(string.format("Started placement mode for %s", buildingType))
end

--[=[
	Create preview model for placement
	@param buildingType string
]=]
function SanctuaryController:CreatePreviewModel(buildingType: string)
	-- In real implementation, load actual model
	-- For now, create a simple placeholder
	previewModel = Instance.new("Part")
	previewModel.Name = "BuildingPreview"
	previewModel.Size = Vector3.new(10, 5, 10)
	previewModel.Anchored = true
	previewModel.CanCollide = false
	previewModel.Transparency = 0.5
	previewModel.Color = Color3.fromRGB(100, 200, 255)
	previewModel.Parent = workspace
	
	-- Add highlight
	local highlight = Instance.new("Highlight")
	highlight.FillTransparency = 0.5
	highlight.OutlineColor = Color3.fromRGB(255, 255, 255)
	highlight.Parent = previewModel
end

--[=[
	Update preview model position based on mouse
]=]
function SanctuaryController:UpdatePreviewPosition()
	if not previewModel then return end
	
	local mouse = Player:GetMouse()
	local ray = workspace.CurrentCamera:ScreenPointToRay(mouse.X, mouse.Y)
	local raycastParams = RaycastParams.new()
	raycastParams.FilterType = Enum.RaycastFilterType.Blacklist
	raycastParams.FilterDescendantsInstances = {previewModel}
	
	local result = workspace:Raycast(ray.Origin, ray.Direction * 1000, raycastParams)
	
	if result then
		-- Snap to grid (5 stud increments)
		local gridSize = 5
		local snappedX = math.floor(result.Position.X / gridSize + 0.5) * gridSize
		local snappedZ = math.floor(result.Position.Z / gridSize + 0.5) * gridSize
		
		previewModel.Position = Vector3.new(snappedX, result.Position.Y + (previewModel.Size.Y / 2), snappedZ)
		
		-- Check if position is valid (green = valid, red = invalid)
		local isValid = self:IsValidPlacement(previewModel.Position)
		previewModel.Color = isValid and Color3.fromRGB(100, 255, 100) or Color3.fromRGB(255, 100, 100)
	end
end

--[=[
	Check if placement position is valid
	@param position Vector3
	@return boolean
]=]
function SanctuaryController:IsValidPlacement(position: Vector3): boolean
	-- Basic validation - can be expanded
	-- Check if within sanctuary bounds
	local maxDistance = 100
	if position.Magnitude > maxDistance then
		return false
	end
	
	-- Check for collisions with other buildings
	-- TODO: Implement collision detection
	
	return true
end

--[=[
	Place building at current preview position
]=]
function SanctuaryController:PlaceBuilding()
	if not previewModel or not currentBuilding then return end
	
	local position = previewModel.Position
	
	if not self:IsValidPlacement(position) then
		print("❌ Invalid placement position")
		return
	end
	
	-- Request placement from server
	local success, message = placeBuildingRequest:InvokeServer(currentBuilding, position, 0)
	
	if success then
		print("✅ Building placed:", message)
	else
		warn("❌ Failed to place building:", message)
	end
	
	-- Clean up
	self:CancelPlacement()
end

--[=[
	Cancel building placement
]=]
function SanctuaryController:CancelPlacement()
	placementMode = false
	currentBuilding = nil
	
	if previewModel then
		previewModel:Destroy()
		previewModel = nil
	end
	
	print("Cancelled placement mode")
end

--[=[
	Create building model in world
	@param buildingData BuildingData
]=]
function SanctuaryController:CreateBuildingModel(buildingData)
	-- In real implementation, load actual building model from assets
	-- For now, create a placeholder
	local buildingModel = Instance.new("Part")
	buildingModel.Name = buildingData.Id
	buildingModel.Size = Vector3.new(10, 5, 10)
	buildingModel.Position = buildingData.Position
	buildingModel.Orientation = Vector3.new(0, buildingData.Rotation, 0)
	buildingModel.Anchored = true
	buildingModel.Color = Config.UI.Colors.Primary
	
	-- Add label
	local billboardGui = Instance.new("BillboardGui")
	billboardGui.Size = UDim2.new(0, 200, 0, 50)
	billboardGui.Adornee = buildingModel
	billboardGui.AlwaysOnTop = true
	billboardGui.Parent = buildingModel
	
	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, 0, 1, 0)
	label.BackgroundTransparency = 1
	label.Text = buildingData.BuildingType
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextScaled = true
	label.Parent = billboardGui
	
	-- Store in workspace folder
	local sanctuaryFolder = workspace:FindFirstChild("Sanctuary") or Instance.new("Folder", workspace)
	sanctuaryFolder.Name = "Sanctuary"
	buildingModel.Parent = sanctuaryFolder
	
	print(string.format("Created building model: %s", buildingData.BuildingType))
end

--[=[
	Remove building model from world
	@param buildingId string
]=]
function SanctuaryController:RemoveBuildingModel(buildingId: string)
	local sanctuaryFolder = workspace:FindFirstChild("Sanctuary")
	if sanctuaryFolder then
		local building = sanctuaryFolder:FindFirstChild(buildingId)
		if building then
			building:Destroy()
			print(string.format("Removed building: %s", buildingId))
		end
	end
end

--[=[
	Request building removal
	@param buildingId string
]=]
function SanctuaryController:RemoveBuilding(buildingId: string)
	local success, message = removeBuildingRequest:InvokeServer(buildingId)
	
	if success then
		print("✅", message)
	else
		warn("❌", message)
	end
end

-- Initialize when script runs
SanctuaryController:Initialize()

return SanctuaryController
