--[[
	CatController.lua
	Client-side cat interaction and management
	
	COPY TO: StarterPlayer/StarterPlayerScripts/CatSanctuary/Controllers/CatController (LocalScript)
	COPY ORDER: #13
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage.Shared.Config)
local Utils = require(ReplicatedStorage.Shared.Utils)

local CatController = {}

-- Cat data cache
local playerCats = {}
local selectedCat = nil

-- Remote events
local catRemotes = ReplicatedStorage:WaitForChild("CatRemotes")
local catAdded = catRemotes:WaitForChild("CatAdded")
local catUpdated = catRemotes:WaitForChild("CatUpdated")
local trainCatRequest = catRemotes:WaitForChild("TrainCatRequest")

--[=[
	Initialize cat controller
]=]
function CatController:Initialize()
	-- Listen for cat events
	catAdded.OnClientEvent:Connect(function(catData)
		self:OnCatAdded(catData)
	end)
	
	catUpdated.OnClientEvent:Connect(function(catData)
		self:OnCatUpdated(catData)
	end)
	
	print("🐱 CatController initialized")
end

--[=[
	Handle new cat added
	@param catData CatData
]=]
function CatController:OnCatAdded(catData)
	table.insert(playerCats, catData)
	
	-- Show notification
	self:ShowNotification(
		string.format("New cat rescued: %s (%s)!", catData.Name, catData.Rarity),
		Utils.GetRarityColor(catData.Rarity)
	)
	
	print(string.format("✅ Added cat: %s", catData.Name))
end

--[=[
	Handle cat updated
	@param catData CatData
]=]
function CatController:OnCatUpdated(catData)
	-- Update in cache
	for i, cat in ipairs(playerCats) do
		if cat.Id == catData.Id then
			playerCats[i] = catData
			
			-- If this is the selected cat, update selection
			if selectedCat and selectedCat.Id == catData.Id then
				selectedCat = catData
			end
			
			break
		end
	end
	
	print(string.format("🔄 Updated cat: %s", catData.Name))
end

--[=[
	Train a cat's skill
	@param catId string
	@param skillName string
]=]
function CatController:TrainSkill(catId: string, skillName: string)
	local success, message = trainCatRequest:InvokeServer(catId, skillName)
	
	if success then
		self:ShowNotification(message, Config.UI.Colors.Success)
	else
		self:ShowNotification(message, Config.UI.Colors.Error)
	end
	
	return success
end

--[=[
	Select a cat
	@param catId string
]=]
function CatController:SelectCat(catId: string)
	for _, cat in ipairs(playerCats) do
		if cat.Id == catId then
			selectedCat = cat
			print(string.format("Selected cat: %s", cat.Name))
			return cat
		end
	end
	return nil
end

--[=[
	Get selected cat
	@return CatData?
]=]
function CatController:GetSelectedCat()
	return selectedCat
end

--[=[
	Get all player cats
	@return {CatData}
]=]
function CatController:GetAllCats()
	return playerCats
end

--[=[
	Show notification to player
	@param message string
	@param color Color3
]=]
function CatController:ShowNotification(message: string, color: Color3?)
	-- Create screen GUI notification
	local playerGui = Player:WaitForChild("PlayerGui")
	
	local notification = Instance.new("ScreenGui")
	notification.Name = "Notification"
	notification.ResetOnSpawn = false
	notification.Parent = playerGui
	
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(0, 400, 0, 80)
	frame.Position = UDim2.new(0.5, -200, 0, -100)
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.BackgroundColor3 = color or Config.UI.Colors.Primary
	frame.BorderSizePixel = 0
	frame.Parent = notification
	
	-- Add corner radius
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = frame
	
	-- Add text
	local textLabel = Instance.new("TextLabel")
	textLabel.Size = UDim2.new(1, -20, 1, -20)
	textLabel.Position = UDim2.new(0, 10, 0, 10)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = message
	textLabel.TextColor3 = Color3.new(1, 1, 1)
	textLabel.TextScaled = true
	textLabel.Font = Enum.Font.GothamBold
	textLabel.Parent = frame
	
	-- Animate in
	frame:TweenPosition(
		UDim2.new(0.5, -200, 0.1, 0),
		Enum.EasingDirection.Out,
		Enum.EasingStyle.Back,
		0.5,
		true
	)
	
	-- Animate out and destroy
	task.delay(Config.UI.Notifications.DisplayTime, function()
		frame:TweenPosition(
			UDim2.new(0.5, -200, 0, -100),
			Enum.EasingDirection.In,
			Enum.EasingStyle.Back,
			0.5,
			true,
			function()
				notification:Destroy()
			end
		)
	end)
end

-- Initialize when script runs
CatController:Initialize()

return CatController
