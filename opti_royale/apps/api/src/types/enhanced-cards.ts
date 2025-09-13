/**
 * Enhanced Card Type System
 * Based on Official Clash Royale API + Detailed Game Mechanics
 */

export enum CardType {
  TROOP = "TROOP",
  BUILDING = "BUILDING", 
  SPELL = "SPELL"
}

export enum TargetingType {
  BUILDINGS_ONLY = "BUILDINGS_ONLY",           // Giant, Hog Rider, Balloon
  TROOPS_ONLY = "TROOPS_ONLY",                 // Mini P.E.K.K.A, Bandit  
  BOTH_TARGETS = "BOTH_TARGETS",               // Knight, Prince, Archers
  GROUND_TROOPS_ONLY = "GROUND_TROOPS_ONLY",   // Cannon (building)
  AREA_DAMAGE = "AREA_DAMAGE",                 // Fireball, Arrows (spells)
  MULTI_TARGET = "MULTI_TARGET",               // Lightning (spell)
  NONE = "NONE"                                // Tombstone (spawner only)
}

export enum SpeedType {
  SLOW = "SLOW",         // 0.5-0.8 tiles/sec
  MEDIUM = "MEDIUM",     // 1.0-1.2 tiles/sec  
  FAST = "FAST",         // 1.4-1.6 tiles/sec
  VERY_FAST = "VERY_FAST" // 1.8-2.0+ tiles/sec
}

export enum RarityType {
  COMMON = "common",
  RARE = "rare", 
  EPIC = "epic",
  LEGENDARY = "legendary",
  CHAMPION = "champion"
}

export interface EnhancedCard {
  // Official API Data
  id: number;
  name: string;
  elixirCost: number;
  rarity: RarityType;
  maxLevel: number;
  canEvolve: boolean;
  iconUrls: {
    medium?: string;
    evolutionMedium?: string;
  };
  
  // Enhanced Game Mechanics
  type: CardType;
  targeting: TargetingType;
  sightRange?: number;        // Tiles
  attackRange?: number;       // Tiles  
  speed?: SpeedType;
  hitpoints?: number;         // At standard level
  damage?: number;            // At standard level
  attackSpeed?: number;       // Seconds between attacks
  
  // Special Abilities
  splashDamage?: boolean;
  splashRadius?: number;
  chargeAbility?: boolean;
  dashAbility?: boolean;
  flyingUnit?: boolean;
  hiddenWhenIdle?: boolean;
  
  // Building-Specific
  lifetime?: number;          // Seconds (for buildings)
  buildingPull?: boolean;     // Can pull building-targeting troops
  deadZone?: number;          // Minimum attack range (Mortar)
  
  // Spell-Specific  
  radius?: number;            // Spell radius
  knockback?: boolean;
  stun?: number;              // Stun duration
  targets?: number;           // Number of targets (Lightning)
  slow?: number;              // Slow duration
  
  // Special Mechanics
  rampingDamage?: boolean;    // Inferno Tower/Dragon
  maxDamage?: number;         // Max ramping damage
  lightningAura?: {           // Electro Giant
    range: number;
    damage: number;
    effect: string;
  };
  spearGoblins?: {            // Goblin Giant
    count: number;
    targeting: TargetingType;
    range: number;
    damage: number;
  };
  spawnsOnDeath?: {           // Tombstone, Golem
    unit: string;
    count: number;
  };
  spawnsOverTime?: {          // Spawner buildings
    unit: string;
    count: number;
    interval: number;
  };
  
  description: string;
}

export interface GameMechanics {
  buildingPull: {
    enabled: boolean;
    range: number;              // Standard 5.5 tiles
    vulnerableTargeting: TargetingType[]; // BUILDINGS_ONLY cards
    immuneTargeting: TargetingType[];     // TROOPS_ONLY, BOTH_TARGETS
  };
  
  sightRanges: {
    standard: 5.5;             // Most cards
    extended: 6.0;             // Musketeer, Inferno Tower
    longRange: 7.0;            // X-Bow, Mortar  
    princess: 9.0;             // Princess special range
  };
  
  cardInteractions: {
    buildingTargeters: string[]; // Affected by building pull
    troopTargeters: string[];   // Immune to building pull
    versatileUnits: string[];   // Target closest enemy
  };
}

export const CARD_INTERACTIONS: GameMechanics = {
  buildingPull: {
    enabled: true,
    range: 5.5,
    vulnerableTargeting: [TargetingType.BUILDINGS_ONLY],
    immuneTargeting: [TargetingType.TROOPS_ONLY, TargetingType.BOTH_TARGETS]
  },
  
  sightRanges: {
    standard: 5.5,
    extended: 6.0, 
    longRange: 7.0,
    princess: 9.0
  },
  
  cardInteractions: {
    buildingTargeters: [
      "Giant", "Golem", "Hog Rider", "Balloon", "Royal Giant",
      "Electro Giant", "Goblin Giant", "Ram Rider", "Mega Knight"
    ],
    troopTargeters: [
      "Mini P.E.K.K.A", "Bandit", "Inferno Dragon", "Lumberjack"
    ],
    versatileUnits: [
      "Knight", "Prince", "Dark Prince", "Valkyrie", "Archers",
      "Musketeer", "Wizard", "Witch", "Baby Dragon"
    ]
  }
};

export class CardMechanicsEngine {
  
  static isBuildingTargeter(card: EnhancedCard): boolean {
    return card.targeting === TargetingType.BUILDINGS_ONLY;
  }
  
  static isTroopTargeter(card: EnhancedCard): boolean {
    return card.targeting === TargetingType.TROOPS_ONLY;
  }
  
  static canBePulledByBuilding(card: EnhancedCard): boolean {
    return this.isBuildingTargeter(card);
  }
  
  static isVulnerableToSpells(card: EnhancedCard, spellRadius: number): boolean {
    // All ground troops vulnerable to ground-targeting spells
    return card.type === CardType.TROOP && !card.flyingUnit;
  }
  
  static calculateEffectiveRange(card: EnhancedCard): number {
    return Math.max(card.sightRange || 0, card.attackRange || 0);
  }
  
  static getCounterCards(targetCard: EnhancedCard, allCards: EnhancedCard[]): EnhancedCard[] {
    const counters: EnhancedCard[] = [];
    
    // Building targeters countered by buildings
    if (this.isBuildingTargeter(targetCard)) {
      counters.push(...allCards.filter(c => 
        c.type === CardType.BUILDING && c.buildingPull
      ));
    }
    
    // Flying units countered by air-targeting cards
    if (targetCard.flyingUnit) {
      counters.push(...allCards.filter(c =>
        c.targeting === TargetingType.BOTH_TARGETS || 
        c.targeting === TargetingType.AREA_DAMAGE
      ));
    }
    
    // Swarm units countered by splash damage
    if (targetCard.hitpoints && targetCard.hitpoints < 500) {
      counters.push(...allCards.filter(c => c.splashDamage));
    }
    
    return counters;
  }
  
  static analyzePlacementStrategy(card: EnhancedCard): string[] {
    const strategies: string[] = [];
    
    if (this.isBuildingTargeter(card)) {
      strategies.push("Place behind tank for tower targeting");
      strategies.push("Beware of defensive building pulls"); 
    }
    
    if (card.type === CardType.BUILDING && card.buildingPull) {
      strategies.push("Place to pull building-targeting troops");
      strategies.push("Position within 5.5 tiles of target path");
    }
    
    if (card.splashDamage) {
      strategies.push("Target grouped enemy units");
      strategies.push("Effective against swarm troops");
    }
    
    return strategies;
  }
}
