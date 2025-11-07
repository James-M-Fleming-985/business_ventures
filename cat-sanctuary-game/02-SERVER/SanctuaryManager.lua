--[[
	SanctuaryManager.lua
	Handles sanctuary building and decoration placement
	
	COPY TO: ServerScriptService/CatSanctuary/SanctuaryManager (ModuleScript)
	COPY ORDER: #7
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Types = require(ReplicatedStorage.Shared.Types)
local Utils = require(ReplicatedStorage.Shared.Utils)

local SanctuaryManager = {}
SanctuaryManager.__index = SanctuaryManager

-- Remote events
local RemoteEvents = {
	BuildingPlaced = nil,
	BuildingRemoved = nil,
	PlaceBuildingRequest = nil,
	RemoveBuildingRequest = nil
}

--[=[
	Initialize sanctuary manager
	@param dataStore DataStore module
	@param currencyManager CurrencyManager module
]=]
function SanctuaryManager:Initialize(dataStore, currencyManager)
	self.DataStore = dataStore
	self.CurrencyManager = currencyManager
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "SanctuaryRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.BuildingPlaced = Instance.new("RemoteEvent")
	RemoteEvents.BuildingPlaced.Name = "BuildingPlaced"
	RemoteEvents.BuildingPlaced.Parent = remoteFolder
	
	RemoteEvents.BuildingRemoved = Instance.new("RemoteEvent")
	RemoteEvents.BuildingRemoved.Name = "BuildingRemoved"
	RemoteEvents.BuildingRemoved.Parent = remoteFolder
	
	RemoteEvents.PlaceBuildingRequest = Instance.new("RemoteFunction")
	RemoteEvents.PlaceBuildingRequest.Name = "PlaceBuildingRequest"
	RemoteEvents.PlaceBuildingRequest.Parent = remoteFolder
	
	RemoteEvents.RemoveBuildingRequest = Instance.new("RemoteFunction")
	RemoteEvents.RemoveBuildingRequest.Name = "RemoveBuildingRequest"
	RemoteEvents.RemoveBuildingRequest.Parent = remoteFolder
	
	-- Handle requests
	RemoteEvents.PlaceBuildingRequest.OnServerInvoke = function(player, buildingType, position, rotation)
		return self:PlaceBuilding(player, buildingType, position, rotation)
	end
	
	RemoteEvents.RemoveBuildingRequest.OnServerInvoke = function(player, buildingId)
		return self:RemoveBuilding(player, buildingId)
	end
	
	Utils.DebugPrint("SanctuaryManager initialized", "Sanctuary")
end

--[=[
	Get building configuration by type
	@param buildingType string
	@return table?
]=]
function SanctuaryManager:GetBuildingConfig(buildingType: string)
	for _, building in ipairs(Config.BUILDINGS) do
		if building.Id == buildingType then
			return building
		end
	end
	return nil
end

--[=[
	Place a building in player's sanctuary
	@param player Player
	@param buildingType string
	@param position Vector3
	@param rotation number
	@return boolean, string -- success, message
]=]
function SanctuaryManager:PlaceBuilding(player: Player, buildingType: string, position: Vector3, rotation: number)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false, "Player data not loaded"
	end
	
	-- Get building config
	local buildingConfig = self:GetBuildingConfig(buildingType)
	if not buildingConfig then
		return false, "Invalid building type"
	end
	
	-- Check if player can afford
	if not self.CurrencyManager:CanAfford(player, buildingConfig.Cost) then
		return false, string.format("Not enough charity (need %d)", buildingConfig.Cost)
	end
	
	-- Validate position (basic check - can be expanded)
	if not self:IsValidPosition(player, position) then
		return false, "Invalid building position"
	end
	
	-- Deduct currency
	local success = self.CurrencyManager:RemoveCurrency(
		player,
		buildingConfig.Cost,
		string.format("Place %s", buildingConfig.Name)
	)
	if not success then
		return false, "Payment failed"
	end
	
	-- Create building data
	local newBuilding: Types.BuildingData = {
		Id = Utils.GenerateId(),
		BuildingType = buildingType,
		Position = position,
		Rotation = rotation or 0,
		Material = data.Sanctuary.Material,
		Level = 1,
		PlacedAt = os.time()
	}
	
	-- Add to sanctuary
	table.insert(data.Sanctuary.Buildings, newBuilding)
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	if RemoteEvents.BuildingPlaced then
		RemoteEvents.BuildingPlaced:FireClient(player, newBuilding)
	end
	
	Utils.DebugPrint(
		string.format("%s placed %s at %s", player.Name, buildingConfig.Name, tostring(position)),
		"Sanctuary"
	)
	
	return true, "Building placed successfully"
end

--[=[
	Remove a building from sanctuary
	@param player Player
	@param buildingId string
	@return boolean, string
]=]
function SanctuaryManager:RemoveBuilding(player: Player, buildingId: string)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false, "Player data not loaded"
	end
	
	-- Find and remove building
	for i, building in ipairs(data.Sanctuary.Buildings) do
		if building.Id == buildingId then
			-- Get building config for refund
			local buildingConfig = self:GetBuildingConfig(building.BuildingType)
			if buildingConfig then
				-- Refund 50% of cost
				local refund = math.floor(buildingConfig.Cost * 0.5)
				self.CurrencyManager:AddCurrency(player, refund, "Building sold")
			end
			
			-- Remove from array
			table.remove(data.Sanctuary.Buildings, i)
			
			-- Update cache
			self.DataStore:UpdateCache(player, data)
			
			-- Notify client
			if RemoteEvents.BuildingRemoved then
				RemoteEvents.BuildingRemoved:FireClient(player, buildingId)
			end
			
			Utils.DebugPrint(
				string.format("%s removed building %s", player.Name, buildingId),
				"Sanctuary"
			)
			
			return true, "Building removed"
		end
	end
	
	return false, "Building not found"
end

--[=[
	Upgrade sanctuary material
	@param player Player
	@param newMaterial string
	@return boolean, string
]=]
function SanctuaryManager:UpgradeMaterial(player: Player, newMaterial: string)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false, "Player data not loaded"
	end
	
	-- Find material config
	local materialConfig
	for _, mat in ipairs(Config.MATERIALS) do
		if mat.Name == newMaterial then
			materialConfig = mat
			break
		end
	end
	
	if not materialConfig then
		return false, "Invalid material"
	end
	
	-- Check current material tier
	local currentTier = 1
	for _, mat in ipairs(Config.MATERIALS) do
		if mat.Name == data.Sanctuary.Material then
			currentTier = mat.Tier
			break
		end
	end
	
	if materialConfig.Tier <= currentTier then
		return false, "Can only upgrade to higher tier materials"
	end
	
	-- Calculate upgrade cost (based on tier difference and existing buildings)
	local baseCost = 10000 * (materialConfig.Tier - currentTier)
	local buildingCount = #data.Sanctuary.Buildings
	local totalCost = baseCost * (1 + buildingCount * 0.1)
	
	-- Check if player can afford
	if not self.CurrencyManager:CanAfford(player, totalCost) then
		return false, string.format("Not enough charity (need %d)", totalCost)
	end
	
	-- Deduct currency
	local success = self.CurrencyManager:RemoveCurrency(
		player,
		totalCost,
		string.format("Upgrade to %s", newMaterial)
	)
	if not success then
		return false, "Payment failed"
	end
	
	-- Update material
	data.Sanctuary.Material = newMaterial
	
	-- Update all existing buildings to new material
	for _, building in ipairs(data.Sanctuary.Buildings) do
		building.Material = newMaterial
	end
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	Utils.DebugPrint(
		string.format("%s upgraded sanctuary to %s", player.Name, newMaterial),
		"Sanctuary"
	)
	
	return true, string.format("Sanctuary upgraded to %s!", newMaterial)
end

--[=[
	Expand sanctuary plot size
	@param player Player
	@return boolean, string
]=]
function SanctuaryManager:ExpandPlot(player: Player)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false, "Player data not loaded"
	end
	
	-- Check max plots
	local maxPlots = Config.PLAYER.MaxSanctuaryPlots
	if Utils.PlayerOwnsGamePass(player, Config.GAME_PASSES.MegaSanctuary) then
		maxPlots = Config.PLAYER.MaxSanctuaryPlotsWithVIP
	end
	
	if data.Sanctuary.PlotSize >= maxPlots then
		return false, string.format("Maximum plot size reached (%d)", maxPlots)
	end
	
	-- Calculate expansion cost (exponential)
	local cost = 5000 * (2 ^ data.Sanctuary.PlotSize)
	
	-- Check if player can afford
	if not self.CurrencyManager:CanAfford(player, cost) then
		return false, string.format("Not enough charity (need %d)", cost)
	end
	
	-- Deduct currency
	local success = self.CurrencyManager:RemoveCurrency(player, cost, "Plot expansion")
	if not success then
		return false, "Payment failed"
	end
	
	-- Expand plot
	data.Sanctuary.PlotSize = data.Sanctuary.PlotSize + 1
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	Utils.DebugPrint(
		string.format("%s expanded plot to size %d", player.Name, data.Sanctuary.PlotSize),
		"Sanctuary"
	)
	
	return true, "Plot expanded!"
end

--[=[
	Validate building position
	@param player Player
	@param position Vector3
	@return boolean
]=]
function SanctuaryManager:IsValidPosition(player: Player, position: Vector3): boolean
	-- Basic validation - can be expanded with collision detection
	
	-- Check if position is within plot bounds
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false
	end
	
	local plotSize = data.Sanctuary.PlotSize * 50 -- 50 studs per plot
	
	if math.abs(position.X) > plotSize or math.abs(position.Z) > plotSize then
		return false
	end
	
	-- Check Y is on ground level
	if position.Y < 0 or position.Y > 50 then
		return false
	end
	
	-- TODO: Add collision detection with other buildings
	
	return true
end

--[=[
	Get all buildings in a sanctuary
	@param player Player
	@return {BuildingData}
]=]
function SanctuaryManager:GetAllBuildings(player: Player): {Types.BuildingData}
	local data = self.DataStore:GetCachedData(player)
	return data and data.Sanctuary.Buildings or {}
end

--[=[
	Calculate total cat capacity from buildings
	@param player Player
	@return number
]=]
function SanctuaryManager:CalculateCatCapacity(player: Player): number
	local buildings = self:GetAllBuildings(player)
	local totalCapacity = 0
	
	for _, building in ipairs(buildings) do
		local config = self:GetBuildingConfig(building.BuildingType)
		if config and config.Capacity then
			totalCapacity = totalCapacity + config.Capacity
		end
	end
	
	return totalCapacity
end

return SanctuaryManager
