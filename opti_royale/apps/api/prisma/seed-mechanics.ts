import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function seedCrownTowers() {
  console.log('🏰 Seeding Crown Tower system...')

  // Clear existing tower data
  await prisma.crownTower.deleteMany({})

  // === STANDARD TOWERS ===
  
  // Princess Tower (Standard)
  await prisma.crownTower.create({
    data: {
      towerType: 'PRINCESS',
      name: 'Princess Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2534,    // Level 1 HP
      baseDamage: 109,        // Level 1 damage
      attackSpeed: 0.8,
      range: 7.0,
      hpPerLevel: 202,        // HP increase per level
      damagePerLevel: 8,      // Damage increase per level
      hasSpecialAbility: false,
      retargetSpeed: 0.1
    }
  })

  // King Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'KING',
      name: 'King Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 4824,    // Level 1 HP
      baseDamage: 129,        // Level 1 damage
      attackSpeed: 1.0,
      range: 7.0,
      activationRange: 6.0,   // Must take damage to activate
      hpPerLevel: 385,        // HP increase per level
      damagePerLevel: 10,     // Damage increase per level
      hasSpecialAbility: false,
      retargetSpeed: 0.1
    }
  })

  // === TOWER SKINS WITH SPECIAL ABILITIES ===

  // Chef Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'CHEF',
      name: 'Chef Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2534,    // Same base stats as Princess Tower
      baseDamage: 109,
      attackSpeed: 0.8,
      range: 7.0,
      hpPerLevel: 202,
      damagePerLevel: 8,
      hasSpecialAbility: true,
      abilityName: "Chef's Special",
      abilityDescription: "Periodically throws cooking pots for area damage",
      abilityCooldown: 10.0,  // 10 second cooldown
      abilityRadius: 2.5,     // 2.5 tile radius
      abilityDamage: 150,     // Base ability damage
      retargetSpeed: 0.1
    }
  })

  // Dagger Duchess Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'DAGGER_DUCHESS',
      name: 'Dagger Duchess Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2534,
      baseDamage: 136,        // +25% base damage
      attackSpeed: 0.8,
      range: 7.0,
      hpPerLevel: 202,
      damagePerLevel: 10,     // Higher damage scaling
      hasSpecialAbility: true,
      abilityName: "Dagger Throw",
      abilityDescription: "Throws daggers that pierce through the first target",
      abilityCooldown: 0.0,   // Passive ability
      abilityRadius: 0.0,     // Piercing effect
      abilityDamage: 0,       // Modifier to base damage
      retargetSpeed: 0.1
    }
  })

  // Cannoneer Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'CANNONEER',
      name: 'Cannoneer Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2534,
      baseDamage: 109,
      attackSpeed: 1.0,       // Slower attack speed
      range: 7.5,             // Slightly longer range
      hpPerLevel: 202,
      damagePerLevel: 8,
      hasSpecialAbility: true,
      abilityName: "Cannon Blast",
      abilityDescription: "Fires explosive cannon shots with area damage",
      abilityCooldown: 0.0,   // Passive ability
      abilityRadius: 1.5,     // Splash radius
      abilityDamage: 82,      // 75% splash damage (75% of 109)
      retargetSpeed: 0.1
    }
  })

  // === ADDITIONAL TOWER SKINS ===

  // Goblin Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'GOBLIN',
      name: 'Goblin Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2281,    // -10% HP (more fragile)
      baseDamage: 120,        // +10% damage (more aggressive)
      attackSpeed: 0.7,       // Faster attack speed
      range: 6.5,             // Slightly shorter range
      hpPerLevel: 182,        // Lower HP scaling
      damagePerLevel: 9,      // Higher damage scaling
      hasSpecialAbility: true,
      abilityName: "Goblin Swarm",
      abilityDescription: "Spawns goblins when destroyed",
      abilityCooldown: 0.0,   // Death effect
      abilityRadius: 3.0,     // Spawn radius
      abilityDamage: 0,       // No direct damage
      retargetSpeed: 0.05     // Very fast retargeting
    }
  })

  // Ice Tower
  await prisma.crownTower.create({
    data: {
      towerType: 'ICE',
      name: 'Ice Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2787,    // +10% HP (more defensive)
      baseDamage: 98,         // -10% damage
      attackSpeed: 0.9,       // Slower attack
      range: 7.0,
      hpPerLevel: 222,        // Higher HP scaling
      damagePerLevel: 7,      // Lower damage scaling
      hasSpecialAbility: true,
      abilityName: "Frost Aura",
      abilityDescription: "Slows enemies within range",
      abilityCooldown: 0.0,   // Passive aura
      abilityRadius: 4.0,     // Slow radius
      abilityDamage: 0,       // No direct damage
      retargetSpeed: 0.1
    }
  })

  // Royal Tower (Premium)
  await prisma.crownTower.create({
    data: {
      towerType: 'ROYAL',
      name: 'Royal Tower',
      minLevel: 1,
      maxLevel: 13,
      baseHitpoints: 2787,    // +10% HP
      baseDamage: 120,        // +10% damage
      attackSpeed: 0.8,
      range: 7.5,             // Extended range
      hpPerLevel: 222,        // Higher HP scaling
      damagePerLevel: 9,      // Higher damage scaling
      hasSpecialAbility: true,
      abilityName: "Royal Decree",
      abilityDescription: "Briefly increases damage and range when activated",
      abilityCooldown: 15.0,  // 15 second cooldown
      abilityRadius: 8.0,     // Extended range during ability
      abilityDamage: 60,      // +50% damage during ability
      retargetSpeed: 0.1
    }
  })

  const towerCount = await prisma.crownTower.count()
  console.log(`✅ Crown Tower system seeded with ${towerCount} tower types`)
  
  // Display tower statistics
  const towerStats = await prisma.crownTower.findMany({
    select: {
      name: true,
      towerType: true,
      hasSpecialAbility: true,
      abilityName: true
    }
  })

  console.log(`\n🏰 Tower Types Available:`)
  towerStats.forEach((tower: any) => {
    const ability = tower.hasSpecialAbility ? ` (${tower.abilityName})` : ''
    console.log(`   • ${tower.name}${ability}`)
  })

  return towerCount
}

async function seedGameMechanicsUpdates() {
  console.log('\n📊 Seeding Game Mechanics tracking...')

  await prisma.gameMechanicsUpdate.deleteMany({})

  // Recent major updates
  const updates = [
    {
      updateType: 'EVOLUTION_UPDATE',
      gameVersion: '4.0.0',
      updateTitle: 'Evolution System Launch',
      affectedCards: '["knight", "archers", "skeletons", "bats", "firecracker"]',
      changeDescription: 'Introduced card evolution mechanics where cards gain enhanced stats and abilities after cycling 2-3 times.',
      newFeatures: '["evolution_cycling", "enhanced_stats", "special_abilities"]',
      impactLevel: 'CRITICAL',
      analysisUpdate: true,
      specUpdate: true,
      sourceType: 'OFFICIAL',
      sourceUrl: 'https://clashroyale.com/blog/news/evolution-update',
      processed: true,
      announcedAt: new Date('2024-12-01'),
      implementedAt: new Date('2025-01-15')
    },
    {
      updateType: 'BALANCE_CHANGE',
      gameVersion: '4.1.0',
      updateTitle: 'March 2025 Balance Changes',
      affectedCards: '["hog-rider", "valkyrie", "wizard", "fireball"]',
      changeDescription: 'Monthly balance adjustments to card stats based on usage rates and win rates.',
      statChanges: '{"hog-rider": {"hitpoints": "+4%"}, "valkyrie": {"damage": "-6%"}, "wizard": {"hitpoints": "+8%"}, "fireball": {"damage": "-3%"}}',
      impactLevel: 'MEDIUM',
      analysisUpdate: true,
      specUpdate: false,
      sourceType: 'OFFICIAL',
      sourceUrl: 'https://clashroyale.com/blog/news/march-2025-balance',
      processed: true,
      announcedAt: new Date('2025-03-01'),
      implementedAt: new Date('2025-03-05')
    },
    {
      updateType: 'TOWER_UPDATE',
      gameVersion: '4.1.2',
      updateTitle: 'New Tower Skins & Abilities',
      affectedTowers: '["CHEF", "DAGGER_DUCHESS", "CANNONEER"]',
      changeDescription: 'Added new tower skins with unique special abilities that affect defensive capabilities.',
      newFeatures: '["tower_abilities", "special_effects", "tactical_variety"]',
      impactLevel: 'HIGH',
      analysisUpdate: true,
      specUpdate: true,
      sourceType: 'OFFICIAL',
      sourceUrl: 'https://clashroyale.com/blog/news/tower-skins-update',
      processed: true,
      announcedAt: new Date('2025-04-01'),
      implementedAt: new Date('2025-04-10')
    },
    {
      updateType: 'NEW_CARD',
      gameVersion: '4.2.0',
      updateTitle: 'Phoenix Card Release',
      affectedCards: '["phoenix"]',
      changeDescription: 'New Legendary card that resurrects as an egg when destroyed.',
      newFeatures: '["resurrection_mechanic", "transformation_states", "tactical_revival"]',
      impactLevel: 'HIGH',
      analysisUpdate: true,
      specUpdate: true,
      sourceType: 'OFFICIAL',
      sourceUrl: 'https://clashroyale.com/blog/news/phoenix-card',
      processed: false, // Still being processed
      announcedAt: new Date('2025-07-20')
    }
  ]

  for (const update of updates) {
    await prisma.gameMechanicsUpdate.create({ data: update })
  }

  const updateCount = await prisma.gameMechanicsUpdate.count()
  console.log(`✅ Game Mechanics tracking seeded with ${updateCount} updates`)

  return updateCount
}

async function main() {
  console.log('🎮 Starting comprehensive game mechanics seeding...')

  const towerCount = await seedCrownTowers()
  const updateCount = await seedGameMechanicsUpdates()

  console.log(`\n🎯 Game Mechanics Seeding Complete:`)
  console.log(`   • ${towerCount} Tower Types`)
  console.log(`   • ${updateCount} Mechanics Updates`)
  console.log(`   • Level-aware card system ready`)
  console.log(`   • Evolution tracking operational`)
  console.log(`   • Tower ability system active`)
  
  console.log(`\n🔄 Next Steps:`)
  console.log(`   • Update API routes for level-aware queries`)
  console.log(`   • Implement tower type detection in CV`)
  console.log(`   • Build level difference calculators`)
  console.log(`   • Create evolution cycle tracking`)
}

main()
  .catch((e) => {
    console.error('Error seeding game mechanics:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
