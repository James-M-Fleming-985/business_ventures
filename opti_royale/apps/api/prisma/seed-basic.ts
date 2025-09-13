import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Clash Royale Cards Data (SQLite Compatible)
const cards = [
  // Win Conditions
  { id: 'hog-rider', name: 'Hog Rider', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 1408, damage: 318 },
  { id: 'giant', name: 'Giant', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 4256, damage: 358 },
  { id: 'balloon', name: 'Balloon', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 1974, damage: 1472 },
  { id: 'golem', name: 'Golem', cardType: 'TROOP', rarity: 'EPIC', cost: 8, hitpoints: 8032, damage: 452 },
  { id: 'royal-giant', name: 'Royal Giant', cardType: 'TROOP', rarity: 'COMMON', cost: 6, hitpoints: 3668, damage: 344, range: 6.5 },
  
  // Support Troops
  { id: 'musketeer', name: 'Musketeer', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 598, damage: 340, range: 6.0 },
  { id: 'wizard', name: 'Wizard', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 698, damage: 340, range: 5.5 },
  { id: 'valkyrie', name: 'Valkyrie', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 1344, damage: 297 },
  { id: 'baby-dragon', name: 'Baby Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 1200, damage: 340, range: 3.5 },
  { id: 'electro-wizard', name: 'Electro Wizard', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 598, damage: 192, range: 5.0 },
  
  // Small Troops
  { id: 'skeletons', name: 'Skeletons', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 91, damage: 91 },
  { id: 'goblins', name: 'Goblins', cardType: 'TROOP', rarity: 'COMMON', cost: 2, hitpoints: 169, damage: 169 },
  { id: 'archers', name: 'Archers', cardType: 'TROOP', rarity: 'COMMON', cost: 3, hitpoints: 304, damage: 127, range: 5.0 },
  { id: 'knight', name: 'Knight', cardType: 'TROOP', rarity: 'COMMON', cost: 3, hitpoints: 1344, damage: 183 },
  { id: 'ice-spirit', name: 'Ice Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 190, damage: 190 },
  
  // Spells
  { id: 'fireball', name: 'Fireball', cardType: 'SPELL', rarity: 'RARE', cost: 4, damage: 689 },
  { id: 'zap', name: 'Zap', cardType: 'SPELL', rarity: 'COMMON', cost: 2, damage: 192 },
  { id: 'lightning', name: 'Lightning', cardType: 'SPELL', rarity: 'EPIC', cost: 6, damage: 1218 },
  { id: 'log', name: 'The Log', cardType: 'SPELL', rarity: 'LEGENDARY', cost: 2, damage: 432 },
  { id: 'arrows', name: 'Arrows', cardType: 'SPELL', rarity: 'COMMON', cost: 3, damage: 243 },
  
  // Buildings
  { id: 'cannon', name: 'Cannon', cardType: 'BUILDING', rarity: 'COMMON', cost: 3, hitpoints: 828, damage: 276, range: 5.5 },
  { id: 'inferno-tower', name: 'Inferno Tower', cardType: 'BUILDING', rarity: 'RARE', cost: 5, hitpoints: 1508, damage: 50, range: 6.0 },
  { id: 'tesla', name: 'Tesla', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, hitpoints: 828, damage: 276, range: 5.5 },
  { id: 'x-bow', name: 'X-Bow', cardType: 'BUILDING', rarity: 'EPIC', cost: 6, hitpoints: 1630, damage: 53, range: 12.0 },
]

// Achievement System for Placement Analysis (SQLite Compatible)
const achievements = [
  // Placement Mastery Achievements
  {
    name: 'First Analysis',
    description: 'Complete your first placement analysis',
    category: 'PLACEMENT_MASTERY',
    rarity: 'COMMON',
    unlockCriteriaText: 'Complete 1 placement analysis',
    xpReward: 10,
  },
  {
    name: 'Analyzer',
    description: 'Complete 10 placement analyses',
    category: 'PLACEMENT_MASTERY',
    rarity: 'COMMON',
    unlockCriteriaText: 'Complete 10 placement analyses',
    xpReward: 50,
  },
  {
    name: 'Strategic Mind',
    description: 'Complete 50 placement analyses',
    category: 'PLACEMENT_MASTERY',
    rarity: 'RARE',
    unlockCriteriaText: 'Complete 50 placement analyses',
    xpReward: 100,
  },
  {
    name: 'Master Analyst',
    description: 'Complete 100 placement analyses',
    category: 'PLACEMENT_MASTERY',
    rarity: 'EPIC',
    unlockCriteriaText: 'Complete 100 placement analyses',
    xpReward: 250,
  },
  
  // Score-based Achievements
  {
    name: 'Good Placement',
    description: 'Achieve a placement score of 7.0 or higher',
    category: 'SKILL_DEVELOPMENT',
    rarity: 'COMMON',
    unlockCriteriaText: 'Get placement score >= 7.0',
    xpReward: 15,
  },
  {
    name: 'Excellent Placement',
    description: 'Achieve a placement score of 8.5 or higher',
    category: 'SKILL_DEVELOPMENT',
    rarity: 'RARE',
    unlockCriteriaText: 'Get placement score >= 8.5',
    xpReward: 30,
  },
  {
    name: 'Perfect Placement',
    description: 'Achieve a perfect placement score of 10.0',
    category: 'SKILL_DEVELOPMENT',
    rarity: 'LEGENDARY',
    unlockCriteriaText: 'Get placement score = 10.0',
    xpReward: 100,
  },
  
  // Improvement Achievements
  {
    name: 'Quick Learner',
    description: 'Improve your average score by 1.0 points',
    category: 'IMPROVEMENT',
    rarity: 'COMMON',
    unlockCriteriaText: 'Improve average score by 1.0',
    xpReward: 25,
  },
  {
    name: 'Dedicated Student',
    description: 'Improve your average score by 2.0 points',
    category: 'IMPROVEMENT',
    rarity: 'RARE',
    unlockCriteriaText: 'Improve average score by 2.0',
    xpReward: 50,
  },
  {
    name: 'Skill Master',
    description: 'Achieve an average score of 8.0 or higher',
    category: 'IMPROVEMENT',
    rarity: 'EPIC',
    unlockCriteriaText: 'Get average score >= 8.0',
    xpReward: 150,
  },
  
  // Milestone Achievements
  {
    name: 'Video Uploader',
    description: 'Upload your first video for analysis',
    category: 'MILESTONE',
    rarity: 'COMMON',
    unlockCriteriaText: 'Upload 1 video',
    xpReward: 20,
  },
  {
    name: 'Content Creator',
    description: 'Upload 10 videos for analysis',
    category: 'MILESTONE',
    rarity: 'RARE',
    unlockCriteriaText: 'Upload 10 videos',
    xpReward: 100,
  },
  {
    name: 'Analysis Expert',
    description: 'Upload 50 videos for analysis',
    category: 'MILESTONE',
    rarity: 'EPIC',
    unlockCriteriaText: 'Upload 50 videos',
    xpReward: 300,
  },
]

async function main() {
  console.log('🌱 Starting database seeding...')

  // Clear existing data
  console.log('🧹 Clearing existing data...')
  await prisma.userAchievement.deleteMany()
  await prisma.placementAnalysis.deleteMany()
  await prisma.video.deleteMany()
  await prisma.analyticsEvent.deleteMany()
  await prisma.progressTracking.deleteMany()
  await prisma.subscription.deleteMany()
  await prisma.user.deleteMany()
  await prisma.achievement.deleteMany()
  await prisma.card.deleteMany()

  // Seed cards
  console.log('🃏 Seeding Clash Royale cards...')
  for (const card of cards) {
    await prisma.card.create({
      data: {
        ...card,
        description: `${card.name} is a ${card.rarity.toLowerCase()} ${card.cardType.toLowerCase()} card that costs ${card.cost} elixir.`,
        usageRate: Math.random() * 20 + 5, // Random usage rate between 5-25%
        winRate: Math.random() * 10 + 45,  // Random win rate between 45-55%
      }
    })
  }

  // Seed achievements
  console.log('🏆 Seeding achievements...')
  for (const achievement of achievements) {
    await prisma.achievement.create({
      data: achievement
    })
  }

  // Create a test user for development
  console.log('👤 Creating test user...')
  const testUser = await prisma.user.create({
    data: {
      email: 'test@opti-royale.com',
      username: 'testuser',
      firstName: 'Test',
      lastName: 'User',
      playerTag: '#TESTUSER123',
      trophies: 4500,
      maxTrophies: 5200,
      skillLevel: 'INTERMEDIATE'
    }
  })

  // Create subscription for test user
  await prisma.subscription.create({
    data: {
      userId: testUser.id,
      plan: 'FREE',
      status: 'ACTIVE',
      analysesPerMonth: 10,
      maxVideoLength: 300,
    }
  })

  // Create progress tracking for test user
  await prisma.progressTracking.create({
    data: {
      userId: testUser.id,
      overallLevel: 1,
      xpPoints: 0,
      xpToNextLevel: 100,
      totalAnalyses: 0,
      averageScore: 0,
      improvementTrend: 0,
      skillLevelCurrent: 'INTERMEDIATE',
      skillLevelProgress: 0.3,
      masteredConceptsText: 'basic-placement,elixir-management',
    }
  })

  console.log('✅ Database seeded successfully!')
  console.log(`📊 Created ${cards.length} cards`)
  console.log(`🏆 Created ${achievements.length} achievements`)
  console.log(`👤 Created test user: ${testUser.email}`)
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
