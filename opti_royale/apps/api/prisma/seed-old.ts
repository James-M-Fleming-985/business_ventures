import { PrismaClient, CardType, CardRarity, AchievementCategory, AchievementRarity } from '@prisma/client'

const prisma = new PrismaClient()

// Clash Royale Cards Data
const cards = [
  // Win Conditions
  { id: 'hog-rider', name: 'Hog Rider', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Win Condition' },
  { id: 'giant', name: 'Giant', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 5, category: 'Win Condition' },
  { id: 'balloon', name: 'Balloon', type: CardType.TROOP, rarity: CardRarity.EPIC, cost: 5, category: 'Win Condition' },
  { id: 'golem', name: 'Golem', type: CardType.TROOP, rarity: CardRarity.EPIC, cost: 8, category: 'Win Condition' },
  { id: 'royal-giant', name: 'Royal Giant', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 6, category: 'Win Condition' },
  
  // Support Troops
  { id: 'musketeer', name: 'Musketeer', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Support' },
  { id: 'wizard', name: 'Wizard', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 5, category: 'Support' },
  { id: 'valkyrie', name: 'Valkyrie', type: CardType.TROOP, rarity: CardRarity.RARE, cost: 4, category: 'Support' },
  { id: 'baby-dragon', name: 'Baby Dragon', type: CardType.TROOP, rarity: CardRarity.EPIC, cost: 4, category: 'Support' },
  { id: 'electro-wizard', name: 'Electro Wizard', type: CardType.TROOP, rarity: CardRarity.LEGENDARY, cost: 4, category: 'Support' },
  
  // Small Troops
  { id: 'skeletons', name: 'Skeletons', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 1, category: 'Cycle' },
  { id: 'goblins', name: 'Goblins', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 2, category: 'Cycle' },
  { id: 'archers', name: 'Archers', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 3, category: 'Support' },
  { id: 'knight', name: 'Knight', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 3, category: 'Tank' },
  { id: 'ice-spirit', name: 'Ice Spirit', type: CardType.TROOP, rarity: CardRarity.COMMON, cost: 1, category: 'Cycle' },
  
  // Spells
  { id: 'fireball', name: 'Fireball', type: CardType.SPELL, rarity: CardRarity.RARE, cost: 4, category: 'Damage Spell' },
  { id: 'zap', name: 'Zap', type: CardType.SPELL, rarity: CardRarity.COMMON, cost: 2, category: 'Small Spell' },
  { id: 'lightning', name: 'Lightning', type: CardType.SPELL, rarity: CardRarity.EPIC, cost: 6, category: 'Heavy Spell' },
  { id: 'log', name: 'The Log', type: CardType.SPELL, rarity: CardRarity.LEGENDARY, cost: 2, category: 'Small Spell' },
  { id: 'arrows', name: 'Arrows', type: CardType.SPELL, rarity: CardRarity.COMMON, cost: 3, category: 'Small Spell' },
  
  // Buildings
  { id: 'cannon', name: 'Cannon', type: CardType.BUILDING, rarity: CardRarity.COMMON, cost: 3, category: 'Defense' },
  { id: 'inferno-tower', name: 'Inferno Tower', type: CardType.BUILDING, rarity: CardRarity.RARE, cost: 5, category: 'Defense' },
  { id: 'tesla', name: 'Tesla', type: CardType.BUILDING, rarity: CardRarity.COMMON, cost: 4, category: 'Defense' },
  { id: 'x-bow', name: 'X-Bow', type: CardType.BUILDING, rarity: CardRarity.EPIC, cost: 6, category: 'Win Condition' },
]

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
    name: 'Placement Perfectionist',
    description: 'Achieve a perfect 10/10 placement score',
    category: AchievementCategory.PLACEMENT_MASTERY,
    rarity: AchievementRarity.RARE,
    unlockCriteria: { type: 'perfect_placement', value: 1 },
    xpReward: 200
  },
  {
    name: 'Hog Rider Master',
    description: 'Analyze 25 Hog Rider placements',
    category: AchievementCategory.PLACEMENT_MASTERY,
    rarity: AchievementRarity.EPIC,
    unlockCriteria: { type: 'card_analysis_count', card: 'hog-rider', value: 25 },
    xpReward: 300
  },
  
  // Improvement Achievements
  {
    name: 'Getting Better',
    description: 'Improve your average placement score by 1 point',
    category: AchievementCategory.IMPROVEMENT,
    rarity: AchievementRarity.COMMON,
    unlockCriteria: { type: 'score_improvement', value: 1.0 },
    xpReward: 100
  },
  {
    name: 'Consistency Champion',
    description: 'Maintain a 7+ average placement score for a week',
    category: AchievementCategory.CONSISTENCY,
    rarity: AchievementRarity.RARE,
    unlockCriteria: { type: 'weekly_average', value: 7.0 },
    xpReward: 250
  },
  {
    name: 'Placement Prodigy',
    description: 'Achieve 8+ average score on 50 analyses',
    category: AchievementCategory.IMPROVEMENT,
    rarity: AchievementRarity.LEGENDARY,
    unlockCriteria: { type: 'high_average_count', average: 8.0, count: 50 },
    xpReward: 500
  },
  
  // Engagement Achievements
  {
    name: 'Daily Analyzer',
    description: 'Complete analyses on 7 consecutive days',
    category: AchievementCategory.CONSISTENCY,
    rarity: AchievementRarity.RARE,
    unlockCriteria: { type: 'daily_streak', value: 7 },
    xpReward: 200
  },
  {
    name: 'Video Veteran',
    description: 'Upload 10 gameplay videos',
    category: AchievementCategory.MILESTONE,
    rarity: AchievementRarity.COMMON,
    unlockCriteria: { type: 'video_upload_count', value: 10 },
    xpReward: 150
  },
  
  // Social Achievements
  {
    name: 'Share the Knowledge',
    description: 'Share your first improvement highlight',
    category: AchievementCategory.SOCIAL,
    rarity: AchievementRarity.COMMON,
    unlockCriteria: { type: 'first_share', value: 1 },
    xpReward: 75
  }
]

async function main() {
  console.log('🌱 Starting database seed...')

  // Clear existing data (be careful in production!)
  console.log('🧹 Cleaning existing data...')
  await prisma.userAchievement.deleteMany()
  await prisma.achievement.deleteMany()
  await prisma.card.deleteMany()

  // Seed Cards
  console.log('🃏 Seeding Clash Royale cards...')
  for (const card of cards) {
    await prisma.card.create({
      data: {
        ...card,
        tags: JSON.stringify([card.category])
      }
    })
  }
  console.log(`✅ Created ${cards.length} cards`)

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

  console.log('🎉 Database seed completed successfully!')
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
