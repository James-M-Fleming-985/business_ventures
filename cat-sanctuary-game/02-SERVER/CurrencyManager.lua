--[[
	CurrencyManager.lua
	Handles charity money (in-game currency)
	
	COPY TO: ServerScriptService/CatSanctuary/CurrencyManager (ModuleScript)
	COPY ORDER: #5
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local CurrencyManager = {}
CurrencyManager.__index = CurrencyManager

-- Remote events for client communication
local RemoteEvents = {
	CurrencyChanged = nil,
	PurchaseRequest = nil
}

--[=[
	Initialize currency manager
	@param dataStore DataStore module
]=]
function CurrencyManager:Initialize(dataStore)
	self.DataStore = dataStore
	
	-- Create remote events
	local remoteFolder = Instance.new("Folder")
	remoteFolder.Name = "CurrencyRemotes"
	remoteFolder.Parent = ReplicatedStorage
	
	RemoteEvents.CurrencyChanged = Instance.new("RemoteEvent")
	RemoteEvents.CurrencyChanged.Name = "CurrencyChanged"
	RemoteEvents.CurrencyChanged.Parent = remoteFolder
	
	RemoteEvents.PurchaseRequest = Instance.new("RemoteFunction")
	RemoteEvents.PurchaseRequest.Name = "PurchaseRequest"
	RemoteEvents.PurchaseRequest.Parent = remoteFolder
	
	-- Handle purchase requests
	RemoteEvents.PurchaseRequest.OnServerInvoke = function(player, itemType, itemId)
		return self:HandlePurchase(player, itemType, itemId)
	end
	
	Utils.DebugPrint("CurrencyManager initialized", "Currency")
end

--[=[
	Get player's current currency
	@param player Player
	@return number
]=]
function CurrencyManager:GetCurrency(player: Player): number
	local data = self.DataStore:GetCachedData(player)
	return data and data.Currency or 0
end

--[=[
	Add currency to player
	@param player Player
	@param amount number
	@param reason string -- For tracking/analytics
	@return boolean -- Success
]=]
function CurrencyManager:AddCurrency(player: Player, amount: number, reason: string?): boolean
	if amount <= 0 then
		return false
	end
	
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false
	end
	
	-- Add currency (capped at max)
	local oldAmount = data.Currency
	data.Currency = math.min(data.Currency + amount, Config.CURRENCY.MaxAmount)
	local actualAdded = data.Currency - oldAmount
	
	-- Update statistics
	data.Statistics.TotalEarned = data.Statistics.TotalEarned + actualAdded
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	self:NotifyClient(player, data.Currency, actualAdded)
	
	Utils.DebugPrint(
		string.format("%s gained %d charity (reason: %s)", player.Name, actualAdded, reason or "unknown"),
		"Currency"
	)
	
	return true
end

--[=[
	Remove currency from player
	@param player Player
	@param amount number
	@param reason string
	@return boolean -- Success (false if not enough currency)
]=]
function CurrencyManager:RemoveCurrency(player: Player, amount: number, reason: string?): boolean
	if amount <= 0 then
		return false
	end
	
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false
	end
	
	-- Check if player has enough
	if data.Currency < amount then
		Utils.DebugPrint(
			string.format("%s tried to spend %d but only has %d", player.Name, amount, data.Currency),
			"Currency"
		)
		return false
	end
	
	-- Remove currency
	data.Currency = data.Currency - amount
	
	-- Update statistics
	data.Statistics.TotalSpent = data.Statistics.TotalSpent + amount
	
	-- Update cache
	self.DataStore:UpdateCache(player, data)
	
	-- Notify client
	self:NotifyClient(player, data.Currency, -amount)
	
	Utils.DebugPrint(
		string.format("%s spent %d charity (reason: %s)", player.Name, amount, reason or "unknown"),
		"Currency"
	)
	
	return true
end

--[=[
	Set player currency to specific amount (admin use)
	@param player Player
	@param amount number
]=]
function CurrencyManager:SetCurrency(player: Player, amount: number)
	local data = self.DataStore:GetCachedData(player)
	if not data then
		return false
	end
	
	amount = Utils.Clamp(amount, 0, Config.CURRENCY.MaxAmount)
	local change = amount - data.Currency
	data.Currency = amount
	
	self.DataStore:UpdateCache(player, data)
	self:NotifyClient(player, data.Currency, change)
	
	Utils.DebugPrint(string.format("Set %s currency to %d", player.Name, amount), "Currency")
	return true
end

--[=[
	Award currency from mini-game performance
	@param player Player
	@param place number -- 1st, 2nd, 3rd, etc.
	@param catCuteness number -- For audience bonus
	@param gameType string -- Type of mini-game
]=]
function CurrencyManager:AwardGameReward(player: Player, place: number, catCuteness: number, gameType: string)
	-- Base reward from placement
	local baseReward = Config.CURRENCY.PlaceBonus[place] or Config.CURRENCY.ParticipationReward
	
	-- Audience multiplier based on cat cuteness
	local audienceMultiplier = Config.CURRENCY.AudienceMultiplier(catCuteness)
	
	-- Game type multiplier
	local gameConfig = Config.MINI_GAMES[gameType]
	local gameMultiplier = gameConfig and gameConfig.RewardMultiplier or 1.0
	
	-- Check for VIP game pass (2x earnings)
	local vipMultiplier = 1.0
	if Utils.PlayerOwnsGamePass(player, Config.GAME_PASSES.VIP) then
		vipMultiplier = 2.0
	end
	
	-- Calculate final reward
	local totalReward = math.floor(baseReward * audienceMultiplier * gameMultiplier * vipMultiplier)
	
	-- Add currency
	self:AddCurrency(player, totalReward, string.format("%s game - place %d", gameType, place))
	
	return totalReward
end

--[=[
	Handle purchase request from client
	@param player Player
	@param itemType string -- "Cat", "Building", "Decoration", "Upgrade"
	@param itemId string
	@return boolean, string -- success, message
]=]
function CurrencyManager:HandlePurchase(player: Player, itemType: string, itemId: string)
	-- This will be expanded when we implement shop system
	-- For now, just verify player has currency
	
	local cost = self:GetItemCost(itemType, itemId)
	if not cost then
		return false, "Item not found"
	end
	
	local success = self:RemoveCurrency(player, cost, string.format("Purchase: %s", itemId))
	if success then
		return true, "Purchase successful"
	else
		return false, "Not enough charity money"
	end
end

--[=[
	Get cost of an item
	@param itemType string
	@param itemId string
	@return number?
]=]
function CurrencyManager:GetItemCost(itemType: string, itemId: string): number?
	if itemType == "Building" then
		for _, building in ipairs(Config.BUILDINGS) do
			if building.Id == itemId then
				return building.Cost
			end
		end
	end
	
	-- Add more item types here
	
	return nil
end

--[=[
	Notify client of currency change
	@param player Player
	@param newAmount number
	@param changeAmount number
]=]
function CurrencyManager:NotifyClient(player: Player, newAmount: number, changeAmount: number)
	if RemoteEvents.CurrencyChanged then
		RemoteEvents.CurrencyChanged:FireClient(player, newAmount, changeAmount)
	end
end

--[=[
	Check if player can afford something
	@param player Player
	@param cost number
	@return boolean
]=]
function CurrencyManager:CanAfford(player: Player, cost: number): boolean
	local current = self:GetCurrency(player)
	return current >= cost
end

return CurrencyManager
