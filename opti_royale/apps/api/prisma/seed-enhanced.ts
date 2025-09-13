import { PrismaClient, CardType, CardRarity, AchievementCategory, AchievementRarity } from '@prisma/client'

const prisma = new PrismaClient()

// Enhanced Clash Royale Cards Data with Statistics
const cardsWithStats = [
  // Win Conditions
  {
    id: 'hog-rider', name: 'Hog Rider', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Win Condition',
    hitpoints: 1408, damage: 318, dps: 159.0, attackSpeed: 2.0, range: 1.0, speed: 'Very Fast',
    deployTime: 1.0, targetType: 'Buildings', description: 'Fast melee troop that targets buildings.',
    archetype: 'Cycle', synergies: ['knight', 'ice-spirit', 'fireball'], counters: ['cannon', 'tesla', 'tombstone']
  },
  {
    id: 'giant', name: 'Giant', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 5, category: 'Win Condition',
    hitpoints: 3275, damage: 318, dps: 159.0, attackSpeed: 2.0, range: 1.0, speed: 'Slow',
    deployTime: 1.0, targetType: 'Buildings', description: 'Slow but durable, only attacks buildings.',
    archetype: 'Beatdown', synergies: ['wizard', 'musketeer', 'baby-dragon'], counters: ['inferno-tower', 'pekka', 'mini-pekka']
  },
  {
    id: 'balloon', name: 'Balloon', type: CardType.TROOP, rarity: CardRarity.EPIC, cost: 5, category: 'Win Condition',
    hitpoints: 1318, damage: 1400, dps: 175.0, attackSpeed: 8.0, range: 1.0, speed: 'Medium',
    deployTime: 1.0, targetType: 'Buildings', description: 'Flying unit that targets buildings.',
    archetype: 'Beatdown', synergies: ['giant', 'lava-hound', 'freeze'], counters: ['inferno-dragon', 'mega-minion', 'musketeer']
  },
  {
    id: 'royal-giant', name: 'Royal Giant', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 6, category: 'Win Condition',
    hitpoints: 2544, damage: 286, dps: 163.4, attackSpeed: 1.75, range: 6.5, speed: 'Slow',
    deployTime: 1.0, targetType: 'Buildings', description: 'Long-range troop that targets buildings.',
    archetype: 'Control', synergies: ['lightning', 'fisherman', 'heal-spirit'], counters: ['inferno-tower', 'barbarians', 'mini-pekka']
  },

  // Support Troops
  {
    id: 'musketeer', name: 'Musketeer', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Support',
    hitpoints: 598, damage: 214, dps: 178.3, attackSpeed: 1.2, range: 6.0, speed: 'Medium',
    deployTime: 1.0, targetType: 'Air & Ground', description: 'Long-range troop that targets air and ground.',
    archetype: 'Control', synergies: ['giant', 'hog-rider', 'knight'], counters: ['fireball', 'lightning', 'rocket']
  },
  {
    id: 'wizard', name: 'Wizard', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 5, category: 'Support',
    hitpoints: 598, damage: 340, dps: 170.0, attackSpeed: 2.0, range: 5.0, speed: 'Medium',
    deployTime: 1.0, targetType: 'Air & Ground', splashRadius: 1.5, description: 'Area damage, air and ground targeting.',
    archetype: 'Beatdown', synergies: ['giant', 'golem', 'giant-skeleton'], counters: ['lightning', 'fireball', 'poison']
  },
  {
    id: 'valkyrie', name: 'Valkyrie', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Support',
    hitpoints: 1344, damage: 318, dps: 212.0, attackSpeed: 1.5, range: 1.0, speed: 'Medium',
    deployTime: 1.0, targetType: 'Ground', splashRadius: 1.2, description: '360° splash damage around her.',
    archetype: 'Control', synergies: ['hog-rider', 'miner', 'graveyard'], counters: ['inferno-dragon', 'pekka', 'mini-pekka']
  },
  {
    id: 'baby-dragon', name: 'Baby Dragon', type: CardType.TROOP, rarity: CardRarity.EPIC, cost: 4, category: 'Support',
    hitpoints: 1240, damage: 340, dps: 113.3, attackSpeed: 3.0, range: 3.5, speed: 'Fast',
    deployTime: 1.0, targetType: 'Air & Ground', splashRadius: 1.0, description: 'Flying troop with area damage.',
    archetype: 'Beatdown', synergies: ['giant', 'golem', 'lava-hound'], counters: ['mega-minion', 'inferno-dragon', 'electro-dragon']
  },

  // Small Troops & Cycle Cards
  {
    id: 'skeletons', name: 'Skeletons', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 1, category: 'Cycle',
    hitpoints: 67, damage: 67, dps: 67.0, attackSpeed: 1.0, range: 1.0, count: 3, speed: 'Fast',
    deployTime: 1.0, targetType: 'Ground', description: 'Three fast, unarmored melee fighters.',
    archetype: 'Cycle', synergies: ['knight', 'cannon', 'ice-spirit'], counters: ['zap', 'log', 'arrows']
  },
  {
    id: 'ice-spirit', name: 'Ice Spirit', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 1, category: 'Cycle',
    hitpoints: 254, damage: 95, splashRadius: 2.0, speed: 'Very Fast',
    deployTime: 1.0, targetType: 'Air & Ground', description: 'Freezes enemies in a small area.',
    archetype: 'Cycle', synergies: ['hog-rider', 'knight', 'cannon'], counters: ['any-ranged-unit']
  },
  {
    id: 'knight', name: 'Knight', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 3, category: 'Tank',
    hitpoints: 1568, damage: 176, dps: 125.7, attackSpeed: 1.4, range: 1.0, speed: 'Medium',
    deployTime: 1.0, targetType: 'Ground', description: 'A tough melee fighter.',
    archetype: 'Cycle', synergies: ['hog-rider', 'ice-spirit', 'skeletons'], counters: ['mini-pekka', 'valkyrie', 'dark-prince']
  },

  // Spells
  {
    id: 'fireball', name: 'Fireball', type: CardType.SPELL, rarity: CardRarity.RARE, cost: 4, category: 'Damage Spell',
    damage: 572, spellRadius: 2.5, description: 'Deals area damage and pushback.',
    archetype: 'Control', synergies: ['hog-rider', 'royal-giant', 'balloon'], counters: ['swarm-units', 'glass-cannons']
  },
  {
    id: 'zap', name: 'Zap', type: CardType.SPELL, rarity: CardRarity.COMMON, cost: 2, category: 'Small Spell',
    damage: 159, spellRadius: 2.5, description: 'Stuns and damages enemies in a small area.',
    archetype: 'Cycle', synergies: ['hog-rider', 'giant', 'balloon'], counters: ['inferno-tower', 'inferno-dragon', 'sparky']
  },
  {
    id: 'arrows', name: 'Arrows', type: CardType.SPELL, rarity: CardRarity.COMMON, cost: 3, category: 'Small Spell',
    damage: 243, spellRadius: 4.0, description: 'Deals area damage to a large area.',
    archetype: 'Control', synergies: ['hog-rider', 'balloon', 'royal-giant'], counters: ['minion-horde', 'skeleton-army', 'goblins']
  },
  {
    id: 'lightning', name: 'Lightning', type: CardType.SPELL, rarity: CardRarity.EPIC, cost: 6, category: 'Heavy Spell',
    damage: 864, spellRadius: 3.5, description: 'Strikes the three highest hitpoint enemies.',
    archetype: 'Beatdown', synergies: ['golem', 'giant', 'royal-giant'], counters: ['glass-cannons', 'buildings', 'wizards']
  },

  // Buildings
  {
    id: 'cannon', name: 'Cannon', type: CardType.BUILDING, rarity: CardRarity.COMMON, cost: 3, category: 'Defense',
    hitpoints: 870, damage: 159, dps: 106.0, attackSpeed: 1.5, range: 5.5, lifetime: 30.0,
    targetType: 'Ground', description: 'Defensive building that targets ground units.',
    archetype: 'Control', synergies: ['ice-spirit', 'skeletons', 'log'], counters: ['hog-rider', 'royal-hogs', 'ram-rider']
  },
  {
    id: 'inferno-tower', name: 'Inferno Tower', type: CardType.BUILDING, rarity: CardRarity.RARE, cost: 5, category: 'Defense',
    hitpoints: 1564, damage: 50, dps: 400, attackSpeed: 0.4, range: 6.0, lifetime: 40.0,
    targetType: 'Ground', description: 'Defensive building with increasing damage.',
    archetype: 'Control', synergies: ['tornado', 'ice-spirit', 'skeletons'], counters: ['zap', 'lightning', 'earthquake']
  },
  {
    id: 'tesla', name: 'Tesla', type: CardType.BUILDING, rarity: CardRarity.COMMON, cost: 4, category: 'Defense',
    hitpoints: 1020, damage: 190, dps: 190.0, attackSpeed: 1.0, range: 5.5, lifetime: 35.0,
    targetType: 'Air & Ground', description: 'Hidden defensive building that targets air and ground.',
    archetype: 'Control', synergies: ['ice-golem', 'tornado', 'log'], counters: ['lightning', 'earthquake', 'rocket']
  }
];

// Achievement System for Placement Analysis
const achievements = [
  // Placement Mastery Achievements
  {
    name: 'First Analysis',
    description: 'Complete your first placement analysis',
    category: AchievementCategory.PLACEMENT_MASTERY,
    rarity: AchievementRarity.COMMON,
    unlockCriteria: { type: 'placement_count', value: 1 },
    xpReward: 50
  },
  {
    name: 'Placement Expert',
    description: 'Complete 100 placement analyses',
    category: AchievementCategory.PLACEMENT_MASTERY,
    rarity: AchievementRarity.RARE,
    unlockCriteria: { type: 'placement_count', value: 100 },
    xpReward: 200
  },
  {
    name: 'Placement Perfectionist',
    description: 'Achieve a perfect 10/10 placement score',
    category: AchievementCategory.PLACEMENT_MASTERY,
    rarity: AchievementRarity.EPIC,
    unlockCriteria: { type: 'perfect_placement', value: 1 },
    xpReward: 300
  },
  {
    name: 'Improvement Master',
    description: 'Improve your average placement score by 2+ points',
    category: AchievementCategory.IMPROVEMENT,
    rarity: AchievementRarity.RARE,
    unlockCriteria: { type: 'score_improvement', value: 2.0 },
    xpReward: 250
  },
  {
    name: 'Card Master',
    description: 'Analyze placements for 25 different cards',
    category: AchievementCategory.CARD_MASTERY,
    rarity: AchievementRarity.EPIC,
    unlockCriteria: { type: 'unique_cards_analyzed', value: 25 },
    xpReward: 400
  },
  {
    name: 'Strategy Scholar',
    description: 'Analyze 50 different strategic scenarios',
    category: AchievementCategory.STRATEGY,
    rarity: AchievementRarity.LEGENDARY,
    unlockCriteria: { type: 'strategic_scenarios', value: 50 },
    xpReward: 500
  },
  {
    name: 'Community Contributor',
    description: 'Share your first placement analysis',
    category: AchievementCategory.SOCIAL,
    rarity: AchievementRarity.COMMON,
    unlockCriteria: { type: 'first_share', value: 1 },
    xpReward: 75
  }
];

async function main() {
  console.log('🌱 Starting enhanced database seed...')

  // Clear existing data (be careful in production!)
  console.log('🧹 Cleaning existing data...')
  await prisma.userAchievement.deleteMany()
  await prisma.achievement.deleteMany()
  await prisma.cardStats.deleteMany()
  await prisma.card.deleteMany()

  // Seed Cards with Enhanced Statistics
  console.log('🃏 Seeding Clash Royale cards with detailed statistics...')
  for (const cardData of cardsWithStats) {
    const { hitpoints, damage, dps, attackSpeed, range, speed, deployTime, targetType, 
            splashRadius, splashDamage, count, lifetime, spellRadius, spellDuration,
            synergies, counters, archetype, ...cardInfo } = cardData;

    // Create card
    const card = await prisma.card.create({
      data: {
        ...cardInfo,
        archetype,
        synergies: synergies ? JSON.stringify(synergies) : null,
        counters: counters ? JSON.stringify(counters) : null,
        tags: JSON.stringify([cardInfo.category, archetype]),
        gameVersion: 'current'
      }
    });

    // Create card statistics
    await prisma.cardStats.create({
      data: {
        cardId: card.id,
        gameVersion: 'current',
        hitpoints,
        damage,
        dps,
        attackSpeed,
        range,
        splashRadius,
        splashDamage,
        deployTime,
        lifetime,
        spellDuration,
        cost: card.cost,
        isActive: true
      }
    });

    console.log(`✅ Created ${card.name} with detailed statistics`);
  }
  console.log(`✅ Created ${cardsWithStats.length} cards with statistics`)

  // Seed Achievements
  console.log('🏆 Seeding achievements...')
  for (const achievement of achievements) {
    await prisma.achievement.create({
      data: {
        ...achievement,
        unlockCriteria: JSON.stringify(achievement.unlockCriteria)
      }
    })
  }
  console.log(`✅ Created ${achievements.length} achievements`)

  console.log('🎉 Enhanced database seed completed successfully!')
  console.log('📊 Cards now include:')
  console.log('   - Combat statistics (HP, damage, DPS)')
  console.log('   - Movement & deployment data')
  console.log('   - Area effects & special mechanics')
  console.log('   - Synergies & counter relationships')
  console.log('   - Version tracking for balance updates')
}

main()
  .catch((e) => {
    console.error('❌ Database seed failed:')
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
