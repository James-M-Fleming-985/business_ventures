--[[
	Utils_Test.lua
	Unit tests for Utils module
	
	HOW TO USE:
	1. Copy to ServerScriptService/Tests/Utils_Test
	2. Run from Command Bar: require(ServerScriptService.Tests.Utils_Test).RunAll()
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Utils = require(ReplicatedStorage.Shared.Utils)

local UtilsTest = {}

function UtilsTest.TestFormatNumber()
	assert(Utils.FormatNumber(1000) == "1,000", "1000 should format to 1,000")
	assert(Utils.FormatNumber(1000000) == "1,000,000", "1000000 should format to 1,000,000")
	assert(Utils.FormatNumber(123) == "123", "123 should remain 123")
	assert(Utils.FormatNumber(0) == "0", "0 should remain 0")
end

function UtilsTest.TestFormatNumberShort()
	assert(Utils.FormatNumberShort(999) == "999", "999 should remain 999")
	assert(Utils.FormatNumberShort(1000) == "1.0K", "1000 should be 1.0K")
	assert(Utils.FormatNumberShort(1500) == "1.5K", "1500 should be 1.5K")
	assert(Utils.FormatNumberShort(1000000) == "1.0M", "1000000 should be 1.0M")
	assert(Utils.FormatNumberShort(1500000) == "1.5M", "1500000 should be 1.5M")
end

function UtilsTest.TestFormatTime()
	assert(Utils.FormatTime(0) == "00:00", "0 seconds should be 00:00")
	assert(Utils.FormatTime(30) == "00:30", "30 seconds should be 00:30")
	assert(Utils.FormatTime(60) == "01:00", "60 seconds should be 01:00")
	assert(Utils.FormatTime(125) == "02:05", "125 seconds should be 02:05")
end

function UtilsTest.TestClamp()
	assert(Utils.Clamp(5, 0, 10) == 5, "5 clamped to [0, 10] should be 5")
	assert(Utils.Clamp(-5, 0, 10) == 0, "-5 clamped to [0, 10] should be 0")
	assert(Utils.Clamp(15, 0, 10) == 10, "15 clamped to [0, 10] should be 10")
end

function UtilsTest.TestLerp()
	assert(Utils.Lerp(0, 10, 0) == 0, "Lerp at t=0 should be start")
	assert(Utils.Lerp(0, 10, 1) == 10, "Lerp at t=1 should be end")
	assert(Utils.Lerp(0, 10, 0.5) == 5, "Lerp at t=0.5 should be middle")
end

function UtilsTest.TestDeepCopy()
	local original = {
		a = 1,
		b = {
			c = 2,
			d = {e = 3}
		}
	}
	
	local copy = Utils.DeepCopy(original)
	
	-- Verify values match
	assert(copy.a == original.a, "Top level should match")
	assert(copy.b.c == original.b.c, "Nested level should match")
	assert(copy.b.d.e == original.b.d.e, "Deep nested level should match")
	
	-- Verify it's a true copy
	copy.b.c = 999
	assert(original.b.c == 2, "Original should not be modified")
end

function UtilsTest.TestWeightedRandom()
	-- Test deterministic cases
	local chances = {OnlyOption = 100}
	local result = Utils.WeightedRandom(chances)
	assert(result == "OnlyOption", "Should always return the only option")
	
	-- Test distribution (probabilistic)
	local results = {Common = 0, Rare = 0}
	local chances2 = {Common = 80, Rare = 20}
	
	for i = 1, 1000 do
		local pick = Utils.WeightedRandom(chances2)
		results[pick] = results[pick] + 1
	end
	
	-- Common should be roughly 4x more than Rare
	local ratio = results.Common / results.Rare
	assert(ratio > 2 and ratio < 6, "Distribution should be roughly 4:1")
end

function UtilsTest.TestExperienceForLevel()
	local exp1 = Utils.ExperienceForLevel(1)
	local exp2 = Utils.ExperienceForLevel(2)
	
	assert(exp1 > 0, "Level 1 should require exp")
	assert(exp2 > exp1, "Higher levels should require more exp")
end

function UtilsTest.TestCalculateGamePerformance()
	-- 70 primary, 30 secondary = perfect 100
	local perf1 = Utils.CalculateGamePerformance(100, 100)
	assert(perf1 == 100, "Perfect stats should give 100")
	
	-- 0 primary, 0 secondary = 0
	local perf2 = Utils.CalculateGamePerformance(0, 0)
	assert(perf2 == 0, "Zero stats should give 0")
	
	-- Primary matters more
	local perf3 = Utils.CalculateGamePerformance(100, 0)
	local perf4 = Utils.CalculateGamePerformance(0, 100)
	assert(perf3 > perf4, "Primary stat should matter more")
end

function UtilsTest.RunAll()
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	print("🧪 Running Utils Tests...")
	print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	
	local tests = {
		"TestFormatNumber",
		"TestFormatNumberShort",
		"TestFormatTime",
		"TestClamp",
		"TestLerp",
		"TestDeepCopy",
		"TestWeightedRandom",
		"TestExperienceForLevel",
		"TestCalculateGamePerformance"
	}
	
	local passed = 0
	local failed = 0
	
	for _, testName in ipairs(tests) do
		local success, errorMsg = pcall(UtilsTest[testName])
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

return UtilsTest
