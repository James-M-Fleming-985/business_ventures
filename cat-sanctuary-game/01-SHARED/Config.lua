--[[
	Config.lua
	Game configuration and constants
	
	COPY TO: ReplicatedStorage/Shared/Config (ModuleScript)
	COPY ORDER: #1 (Copy this FIRST)
]]

local Config = {}

-- Game Information
Config.GAME_NAME = "Cat Sanctuary"
Config.VERSION = "0.1.0-MVP"

-- Cat Configuration
Config.CATS = {
	-- Starter cats (common)
	{
		Id = "tabby",
		Name = "Tabby Cat",
		Rarity = "Common",
		BaseStats = {
			Speed = 50,
			Agility = 40,
			Intelligence = 30,
			Cuteness = 60
		},
		Description = "A friendly street cat with basic skills"
	},
	{
		Id = "siamese",
		Name = "Siamese Cat",
		Rarity = "Common",
		BaseStats = {
			Speed = 60,
			Agility = 50,
			Intelligence = 50,
			Cuteness = 70
		},
		Description = "Smart and agile, great for puzzles"
	},
	-- Uncommon cats
	{
		Id = "persian",
		Name = "Persian Cat",
		Rarity = "Uncommon",
		BaseStats = {
			Speed = 30,
			Agility = 30,
			Intelligence = 40,
			Cuteness = 90
		},
		Description = "Adorable fluffy cat that attracts crowds"
	},
	{
		Id = "bengal",
		Name = "Bengal Cat",
		Rarity = "Uncommon",
		BaseStats = {
			Speed = 80,
			Agility = 70,
			Intelligence = 60,
			Cuteness = 75
		},
		Description = "Athletic and competitive"
	},
	-- Rare cats
	{
		Id = "mainecoon",
		Name = "Maine Coon",
		Rarity = "Rare",
		BaseStats = {
			Speed = 70,
			Agility = 60,
			Intelligence = 70,
			Cuteness = 85
		},
		Description = "Large and versatile champion"
	}
}

-- Rarity spawn chances (must add up to 100)
Config.RARITY_CHANCES = {
	Common = 70,     -- 70% chance
	Uncommon = 23,   -- 23% chance
	Rare = 6,        -- 6% chance
	Legendary = 1    -- 1% chance
}

-- Skill Configuration
Config.SKILLS = {
	Speed = {
		MaxLevel = 100,
		TrainingCost = function(currentLevel)
			return math.floor(100 * (1.15 ^ currentLevel))
		end
	},
	Agility = {
		MaxLevel = 100,
		TrainingCost = function(currentLevel)
			return math.floor(100 * (1.15 ^ currentLevel))
		end
	},
	Intelligence = {
		MaxLevel = 100,
		TrainingCost = function(currentLevel)
			return math.floor(100 * (1.15 ^ currentLevel))
		end
	},
	Cuteness = {
		MaxLevel = 100,
		TrainingCost = function(currentLevel)
			return math.floor(100 * (1.15 ^ currentLevel))
		end
	}
}

-- Mini-Game Configuration
Config.MINI_GAMES = {
	Race = {
		Name = "Sprint Race",
		Description = "Fast cats compete in a race",
		MinPlayers = 2,
		MaxPlayers = 8,
		Duration = 60, -- seconds
		PrimaryStat = "Speed",
		SecondaryStat = "Agility",
		EntryFee = 0, -- Free to play (charity earned from performance)
		RewardMultiplier = 1.0
	},
	Agility = {
		Name = "Agility Course",
		Description = "Navigate obstacles quickly",
		MinPlayers = 2,
		MaxPlayers = 8,
		Duration = 90,
		PrimaryStat = "Agility",
		SecondaryStat = "Speed",
		EntryFee = 0,
		RewardMultiplier = 1.2
	}
}

-- Currency Configuration
Config.CURRENCY = {
	StartingAmount = 1000,
	MaxAmount = 999999999,
	
	-- Earnings from mini-games
	WinBonus = 500,
	PlaceBonus = {
		[1] = 500,  -- 1st place
		[2] = 300,  -- 2nd place
		[3] = 150,  -- 3rd place
	},
	ParticipationReward = 50,
	
	-- Audience multiplier (based on cat cuteness)
	AudienceMultiplier = function(cuteness)
		return 1 + (cuteness / 200) -- Up to 1.5x at 100 cuteness
	end
}

-- Building Configuration
Config.BUILDINGS = {
	-- Starter buildings
	{
		Id = "basic_shelter",
		Name = "Basic Shelter",
		Type = "Housing",
		Cost = 500,
		Material = "Wood",
		Capacity = 2, -- Number of cats
		Description = "Simple wooden shelter for cats"
	},
	{
		Id = "food_station",
		Name = "Food Station",
		Type = "Utility",
		Cost = 200,
		Material = "Wood",
		Description = "Keeps cats fed and happy"
	},
	{
		Id = "training_area",
		Name = "Training Area",
		Type = "Training",
		Cost = 800,
		Material = "Wood",
		Description = "Train your cats' skills"
	},
	-- Upgraded buildings
	{
		Id = "stone_shelter",
		Name = "Stone Shelter",
		Type = "Housing",
		Cost = 5000,
		Material = "Stone",
		Capacity = 4,
		Description = "Sturdy stone shelter"
	},
	{
		Id = "gold_mansion",
		Name = "Gold Mansion",
		Type = "Housing",
		Cost = 50000,
		Material = "Gold",
		Capacity = 8,
		Description = "Luxurious golden mansion"
	},
	{
		Id = "diamond_palace",
		Name = "Diamond Palace",
		Type = "Housing",
		Cost = 500000,
		Material = "Diamond",
		Capacity = 16,
		Description = "Ultimate cat palace"
	}
}

-- Material tiers
Config.MATERIALS = {
	{Name = "Wood", Tier = 1, Multiplier = 1.0},
	{Name = "Stone", Tier = 2, Multiplier = 1.5},
	{Name = "Brick", Tier = 3, Multiplier = 2.0},
	{Name = "Iron", Tier = 4, Multiplier = 3.0},
	{Name = "Gold", Tier = 5, Multiplier = 5.0},
	{Name = "Emerald", Tier = 6, Multiplier = 8.0},
	{Name = "Diamond", Tier = 7, Multiplier = 12.0}
}

-- Player Configuration
Config.PLAYER = {
	MaxCats = 10,              -- Starting capacity
	MaxCatsWithVIP = 25,       -- With VIP game pass
	MaxSanctuaryPlots = 1,     -- Starting plots
	MaxSanctuaryPlotsWithVIP = 3,
	SaveInterval = 300,        -- Auto-save every 5 minutes
	StartingTrophies = 0,      -- Start at 0 trophies
}

-- Trophy/Ranking System
Config.TROPHIES = {
	-- Trophy gains/losses per place
	Rewards = {
		[1] = 30,   -- 1st place: +30 trophies
		[2] = 20,   -- 2nd place: +20 trophies
		[3] = 10,   -- 3rd place: +10 trophies
		[4] = 5,    -- 4th place: +5 trophies
		[5] = 0,    -- 5th place: 0 trophies
		-- Below 5th = lose trophies
	},
	
	-- Trophy loss for poor performance
	LossAmount = function(place, totalPlayers)
		if place <= 5 then return 0 end
		-- Last place loses more
		local positionFromBottom = totalPlayers - place + 1
		return math.min(positionFromBottom * 5, 20) -- Max -20 trophies
	end,
	
	-- Trophy loss protection (can't go below 0)
	MinTrophies = 0,
	
	-- Bonus trophies for win streaks
	WinStreakBonus = {
		[3] = 5,   -- 3 wins in a row: +5 bonus
		[5] = 10,  -- 5 wins in a row: +10 bonus
		[10] = 25, -- 10 wins in a row: +25 bonus
	}
}

-- League/Rank System
Config.LEAGUES = {
	{
		Name = "Rookie",
		MinTrophies = 0,
		MaxTrophies = 99,
		Icon = "🐱",
		Color = Color3.fromRGB(139, 69, 19), -- Brown
		Reward = 500, -- Currency reward for reaching this league
	},
	{
		Name = "Bronze",
		MinTrophies = 100,
		MaxTrophies = 299,
		Icon = "🥉",
		Color = Color3.fromRGB(205, 127, 50), -- Bronze
		Reward = 1000,
	},
	{
		Name = "Silver",
		MinTrophies = 300,
		MaxTrophies = 599,
		Icon = "🥈",
		Color = Color3.fromRGB(192, 192, 192), -- Silver
		Reward = 2500,
	},
	{
		Name = "Gold",
		MinTrophies = 600,
		MaxTrophies = 999,
		Icon = "🥇",
		Color = Color3.fromRGB(255, 215, 0), -- Gold
		Reward = 5000,
	},
	{
		Name = "Platinum",
		MinTrophies = 1000,
		MaxTrophies = 1499,
		Icon = "💎",
		Color = Color3.fromRGB(229, 228, 226), -- Platinum
		Reward = 10000,
	},
	{
		Name = "Diamond",
		MinTrophies = 1500,
		MaxTrophies = 1999,
		Icon = "💠",
		Color = Color3.fromRGB(185, 242, 255), -- Diamond blue
		Reward = 20000,
	},
	{
		Name = "Master",
		MinTrophies = 2000,
		MaxTrophies = 2999,
		Icon = "👑",
		Color = Color3.fromRGB(138, 43, 226), -- Purple
		Reward = 50000,
	},
	{
		Name = "Champion",
		MinTrophies = 3000,
		MaxTrophies = 999999,
		Icon = "🏆",
		Color = Color3.fromRGB(255, 0, 0), -- Red/Gold
		Reward = 100000,
	}
}

-- Season System
Config.SEASONS = {
	Enabled = true,
	DurationDays = 30,        -- Season lasts 30 days
	TrophyDecay = 0.5,        -- Keep 50% of trophies above certain threshold
	DecayThreshold = 1000,    -- Trophies above 1000 decay at season end
	
	-- Season end rewards based on final league
	EndRewards = {
		Rookie = {Currency = 1000},
		Bronze = {Currency = 3000},
		Silver = {Currency = 7500},
		Gold = {Currency = 15000},
		Platinum = {Currency = 30000},
		Diamond = {Currency = 60000},
		Master = {Currency = 150000},
		Champion = {Currency = 300000},
	}
}

-- Leaderboard Configuration
Config.LEADERBOARDS = {
	UpdateInterval = 60,      -- Update every 60 seconds
	TopPlayersShown = 100,    -- Show top 100 on global leaderboard
	FriendsShown = 20,        -- Show top 20 friends
	
	Categories = {
		"Trophies",           -- Main competitive ranking
		"TotalCurrency",      -- Richest players
		"CatsRescued",        -- Most cats collected
		"GamesWon",           -- Total wins
		"HighestLevel",       -- Highest level cat
	}
}

-- Game Pass IDs (set these after creating in Roblox)
Config.GAME_PASSES = {
	VIP = 0,              -- TODO: Replace with actual ID
	PremiumBuilder = 0,   -- TODO: Replace with actual ID
	SpeedTrainer = 0,     -- TODO: Replace with actual ID
	MegaSanctuary = 0     -- TODO: Replace with actual ID
}

-- Developer Product IDs (set these after creating)
Config.DEV_PRODUCTS = {
	Currency_Small = 0,   -- 5,000 charity ($0.99)
	Currency_Medium = 0,  -- 15,000 charity ($2.99)
	Currency_Large = 0,   -- 50,000 charity ($7.99)
	RareCatEgg = 0,      -- Guaranteed rare+ cat ($1.99)
}

-- UI Configuration
Config.UI = {
	Colors = {
		Primary = Color3.fromRGB(255, 182, 193),    -- Light pink
		Secondary = Color3.fromRGB(255, 218, 185),  -- Peach
		Accent = Color3.fromRGB(147, 112, 219),     -- Purple
		Success = Color3.fromRGB(144, 238, 144),    -- Light green
		Warning = Color3.fromRGB(255, 215, 0),      -- Gold
		Error = Color3.fromRGB(255, 99, 71),        -- Tomato
	},
	Notifications = {
		DisplayTime = 3, -- seconds
	}
}

-- Debug Configuration
Config.DEBUG = {
	Enabled = true,  -- Set to false in production
	StartingCurrency = 10000,  -- For testing
	UnlockAllCats = false,     -- For testing
	SkipTutorial = true        -- For testing
}

return Config
