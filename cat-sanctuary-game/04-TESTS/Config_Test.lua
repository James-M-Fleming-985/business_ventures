--[[
	Config_Test.lua
	Validation tests for game configuration
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage.Shared.Config)

local ConfigTest = {}

function ConfigTest.TestGameInfoExists()
	assert(Config.GAME_NAME ~= nil, "GAME_NAME should be defined")
	assert(Config.VERSION ~= nil, "VERSION should be defined")
end

function ConfigTest.TestCatsConfigured()
	assert(#Config.CATS > 0, "Should have at least one cat type")
	
	for _, cat in ipairs(Config.CATS) do
		assert(cat.Id, "Cat should have Id")
		assert(cat.Name, "Cat should have Name")
		assert(cat.Rarity, "Cat should have Rarity")
		assert(cat.BaseStats, "Cat should have BaseStats")
		assert(cat.BaseStats.Speed, "Cat should have Speed stat")
		assert(cat.BaseStats.Agility, "Cat should have Agility stat")
		assert(cat.BaseStats.Intelligence, "Cat should have Intelligence stat")
		assert(cat.BaseStats.Cuteness, "Cat should have Cuteness stat")
	end
end

function ConfigTest.TestRarityChances()
	local total = 0
	for _, chance in pairs(Config.RARITY_CHANCES) do
		total = total + chance
	end
	assert(total == 100, "Rarity chances should sum to 100")
end

function ConfigTest.TestMiniGamesConfigured()
	assert(Config.MINI_GAMES.Race, "Race mini-game should be configured")
	assert(Config.MINI_GAMES.Agility, "Agility mini-game should be configured")
	
	for gameType, gameConfig in pairs(Config.MINI_GAMES) do
		assert(gameConfig.Name, gameType .. " should have Name")
		assert(gameConfig.MinPlayers, gameType .. " should have MinPlayers")
		assert(gameConfig.MaxPlayers, gameType .. " should have MaxPlayers")
		assert(gameConfig.Duration, gameType .. " should have Duration")
		assert(gameConfig.PrimaryStat, gameType .. " should have PrimaryStat")
		assert(gameConfig.MinPlayers <= gameConfig.MaxPlayers, "MinPlayers should be <= MaxPlayers")
	end
end

function ConfigTest.TestBuildingsConfigured()
	assert(#Config.BUILDINGS > 0, "Should have at least one building")
	
	for _, building in ipairs(Config.BUILDINGS) do
		assert(building.Id, "Building should have Id")
		assert(building.Name, "Building should have Name")
		assert(building.Cost >= 0, "Building cost should be non-negative")
	end
end

function ConfigTest.TestMaterialsConfigured()
	assert(#Config.MATERIALS > 0, "Should have at least one material")
	
	local prevTier = 0
	for _, material in ipairs(Config.MATERIALS) do
		assert(material.Name, "Material should have Name")
		assert(material.Tier, "Material should have Tier")
		assert(material.Multiplier, "Material should have Multiplier")
		assert(material.Tier > prevTier, "Materials should be in tier order")
		prevTier = material.Tier
	end
end

function ConfigTest.TestCurrencyConfig()
	assert(Config.CURRENCY.StartingAmount > 0, "Should have positive starting currency")
	assert(Config.CURRENCY.MaxAmount > Config.CURRENCY.StartingAmount, "Max should be greater than starting")
end

function ConfigTest.RunAll()
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	print("🧪 Running Config Tests...")
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	
	local tests = {
		"TestGameInfoExists",
		"TestCatsConfigured",
		"TestRarityChances",
		"TestMiniGamesConfigured",
		"TestBuildingsConfigured",
		"TestMaterialsConfigured",
		"TestCurrencyConfig"
	}
	
	local passed = 0
	local failed = 0
	
	for _, testName in ipairs(tests) do
		local success, errorMsg = pcall(ConfigTest[testName])
		if success then
			print(string.format("✅ PASS: %s", testName))
			passed = passed + 1
		else
			warn(string.format("❌ FAIL: %s", testName))
			warn("   Error:", errorMsg)
			failed = failed + 1
		end
	end
	
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	print(string.format("📊 Results: %d passed, %d failed", passed, failed))
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	
	return passed, failed
end

return ConfigTest
