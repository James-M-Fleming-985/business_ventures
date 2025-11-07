--[[
	Types.lua
	Type definitions for better code documentation and IntelliSense
	
	COPY TO: ReplicatedStorage/Shared/Types (ModuleScript)
	COPY ORDER: #2
]]

local Types = {}

--[=[
	@type CatData table
	@within Types
	Represents a cat owned by a player
	
	@field Id string -- Unique instance ID
	@field CatType string -- Cat breed/type ID
	@field Name string -- Custom name given by player
	@field Level number -- Overall level
	@field Experience number -- XP towards next level
	@field Stats table -- {Speed, Agility, Intelligence, Cuteness}
	@field Rarity string -- "Common", "Uncommon", "Rare", "Legendary"
	@field Skills table -- Trained skill levels
	@field Friendship number -- Relationship with player (0-100)
	@field TimeAcquired number -- Unix timestamp
]=]
export type CatData = {
	Id: string,
	CatType: string,
	Name: string,
	Level: number,
	Experience: number,
	Stats: {
		Speed: number,
		Agility: number,
		Intelligence: number,
		Cuteness: number
	},
	Rarity: string,
	Skills: {[string]: number},
	Friendship: number,
	TimeAcquired: number
}

--[=[
	@type PlayerData table
	@within Types
	All data saved per player
	
	@field UserId number -- Roblox user ID
	@field Currency number -- Charity money
	@field Cats table -- Array of CatData
	@field Sanctuary table -- Building/decoration data
	@field Achievements table -- Unlocked achievements
	@field Statistics table -- Gameplay stats
	@field Settings table -- Player preferences
	@field LastLogin number -- Unix timestamp
]=]
export type PlayerData = {
	UserId: number,
	Currency: number,
	Cats: {CatData},
	Sanctuary: {
		Buildings: {BuildingData},
		Decorations: {DecorationData},
		Material: string,
		PlotSize: number
	},
	Achievements: {[string]: boolean},
	Statistics: {
		TotalEarned: number,
		TotalSpent: number,
		GamesPlayed: number,
		GamesWon: number,
		CatsRescued: number,
		TimePlayed: number,
		HighestLevel: number
	},
	Settings: {
		MusicEnabled: boolean,
		SFXEnabled: boolean,
		NotificationsEnabled: boolean
	},
	GamePasses: {[string]: boolean},
	Trophies: number,
	HighestTrophies: number,
	CurrentLeague: string,
	WinStreak: number,
	SeasonData: {
		SeasonId: number,
		StartTrophies: number,
		HighestThisSeason: number
	},
	LastLogin: number
}

--[=[
	@type BuildingData table
	@within Types
	Represents a building in the sanctuary
]=]
export type BuildingData = {
	Id: string,
	BuildingType: string,
	Position: Vector3,
	Rotation: number,
	Material: string,
	Level: number,
	PlacedAt: number
}

--[=[
	@type DecorationData table
	@within Types
	Represents a decoration in the sanctuary
]=]
export type DecorationData = {
	Id: string,
	DecorationType: string,
	Position: Vector3,
	Rotation: number
}

--[=[
	@type MiniGameResult table
	@within Types
	Result of a mini-game competition
]=]
export type MiniGameResult = {
	GameType: string,
	Players: {
		{
			UserId: number,
			CatId: string,
			Score: number,
			Place: number,
			EarnedCurrency: number
		}
	},
	Duration: number,
	Timestamp: number
}

--[=[
	@type ShopItem table
	@within Types
	Item available for purchase
]=]
export type ShopItem = {
	Id: string,
	Name: string,
	Description: string,
	Category: string, -- "Cats", "Buildings", "Decorations", "Upgrades"
	Cost: number,
	Currency: string, -- "Charity" or "Robux"
	Icon: string, -- Asset ID or path
	Requirements: {
		MinLevel: number?,
		RequiredBuilding: string?,
		GamePass: string?
	}?
}

--[=[
	@type LeaderboardEntry table
	@within Types
	Entry in a leaderboard
]=]
export type LeaderboardEntry = {
	UserId: number,
	DisplayName: string,
	Value: number,
	Rank: number
}

return Types
