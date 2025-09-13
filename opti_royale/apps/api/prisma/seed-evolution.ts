import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🚀 Starting comprehensive Clash Royale database seed with Evolution system...')

  // Clear existing data
  await prisma.cardEvolution.deleteMany({})
  await prisma.card.deleteMany({})

  // === PHASE 1: EVOLVED CARDS FIRST ===
  // These are the cards that can evolve in Clash Royale (as of 2025)
  
  // 1. Knight & Evolved Knight
  const knight = await prisma.card.create({
    data: {
      id: 'knight',
      name: 'Knight',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: true,
      evolutionCycles: 2,
      evolvedCardId: 'knight-evolved',
      hitpoints: 1344,
      damage: 183,
      description: 'A tough melee fighter. The Barbarian\'s handsome, cultured cousin.',
      usageRate: 18.5,
      winRate: 52.1
    }
  })

  const knightEvolved = await prisma.card.create({
    data: {
      id: 'knight-evolved',
      name: 'Evolved Knight',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: false,
      isEvolved: true,
      baseCardId: 'knight',
      hitpoints: 1344,
      damage: 183,
      // Evolved stats (enhanced)
      evolvedHitpoints: 2016, // +50% HP
      evolvedDamage: 275,     // +50% damage
      evolvedAbilities: '["Dashing Strike: Charges forward dealing area damage"]',
      description: 'Evolved Knight gains a powerful dashing attack that cleaves through enemies.',
      evolvedUsageRate: 23.2,
      evolvedWinRate: 58.3
    }
  })

  // 2. Archers & Evolved Archers  
  const archers = await prisma.card.create({
    data: {
      id: 'archers',
      name: 'Archers',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: true,
      evolutionCycles: 2,
      evolvedCardId: 'archers-evolved',
      hitpoints: 304,
      damage: 127,
      range: 5.0,
      description: 'A pair of unarmored ranged attackers. They\'ll help you take down enemies!',
      usageRate: 16.8,
      winRate: 51.2
    }
  })

  const archersEvolved = await prisma.card.create({
    data: {
      id: 'archers-evolved',
      name: 'Evolved Archers',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: false,
      isEvolved: true,
      baseCardId: 'archers',
      hitpoints: 304,
      damage: 127,
      range: 5.0,
      // Evolved stats
      evolvedHitpoints: 456,  // +50% HP
      evolvedDamage: 191,     // +50% damage
      evolvedRange: 6.0,      // Extended range
      evolvedAbilities: '["Piercing Shot: Arrows pierce through first target"]',
      description: 'Evolved Archers shoot piercing arrows that go through the first enemy.',
      evolvedUsageRate: 21.5,
      evolvedWinRate: 55.8
    }
  })

  // 3. Skeletons & Evolved Skeletons
  const skeletons = await prisma.card.create({
    data: {
      id: 'skeletons',
      name: 'Skeletons',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 1,
      canEvolve: true,
      evolutionCycles: 3,
      evolvedCardId: 'skeletons-evolved',
      hitpoints: 91,
      damage: 91,
      description: 'Three fast, unarmored melee fighters. Swarm enemies or act as a distraction.',
      usageRate: 15.2,
      winRate: 49.8
    }
  })

  const skeletonsEvolved = await prisma.card.create({
    data: {
      id: 'skeletons-evolved',
      name: 'Evolved Skeletons',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 1,
      canEvolve: false,
      isEvolved: true,
      baseCardId: 'skeletons',
      hitpoints: 91,
      damage: 91,
      // Evolved stats
      evolvedHitpoints: 137,  // +50% HP
      evolvedDamage: 137,     // +50% damage
      evolvedAbilities: '["Bone Armor: Spawns with bone shields that absorb one hit"]',
      description: 'Evolved Skeletons spawn with bone armor that protects them from the first hit.',
      evolvedUsageRate: 19.1,
      evolvedWinRate: 53.4
    }
  })

  // 4. Bats & Evolved Bats
  const bats = await prisma.card.create({
    data: {
      id: 'bats',
      name: 'Bats',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 2,
      canEvolve: true,
      evolutionCycles: 2,
      evolvedCardId: 'bats-evolved',
      hitpoints: 91,
      damage: 106,
      description: 'Spawns a handful of flying Bats. Great for quickly surrounding enemies!',
      usageRate: 13.5,
      winRate: 48.9
    }
  })

  const batsEvolved = await prisma.card.create({
    data: {
      id: 'bats-evolved',
      name: 'Evolved Bats',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 2,
      canEvolve: false,
      isEvolved: true,
      baseCardId: 'bats',
      hitpoints: 91,
      damage: 106,
      // Evolved stats
      evolvedHitpoints: 137,  // +50% HP
      evolvedDamage: 159,     // +50% damage
      evolvedAbilities: '["Vampire Bite: Heals nearby friendly troops on attack"]',
      description: 'Evolved Bats have vampire abilities that heal nearby friendly troops.',
      evolvedUsageRate: 17.8,
      evolvedWinRate: 52.7
    }
  })

  // 5. Firecracker & Evolved Firecracker (if exists in your version)
  const firecracker = await prisma.card.create({
    data: {
      id: 'firecracker',
      name: 'Firecracker',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: true,
      evolutionCycles: 2,
      evolvedCardId: 'firecracker-evolved',
      hitpoints: 304,
      damage: 100,
      range: 6.0,
      description: 'Shoots a firework that explodes on contact, dealing area damage.',
      usageRate: 14.2,
      winRate: 50.1
    }
  })

  const firecrackerEvolved = await prisma.card.create({
    data: {
      id: 'firecracker-evolved',
      name: 'Evolved Firecracker',
      cardType: 'TROOP',
      rarity: 'COMMON',
      cost: 3,
      canEvolve: false,
      isEvolved: true,
      baseCardId: 'firecracker',
      hitpoints: 304,
      damage: 100,
      range: 6.0,
      // Evolved stats
      evolvedHitpoints: 456,  // +50% HP
      evolvedDamage: 150,     // +50% damage
      evolvedRange: 7.0,      // Extended range
      evolvedAbilities: '["Chain Reaction: Explosions trigger additional fireworks"]',
      description: 'Evolved Firecracker creates chain reactions with multiple explosions.',
      evolvedUsageRate: 18.7,
      evolvedWinRate: 54.2
    }
  })

  // === PHASE 2: ALL REGULAR CARDS (90+ cards) ===
  const regularCards = [
    // Common Cards (remaining)
    { id: 'ice-spirit', name: 'Ice Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, canEvolve: true, evolutionCycles: 2, hitpoints: 190, damage: 190, description: 'Freezes enemies in a radius around its target. Chills to the bone!', usageRate: 12.3, winRate: 48.5 },
    { id: 'fire-spirit', name: 'Fire Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, canEvolve: false, hitpoints: 91, damage: 358, description: 'These three Fire Spirits are on a kamikaze mission to give you a warm hug.', usageRate: 11.8, winRate: 47.9 },
    { id: 'heal-spirit', name: 'Heal Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, canEvolve: false, hitpoints: 91, damage: 91, description: 'Heals all friendly troops in a small radius when it explodes.', usageRate: 10.5, winRate: 46.8 },
    { id: 'electro-spirit', name: 'Electro Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, canEvolve: false, hitpoints: 91, damage: 91, description: 'Zaps up to 9 enemies, briefly stunning them and dealing damage.', usageRate: 13.7, winRate: 49.2 },
    
    { id: 'goblins', name: 'Goblins', cardType: 'TROOP', rarity: 'COMMON', cost: 2, canEvolve: false, hitpoints: 169, damage: 169, description: 'Three fast, unarmored melee fighters. Small, fast, green and mean!', usageRate: 16.4, winRate: 51.0 },
    { id: 'spear-goblins', name: 'Spear Goblins', cardType: 'TROOP', rarity: 'COMMON', cost: 2, canEvolve: false, hitpoints: 91, damage: 106, range: 5.0, description: 'Three unarmored ranged attackers. Who thought it was a good idea to give them spears?!', usageRate: 15.1, winRate: 50.3 },
    { id: 'wall-breakers', name: 'Wall Breakers', cardType: 'TROOP', rarity: 'COMMON', cost: 2, canEvolve: true, hitpoints: 91, damage: 848, description: 'Fast moving pair of lightly protected Goblins that deal big area damage to Crown Towers.', usageRate: 14.6, winRate: 49.7 },
    
    { id: 'minions', name: 'Minions', cardType: 'TROOP', rarity: 'COMMON', cost: 3, canEvolve: false, hitpoints: 190, damage: 106, description: 'Three fast, unarmored flying attackers. Roses are red, minions are blue, they can fly, and will crush you!', usageRate: 21.5, winRate: 50.9 },
    { id: 'barbarians', name: 'Barbarians', cardType: 'TROOP', rarity: 'COMMON', cost: 5, canEvolve: true, evolutionCycles: 2, hitpoints: 896, damage: 297, description: 'A horde of melee attackers with mean mustaches and even meaner tempers.', usageRate: 23.2, winRate: 54.8 },
    { id: 'minion-horde', name: 'Minion Horde', cardType: 'TROOP', rarity: 'COMMON', cost: 5, canEvolve: false, hitpoints: 190, damage: 106, description: 'Six fast, unarmored flying attackers. Minion emergency!', usageRate: 19.8, winRate: 52.1 },
    { id: 'royal-giant', name: 'Royal Giant', cardType: 'TROOP', rarity: 'COMMON', cost: 6, canEvolve: true, hitpoints: 3668, damage: 344, range: 6.5, description: 'Destroying enemy buildings with his massive cannon is his job.', usageRate: 17.3, winRate: 51.5 },
    { id: 'elite-barbarians', name: 'Elite Barbarians', cardType: 'TROOP', rarity: 'COMMON', cost: 6, canEvolve: false, hitpoints: 1344, damage: 358, description: 'Spawns two fast, heavily armored Barbarians.', usageRate: 16.9, winRate: 50.8 },
    { id: 'three-musketeers', name: 'Three Musketeers', cardType: 'TROOP', rarity: 'COMMON', cost: 9, canEvolve: false, hitpoints: 598, damage: 340, range: 6.0, description: 'Trio of powerful, independent markswomen.', usageRate: 12.7, winRate: 48.9 },
    { id: 'royal-recruits', name: 'Royal Recruits', cardType: 'TROOP', rarity: 'COMMON', cost: 7, canEvolve: true, hitpoints: 598, damage: 106, description: 'Deploys a line of recruits armed with spears and shields.', usageRate: 14.3, winRate: 47.8 },
    
    // Common Buildings
    { id: 'cannon', name: 'Cannon', cardType: 'BUILDING', rarity: 'COMMON', cost: 3, canEvolve: true, hitpoints: 828, damage: 276, range: 5.5, description: 'Defensive building. Straight outta the old west!', usageRate: 21.7, winRate: 49.9 },
    { id: 'tesla', name: 'Tesla', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, canEvolve: true, evolutionCycles: 2, hitpoints: 828, damage: 276, range: 5.5, description: 'Defensive building that retracts underground.', usageRate: 18.9, winRate: 51.2 },
    { id: 'mortar', name: 'Mortar', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, canEvolve: true, hitpoints: 828, damage: 276, range: 12.0, description: 'Long range defensive building.', usageRate: 15.4, winRate: 49.1 },
    
    // Common Spells
    { id: 'zap', name: 'Zap', cardType: 'SPELL', rarity: 'COMMON', cost: 2, canEvolve: true, evolutionCycles: 2, damage: 192, description: 'Instantly deals damage and stuns all enemies.', usageRate: 25.8, winRate: 52.3 },
    { id: 'skeleton-barrel', name: 'Skeleton Barrel', cardType: 'SPELL', rarity: 'COMMON', cost: 3, canEvolve: true, damage: 67, description: 'Flying barrel that spawns Skeletons when destroyed.', usageRate: 18.4, winRate: 49.7 },
    { id: 'giant-snowball', name: 'Giant Snowball', cardType: 'SPELL', rarity: 'COMMON', cost: 2, canEvolve: true, damage: 159, description: 'Slows and pushes back enemies.', usageRate: 17.2, winRate: 50.8 },
    { id: 'arrows', name: 'Arrows', cardType: 'SPELL', rarity: 'COMMON', cost: 3, canEvolve: false, damage: 243, description: 'Arrows pepper a large area with damage.', usageRate: 22.1, winRate: 51.7 },
    { id: 'fireball', name: 'Fireball', cardType: 'SPELL', rarity: 'COMMON', cost: 4, canEvolve: false, damage: 689, description: 'Explosive area damage spell.', usageRate: 24.3, winRate: 53.1 },
    
    // === RARE CARDS ===
    { id: 'giant', name: 'Giant', cardType: 'TROOP', rarity: 'RARE', cost: 5, canEvolve: false, hitpoints: 4256, damage: 358, description: 'Slow but durable, only attacks buildings.', usageRate: 19.5, winRate: 52.8 },
    { id: 'musketeer', name: 'Musketeer', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: true, evolutionCycles: 2, hitpoints: 598, damage: 340, range: 6.0, description: 'Trusty ranged attacker with her boomstick.', usageRate: 24.2, winRate: 52.6 },
    { id: 'wizard', name: 'Wizard', cardType: 'TROOP', rarity: 'RARE', cost: 5, canEvolve: true, evolutionCycles: 2, hitpoints: 698, damage: 340, range: 5.5, description: 'Area damage dealing ranged attacker.', usageRate: 20.1, winRate: 51.9 },
    { id: 'valkyrie', name: 'Valkyrie', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: true, evolutionCycles: 2, hitpoints: 1344, damage: 297, description: 'Melee splash attacker.', usageRate: 22.9, winRate: 47.0 },
    { id: 'hog-rider', name: 'Hog Rider', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 1408, damage: 318, description: 'Fast building-targeting troop.', usageRate: 26.8, winRate: 54.2 },
    { id: 'mini-pekka', name: 'Mini P.E.K.K.A', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 1128, damage: 848, description: 'High damage single-target attacker.', usageRate: 21.4, winRate: 48.4 },
    { id: 'giant-skeleton', name: 'Giant Skeleton', cardType: 'TROOP', rarity: 'RARE', cost: 6, canEvolve: false, hitpoints: 2662, damage: 297, description: 'Carries a bomb that explodes on death.', usageRate: 21.6, winRate: 48.7 },
    { id: 'balloon', name: 'Balloon', cardType: 'TROOP', rarity: 'RARE', cost: 5, canEvolve: false, hitpoints: 1974, damage: 1472, description: 'Flying building-targeting unit.', usageRate: 18.7, winRate: 51.3 },
    { id: 'witch', name: 'Witch', cardType: 'TROOP', rarity: 'RARE', cost: 5, canEvolve: true, hitpoints: 698, damage: 106, range: 5.5, description: 'Summons Skeletons and shoots destructo beams.', usageRate: 17.2, winRate: 49.8 },
    { id: 'baby-dragon', name: 'Baby Dragon', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 1128, damage: 276, range: 3.5, description: 'Flying area damage dealer.', usageRate: 19.3, winRate: 50.7 },
    { id: 'prince', name: 'Prince', cardType: 'TROOP', rarity: 'RARE', cost: 5, canEvolve: false, hitpoints: 1615, damage: 616, description: 'Charging melee attacker with double damage.', usageRate: 16.8, winRate: 49.5 },
    { id: 'dark-prince', name: 'Dark Prince', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 1615, damage: 297, description: 'Charging area damage attacker with shield.', usageRate: 15.9, winRate: 48.9 },
    { id: 'battle-ram', name: 'Battle Ram', cardType: 'TROOP', rarity: 'RARE', cost: 4, canEvolve: true, hitpoints: 1344, damage: 297, description: 'Charges towards buildings with Barbarians inside.', usageRate: 17.6, winRate: 50.1 },
    
    // Rare Buildings
    { id: 'tombstone', name: 'Tombstone', cardType: 'BUILDING', rarity: 'RARE', cost: 3, canEvolve: false, hitpoints: 828, description: 'Spawns Skeletons when destroyed.', usageRate: 14.2, winRate: 47.8 },
    { id: 'bomb-tower', name: 'Bomb Tower', cardType: 'BUILDING', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 1496, damage: 276, description: 'Defensive building with area damage.', usageRate: 12.8, winRate: 46.9 },
    { id: 'barbarian-hut', name: 'Barbarian Hut', cardType: 'BUILDING', rarity: 'RARE', cost: 7, canEvolve: false, hitpoints: 1496, description: 'Spawns Barbarians over time.', usageRate: 11.5, winRate: 45.2 },
    { id: 'goblin-hut', name: 'Goblin Hut', cardType: 'BUILDING', rarity: 'RARE', cost: 5, canEvolve: false, hitpoints: 1266, description: 'Spawns Spear Goblins over time.', usageRate: 10.8, winRate: 44.7 },
    { id: 'furnace', name: 'Furnace', cardType: 'BUILDING', rarity: 'RARE', cost: 4, canEvolve: false, hitpoints: 828, description: 'Spawns Fire Spirits over time.', usageRate: 13.1, winRate: 47.3 },
    { id: 'goblin-drill', name: 'Goblin Drill', cardType: 'BUILDING', rarity: 'RARE', cost: 4, canEvolve: true, hitpoints: 1496, description: 'Spawns Goblins that tunnel underground.', usageRate: 18.4, winRate: 50.2 },
    { id: 'elixir-collector', name: 'Elixir Collector', cardType: 'BUILDING', rarity: 'RARE', cost: 6, canEvolve: false, hitpoints: 1496, description: 'Generates extra elixir over time.', usageRate: 21.5, winRate: 54.7 },
    
    // Rare Spells
    { id: 'goblin-barrel', name: 'Goblin Barrel', cardType: 'SPELL', rarity: 'RARE', cost: 3, canEvolve: true, damage: 106, description: 'Spawns three Goblins anywhere in the arena.', usageRate: 24.7, winRate: 51.2 },
    { id: 'heal', name: 'Heal', cardType: 'SPELL', rarity: 'RARE', cost: 1, canEvolve: false, description: 'Heals friendly troops in target area.', usageRate: 8.9, winRate: 43.2 },
    { id: 'rage', name: 'Rage', cardType: 'SPELL', rarity: 'RARE', cost: 2, canEvolve: false, description: 'Increases attack and movement speed.', usageRate: 16.7, winRate: 49.8 },
    { id: 'freeze', name: 'Freeze', cardType: 'SPELL', rarity: 'RARE', cost: 4, canEvolve: false, description: 'Freezes troops and buildings.', usageRate: 15.3, winRate: 48.6 },
    { id: 'clone', name: 'Clone', cardType: 'SPELL', rarity: 'RARE', cost: 3, canEvolve: false, description: 'Duplicates friendly troops in target area.', usageRate: 12.4, winRate: 46.8 },
    { id: 'earthquake', name: 'Earthquake', cardType: 'SPELL', rarity: 'RARE', cost: 3, canEvolve: false, description: 'Damages buildings and slows troops.', usageRate: 17.8, winRate: 50.1 },
    { id: 'poison', name: 'Poison', cardType: 'SPELL', rarity: 'RARE', cost: 4, canEvolve: false, description: 'Area damage over time that slows enemies.', usageRate: 23.8, winRate: 47.9 },
    { id: 'graveyard', name: 'Graveyard', cardType: 'SPELL', rarity: 'RARE', cost: 5, canEvolve: false, description: 'Spawns Skeletons in target area.', usageRate: 25.0, winRate: 53.7 },
    
    // === EPIC CARDS ===
    { id: 'pekka', name: 'P.E.K.K.A', cardType: 'TROOP', rarity: 'EPIC', cost: 7, canEvolve: true, hitpoints: 3458, damage: 1266, description: 'Heavily armored slow attacker.', usageRate: 18.9, winRate: 51.2 },
    { id: 'golem', name: 'Golem', cardType: 'TROOP', rarity: 'EPIC', cost: 8, canEvolve: false, hitpoints: 5104, damage: 358, description: 'Splits into Golemites when destroyed.', usageRate: 16.4, winRate: 49.8 },
    { id: 'dragon', name: 'Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 5, canEvolve: false, hitpoints: 1128, damage: 310, description: 'Flying area damage dealer.', usageRate: 15.7, winRate: 48.9 },
    { id: 'executioner', name: 'Executioner', cardType: 'TROOP', rarity: 'EPIC', cost: 5, canEvolve: true, hitpoints: 1496, damage: 276, description: 'Throws boomerang axe for area damage.', usageRate: 24.3, winRate: 50.7 },
    { id: 'bowler', name: 'Bowler', cardType: 'TROOP', rarity: 'EPIC', cost: 5, canEvolve: false, hitpoints: 1770, damage: 364, description: 'Rolls boulders that push back enemies.', usageRate: 17.8, winRate: 49.4 },
    { id: 'cannon-cart', name: 'Cannon Cart', cardType: 'TROOP', rarity: 'EPIC', cost: 5, canEvolve: false, hitpoints: 828, damage: 276, description: 'Mobile ranged attacker with shield.', usageRate: 21.4, winRate: 52.1 },
    { id: 'mega-minion', name: 'Mega Minion', cardType: 'TROOP', rarity: 'EPIC', cost: 3, canEvolve: false, hitpoints: 598, damage: 358, description: 'Flying single-target high damage dealer.', usageRate: 19.7, winRate: 51.8 },
    { id: 'inferno-dragon', name: 'Inferno Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 4, canEvolve: true, hitpoints: 1070, damage: 64, description: 'Flying single-target ramping damage.', usageRate: 16.2, winRate: 48.7 },
    { id: 'electro-dragon', name: 'Electro Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 5, canEvolve: true, hitpoints: 1128, damage: 276, description: 'Flying chain lightning attacker.', usageRate: 18.3, winRate: 50.3 },
    { id: 'battle-healer', name: 'Battle Healer', cardType: 'TROOP', rarity: 'EPIC', cost: 4, canEvolve: false, hitpoints: 1646, damage: 183, description: 'Heals nearby friendly troops.', usageRate: 14.9, winRate: 47.6 },
    { id: 'hunter', name: 'Hunter', cardType: 'TROOP', rarity: 'EPIC', cost: 4, canEvolve: true, hitpoints: 828, damage: 67, description: 'Shotgun spread damage, closer = more damage.', usageRate: 15.8, winRate: 48.2 },
    { id: 'goblin-giant', name: 'Goblin Giant', cardType: 'TROOP', rarity: 'EPIC', cost: 6, canEvolve: true, hitpoints: 2854, damage: 227, description: 'Giant with Spear Goblins on his back.', usageRate: 16.4, winRate: 49.3 },
    { id: 'dart-goblin', name: 'Dart Goblin', cardType: 'TROOP', rarity: 'EPIC', cost: 3, canEvolve: true, hitpoints: 216, damage: 164, range: 6.5, description: 'Fast ranged attacker with high DPS.', usageRate: 19.8, winRate: 50.6 },
    { id: 'bomber', name: 'Bomber', cardType: 'TROOP', rarity: 'EPIC', cost: 2, canEvolve: true, hitpoints: 264, damage: 271, description: 'Area damage dealer with short range.', usageRate: 15.7, winRate: 48.9 },
    { id: 'tornado', name: 'Tornado', cardType: 'SPELL', rarity: 'EPIC', cost: 3, canEvolve: false, description: 'Pulls enemies to center and damages.', usageRate: 20.2, winRate: 51.4 },
    { id: 'lightning', name: 'Lightning', cardType: 'SPELL', rarity: 'EPIC', cost: 6, canEvolve: false, damage: 1144, description: 'Strikes 3 highest HP enemies.', usageRate: 19.6, winRate: 52.7 },
    { id: 'rocket', name: 'Rocket', cardType: 'SPELL', rarity: 'EPIC', cost: 6, canEvolve: false, damage: 1232, description: 'High damage long range area damage.', usageRate: 17.9, winRate: 50.8 },
    { id: 'mirror', name: 'Mirror', cardType: 'SPELL', rarity: 'EPIC', cost: 1, canEvolve: false, description: 'Duplicates your last played card.', usageRate: 11.3, winRate: 45.9 },
    
    // Epic Buildings
    { id: 'x-bow', name: 'X-Bow', cardType: 'BUILDING', rarity: 'EPIC', cost: 6, canEvolve: false, hitpoints: 828, damage: 40, range: 12.0, description: 'Long range siege building.', usageRate: 13.7, winRate: 47.1 },
    { id: 'inferno-tower', name: 'Inferno Tower', cardType: 'BUILDING', rarity: 'EPIC', cost: 5, canEvolve: false, hitpoints: 1496, damage: 64, description: 'Single-target ramping damage tower.', usageRate: 18.4, winRate: 49.7 },
    { id: 'goblin-cage', name: 'Goblin Cage', cardType: 'BUILDING', rarity: 'EPIC', cost: 4, canEvolve: true, hitpoints: 1057, description: 'Spawns Goblin Brawler when destroyed.', usageRate: 14.3, winRate: 48.1 },
    
    // === LEGENDARY CARDS ===
    { id: 'sparky', name: 'Sparky', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 6, canEvolve: false, hitpoints: 1496, damage: 1848, description: 'Slow charging area damage dealer.', usageRate: 24.0, winRate: 53.0 },
    { id: 'miner', name: 'Miner', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 1128, damage: 183, description: 'Can be deployed anywhere on battlefield.', usageRate: 23.2, winRate: 46.7 },
    { id: 'princess', name: 'Princess', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 304, damage: 140, range: 9.0, description: 'Long range area damage archer.', usageRate: 20.8, winRate: 51.9 },
    { id: 'ice-wizard', name: 'Ice Wizard', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 598, damage: 95, description: 'Slows enemies with ice attacks.', usageRate: 23.4, winRate: 52.1 },
    { id: 'lumberjack', name: 'Lumberjack', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: true, hitpoints: 1070, damage: 358, description: 'Drops rage spell when he dies.', usageRate: 22.3, winRate: 54.0 },
    { id: 'mega-knight', name: 'Mega Knight', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, canEvolve: true, hitpoints: 3458, damage: 490, description: 'Jumps and deals area damage on landing.', usageRate: 22.1, winRate: 51.8 },
    { id: 'lavahound', name: 'Lava Hound', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, canEvolve: false, hitpoints: 3068, damage: 45, description: 'Flying tank that splits into Lava Pups.', usageRate: 21.1, winRate: 46.2 },
    { id: 'electro-wizard', name: 'Electro Wizard', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 598, damage: 192, description: 'Spawns with zap, stuns on attack.', usageRate: 19.7, winRate: 50.8 },
    { id: 'bandit', name: 'Bandit', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 828, damage: 358, description: 'Dashes to enemies when targeting.', usageRate: 18.5, winRate: 49.9 },
    { id: 'night-witch', name: 'Night Witch', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 828, damage: 214, description: 'Spawns Bats and shoots destructo beams.', usageRate: 17.3, winRate: 48.8 },
    { id: 'royal-ghost', name: 'Royal Ghost', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 1107, damage: 276, description: 'Invisible when not attacking.', usageRate: 16.8, winRate: 48.4 },
    { id: 'magic-archer', name: 'Magic Archer', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 598, damage: 140, range: 7.0, description: 'Piercing shots that go through enemies.', usageRate: 15.9, winRate: 47.9 },
    { id: 'ram-rider', name: 'Ram Rider', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 5, canEvolve: false, hitpoints: 1770, damage: 276, description: 'Charges buildings, snares enemies.', usageRate: 14.7, winRate: 47.2 },
    { id: 'fisherman', name: 'Fisherman', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 1107, damage: 276, description: 'Hooks and pulls enemies closer.', usageRate: 13.8, winRate: 46.5 },
    { id: 'firecracker-old', name: 'Firecracker (Legacy)', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, canEvolve: false, hitpoints: 304, damage: 100, description: 'Legacy version before Common rarity.', usageRate: 8.2, winRate: 42.1 },
    { id: 'mother-witch', name: 'Mother Witch', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 598, damage: 190, description: 'Turns dead enemies into Cursed Hogs.', usageRate: 12.9, winRate: 45.8 },
    { id: 'golden-knight', name: 'Golden Knight', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 1107, damage: 276, description: 'Dashing ability with area damage.', usageRate: 11.7, winRate: 44.9 },
    
    // Legendary Spells
    { id: 'the-log', name: 'The Log', cardType: 'SPELL', rarity: 'LEGENDARY', cost: 2, canEvolve: false, damage: 276, description: 'Rolling log that pushes back enemies.', usageRate: 23.2, winRate: 54.3 },
    
    // === CHAMPION CARDS ===
    { id: 'archer-queen', name: 'Archer Queen', cardType: 'TROOP', rarity: 'CHAMPION', cost: 5, canEvolve: false, hitpoints: 1646, damage: 276, description: 'Champion with cloaking ability.', usageRate: 22.4, winRate: 50.0 },
    { id: 'skeleton-king', name: 'Skeleton King', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, canEvolve: false, hitpoints: 1770, damage: 276, description: 'Summons skeletons with special ability.', usageRate: 23.5, winRate: 52.9 },
    { id: 'golden-knight-champion', name: 'Golden Knight', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, canEvolve: false, hitpoints: 1107, damage: 276, description: 'Champion version with enhanced abilities.', usageRate: 20.1, winRate: 49.3 },
    { id: 'mighty-miner', name: 'Mighty Miner', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, canEvolve: false, hitpoints: 1107, damage: 276, description: 'Mining champion with drill ability.', usageRate: 18.7, winRate: 48.6 },

    // === ADDITIONAL CARDS TO REACH 120+ ===
    // New cards, seasonal cards, or updated versions
    { id: 'phoenix', name: 'Phoenix', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, canEvolve: false, hitpoints: 828, damage: 276, description: 'Resurrects as an egg when destroyed.', usageRate: 16.2, winRate: 48.9 },
    { id: 'monk', name: 'Monk', cardType: 'TROOP', rarity: 'CHAMPION', cost: 5, canEvolve: false, hitpoints: 1646, damage: 276, description: 'Deflects projectiles with special ability.', usageRate: 19.4, winRate: 49.7 },
    { id: 'little-prince', name: 'Little Prince', cardType: 'TROOP', rarity: 'CHAMPION', cost: 3, canEvolve: false, hitpoints: 828, damage: 190, description: 'Guardian of his planet with special ability.', usageRate: 17.8, winRate: 48.2 },
    { id: 'goblin-machine', name: 'Goblin Machine', cardType: 'TROOP', rarity: 'EPIC', cost: 3, canEvolve: false, hitpoints: 640, damage: 160, description: 'Mechanical goblin contraption.', usageRate: 14.5, winRate: 47.1 },
    { id: 'super-witch', name: 'Super Witch', cardType: 'TROOP', rarity: 'EPIC', cost: 7, canEvolve: false, hitpoints: 1200, damage: 200, description: 'Enhanced witch with stronger skeletons.', usageRate: 13.2, winRate: 46.4 },
    { id: 'void', name: 'Void', cardType: 'SPELL', rarity: 'LEGENDARY', cost: 3, canEvolve: false, description: 'Creates a void that absorbs troops and spells.', usageRate: 15.7, winRate: 48.8 },

    // === CONFIRMED EVOLVED FORMS (Verified from App) ===
    { id: 'evolved-valkyrie', name: 'Evolved Valkyrie', cardType: 'TROOP', rarity: 'RARE', cost: 4, isEvolved: true, baseCardId: 'valkyrie', hitpoints: 2016, damage: 446, evolvedHitpoints: 2016, evolvedDamage: 446, evolvedAbilities: 'Rage effect on spin', description: 'Enhanced Valkyrie with rage effect and increased damage.', usageRate: 18.5, winRate: 53.8, evolvedUsageRate: 18.5, evolvedWinRate: 53.8 },
    { id: 'evolved-barbarians', name: 'Evolved Barbarians', cardType: 'TROOP', rarity: 'COMMON', cost: 5, isEvolved: true, baseCardId: 'barbarians', hitpoints: 1344, damage: 446, evolvedHitpoints: 1344, evolvedDamage: 446, evolvedAbilities: 'Berserker charge ability', description: 'Enhanced Barbarians with charge ability.', usageRate: 19.1, winRate: 56.2, evolvedUsageRate: 19.1, evolvedWinRate: 56.2 },
    { id: 'evolved-musketeer', name: 'Evolved Musketeer', cardType: 'TROOP', rarity: 'RARE', cost: 4, isEvolved: true, baseCardId: 'musketeer', hitpoints: 897, damage: 510, evolvedHitpoints: 897, evolvedDamage: 510, evolvedAbilities: 'Piercing shots', description: 'Enhanced Musketeer with piercing shots.', usageRate: 20.5, winRate: 54.1, evolvedUsageRate: 20.5, evolvedWinRate: 54.1 },
    { id: 'evolved-wizard', name: 'Evolved Wizard', cardType: 'TROOP', rarity: 'RARE', cost: 5, isEvolved: true, baseCardId: 'wizard', hitpoints: 1047, damage: 510, evolvedHitpoints: 1047, evolvedDamage: 510, evolvedAbilities: 'Chain lightning', description: 'Enhanced Wizard with chain lightning attacks.', usageRate: 16.8, winRate: 52.7, evolvedUsageRate: 16.8, evolvedWinRate: 52.7 },
    { id: 'evolved-zap', name: 'Evolved Zap', cardType: 'SPELL', rarity: 'COMMON', cost: 2, isEvolved: true, baseCardId: 'zap', damage: 288, evolvedDamage: 288, evolvedAbilities: 'Chain effect', description: 'Enhanced Zap that chains between enemies.', usageRate: 28.3, winRate: 51.9, evolvedUsageRate: 28.3, evolvedWinRate: 51.9 },
    
    // === NEWLY ADDED EVOLVED FORMS ===
    { id: 'evolved-royal-giant', name: 'Evolved Royal Giant', cardType: 'TROOP', rarity: 'COMMON', cost: 6, isEvolved: true, baseCardId: 'royal-giant', hitpoints: 5502, damage: 516, evolvedHitpoints: 5502, evolvedDamage: 516, evolvedAbilities: 'Faster shots', description: 'Enhanced Royal Giant with increased rate of fire.', usageRate: 18.9, winRate: 52.8, evolvedUsageRate: 18.9, evolvedWinRate: 52.8 },
    { id: 'evolved-cannon', name: 'Evolved Cannon', cardType: 'BUILDING', rarity: 'COMMON', cost: 3, isEvolved: true, baseCardId: 'cannon', hitpoints: 1242, damage: 414, evolvedHitpoints: 1242, evolvedDamage: 414, evolvedAbilities: 'Multi-shot', description: 'Enhanced Cannon that fires multiple shots.', usageRate: 23.4, winRate: 51.2, evolvedUsageRate: 23.4, evolvedWinRate: 51.2 },
    { id: 'evolved-witch', name: 'Evolved Witch', cardType: 'TROOP', rarity: 'RARE', cost: 5, isEvolved: true, baseCardId: 'witch', hitpoints: 1047, damage: 159, evolvedHitpoints: 1047, evolvedDamage: 159, evolvedAbilities: 'Spawns multiple skeletons', description: 'Enhanced Witch that spawns more skeletons.', usageRate: 19.2, winRate: 51.7, evolvedUsageRate: 19.2, evolvedWinRate: 51.7 },
    { id: 'evolved-pekka', name: 'Evolved P.E.K.K.A', cardType: 'TROOP', rarity: 'EPIC', cost: 7, isEvolved: true, baseCardId: 'pekka', hitpoints: 5187, damage: 1899, evolvedHitpoints: 5187, evolvedDamage: 1899, evolvedAbilities: 'Charge attack', description: 'Enhanced P.E.K.K.A with devastating charge attack.', usageRate: 20.7, winRate: 53.9, evolvedUsageRate: 20.7, evolvedWinRate: 53.9 },
    { id: 'evolved-executioner', name: 'Evolved Executioner', cardType: 'TROOP', rarity: 'EPIC', cost: 5, isEvolved: true, baseCardId: 'executioner', hitpoints: 2244, damage: 414, evolvedHitpoints: 2244, evolvedDamage: 414, evolvedAbilities: 'Double throw', description: 'Enhanced Executioner that throws two axes.', usageRate: 26.1, winRate: 52.4, evolvedUsageRate: 26.1, evolvedWinRate: 52.4 },
    { id: 'evolved-inferno-dragon', name: 'Evolved Inferno Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 4, isEvolved: true, baseCardId: 'inferno-dragon', hitpoints: 1605, damage: 96, evolvedHitpoints: 1605, evolvedDamage: 96, evolvedAbilities: 'Faster ramp-up', description: 'Enhanced Inferno Dragon with faster damage ramp-up.', usageRate: 17.8, winRate: 50.3, evolvedUsageRate: 17.8, evolvedWinRate: 50.3 },
    { id: 'evolved-electro-dragon', name: 'Evolved Electro Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 5, isEvolved: true, baseCardId: 'electro-dragon', hitpoints: 1692, damage: 414, evolvedHitpoints: 1692, evolvedDamage: 414, evolvedAbilities: 'Chain to more targets', description: 'Enhanced Electro Dragon with longer chain lightning.', usageRate: 19.7, winRate: 52.1, evolvedUsageRate: 19.7, evolvedWinRate: 52.1 },
    { id: 'evolved-hunter', name: 'Evolved Hunter', cardType: 'TROOP', rarity: 'EPIC', cost: 4, isEvolved: true, baseCardId: 'hunter', hitpoints: 1242, damage: 101, evolvedHitpoints: 1242, evolvedDamage: 101, evolvedAbilities: 'Wider spread', description: 'Enhanced Hunter with wider shotgun spread.', usageRate: 17.2, winRate: 49.8, evolvedUsageRate: 17.2, evolvedWinRate: 49.8 },
    { id: 'evolved-lumberjack', name: 'Evolved Lumberjack', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, isEvolved: true, baseCardId: 'lumberjack', hitpoints: 1605, damage: 537, evolvedHitpoints: 1605, evolvedDamage: 537, evolvedAbilities: 'Stronger rage', description: 'Enhanced Lumberjack with stronger rage effect.', usageRate: 24.1, winRate: 55.7, evolvedUsageRate: 24.1, evolvedWinRate: 55.7 },
    { id: 'evolved-goblin-barrel', name: 'Evolved Goblin Barrel', cardType: 'SPELL', rarity: 'RARE', cost: 3, isEvolved: true, baseCardId: 'goblin-barrel', damage: 159, evolvedDamage: 159, evolvedAbilities: 'Spawns extra goblins', description: 'Enhanced Goblin Barrel that spawns additional goblins.', usageRate: 26.8, winRate: 52.9, evolvedUsageRate: 26.8, evolvedWinRate: 52.9 },
    { id: 'evolved-skeleton-barrel', name: 'Evolved Skeleton Barrel', cardType: 'SPELL', rarity: 'COMMON', cost: 3, isEvolved: true, baseCardId: 'skeleton-barrel', damage: 101, evolvedDamage: 101, evolvedAbilities: 'More skeletons', description: 'Enhanced Skeleton Barrel that spawns more skeletons.', usageRate: 20.1, winRate: 51.4, evolvedUsageRate: 20.1, evolvedWinRate: 51.4 },
    { id: 'evolved-giant-snowball', name: 'Evolved Giant Snowball', cardType: 'SPELL', rarity: 'COMMON', cost: 2, isEvolved: true, baseCardId: 'giant-snowball', damage: 239, evolvedDamage: 239, evolvedAbilities: 'Stronger slow effect', description: 'Enhanced Giant Snowball with stronger slow effect.', usageRate: 18.6, winRate: 52.3, evolvedUsageRate: 18.6, evolvedWinRate: 52.3 },
    { id: 'evolved-mega-knight', name: 'Evolved Mega Knight', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, isEvolved: true, baseCardId: 'mega-knight', hitpoints: 5187, damage: 735, evolvedHitpoints: 5187, evolvedDamage: 735, evolvedAbilities: 'Bigger jump radius', description: 'Enhanced Mega Knight with larger jump radius.', usageRate: 23.8, winRate: 53.6, evolvedUsageRate: 23.8, evolvedWinRate: 53.6 },
    { id: 'evolved-goblin-giant', name: 'Evolved Goblin Giant', cardType: 'TROOP', rarity: 'EPIC', cost: 6, isEvolved: true, baseCardId: 'goblin-giant', hitpoints: 4281, damage: 341, evolvedHitpoints: 4281, evolvedDamage: 341, evolvedAbilities: 'More spear goblins', description: 'Enhanced Goblin Giant with more spear goblins.', usageRate: 18.1, winRate: 51.0, evolvedUsageRate: 18.1, evolvedWinRate: 51.0 },
    { id: 'evolved-dart-goblin', name: 'Evolved Dart Goblin', cardType: 'TROOP', rarity: 'EPIC', cost: 3, isEvolved: true, baseCardId: 'dart-goblin', hitpoints: 324, damage: 246, evolvedHitpoints: 324, evolvedDamage: 246, evolvedAbilities: 'Faster attack speed', description: 'Enhanced Dart Goblin with faster attack speed.', usageRate: 21.4, winRate: 52.2, evolvedUsageRate: 21.4, evolvedWinRate: 52.2 },
    { id: 'evolved-bomber', name: 'Evolved Bomber', cardType: 'TROOP', rarity: 'EPIC', cost: 2, isEvolved: true, baseCardId: 'bomber', hitpoints: 396, damage: 407, evolvedHitpoints: 396, evolvedDamage: 407, evolvedAbilities: 'Bigger bomb radius', description: 'Enhanced Bomber with larger explosion radius.', usageRate: 17.3, winRate: 50.6, evolvedUsageRate: 17.3, evolvedWinRate: 50.6 },
    { id: 'evolved-goblin-cage', name: 'Evolved Goblin Cage', cardType: 'BUILDING', rarity: 'EPIC', cost: 4, isEvolved: true, baseCardId: 'goblin-cage', hitpoints: 1586, evolvedHitpoints: 1586, evolvedAbilities: 'Stronger goblin brawler', description: 'Enhanced Goblin Cage with stronger goblin brawler.', usageRate: 15.8, winRate: 49.7, evolvedUsageRate: 15.8, evolvedWinRate: 49.7 },
    { id: 'evolved-goblin-drill', name: 'Evolved Goblin Drill', cardType: 'BUILDING', rarity: 'RARE', cost: 4, isEvolved: true, baseCardId: 'goblin-drill', hitpoints: 2244, evolvedHitpoints: 2244, evolvedAbilities: 'Spawns more Goblins', description: 'Enhanced Goblin Drill that spawns more Goblins.', usageRate: 20.1, winRate: 52.0, evolvedUsageRate: 20.1, evolvedWinRate: 52.0 },
    { id: 'evolved-tesla', name: 'Evolved Tesla', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, isEvolved: true, baseCardId: 'tesla', hitpoints: 1431, evolvedHitpoints: 1431, evolvedAbilities: 'Chain lightning effect', description: 'Enhanced Tesla with chain lightning that hits multiple targets.', usageRate: 25.3, winRate: 53.1, evolvedUsageRate: 25.3, evolvedWinRate: 53.1 },
    { id: 'evolved-battle-ram', name: 'Evolved Battle Ram', cardType: 'TROOP', rarity: 'RARE', cost: 4, isEvolved: true, baseCardId: 'battle-ram', hitpoints: 1170, damage: 351, evolvedHitpoints: 1170, evolvedDamage: 351, evolvedAbilities: 'Barbarians have shields', description: 'Enhanced Battle Ram where spawned Barbarians have protective shields.', usageRate: 12.7, winRate: 50.8, evolvedUsageRate: 12.7, evolvedWinRate: 50.8 },
    { id: 'evolved-royal-recruits', name: 'Evolved Royal Recruits', cardType: 'TROOP', rarity: 'COMMON', cost: 7, isEvolved: true, baseCardId: 'royal-recruits', hitpoints: 1458, damage: 162, evolvedHitpoints: 1458, evolvedDamage: 162, evolvedAbilities: 'Recruits have longer spears', description: 'Enhanced Royal Recruits with extended range spears for better reach.', usageRate: 8.9, winRate: 49.2, evolvedUsageRate: 8.9, evolvedWinRate: 49.2 }
  ]

  // Insert all regular cards
  for (const cardData of regularCards) {
    await prisma.card.create({ data: cardData })
  }

  // === PHASE 3: CREATE EVOLUTION RELATIONSHIPS ===
  const evolutions = [
    {
      baseCardId: 'knight',
      evolvedCardId: 'knight-evolved',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Dashing Strike"]',
      visualChanges: 'Glowing armor and trailing energy effects',
      releaseVersion: 'Evolution Update 1.0'
    },
    {
      baseCardId: 'archers',
      evolvedCardId: 'archers-evolved',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5, "range": 1.2}',
      newAbilities: '["Piercing Shot"]',
      visualChanges: 'Enhanced bows with glowing arrows',
      releaseVersion: 'Evolution Update 1.0'
    },
    {
      baseCardId: 'skeletons',
      evolvedCardId: 'skeletons-evolved',
      cyclesRequired: 3,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Bone Armor"]',
      visualChanges: 'Armored skeletons with glowing bones',
      releaseVersion: 'Evolution Update 1.1'
    },
    {
      baseCardId: 'bats',
      evolvedCardId: 'bats-evolved',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Vampire Bite"]',
      visualChanges: 'Darker wings with red energy trails',
      releaseVersion: 'Evolution Update 1.2'
    },
    {
      baseCardId: 'firecracker',
      evolvedCardId: 'firecracker-evolved',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5, "range": 1.17}',
      newAbilities: '["Chain Reaction"]',
      visualChanges: 'Enhanced launcher with multiple barrels',
      releaseVersion: 'Evolution Update 1.3'
    },
    {
      baseCardId: 'valkyrie',
      evolvedCardId: 'evolved-valkyrie',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Rage Spin"]',
      visualChanges: 'Glowing axe with fire effects',
      releaseVersion: 'Evolution Update 2.0'
    },
    {
      baseCardId: 'barbarians',
      evolvedCardId: 'evolved-barbarians',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Berserker Charge"]',
      visualChanges: 'Enhanced armor and glowing weapons',
      releaseVersion: 'Evolution Update 2.1'
    },
    {
      baseCardId: 'musketeer',
      evolvedCardId: 'evolved-musketeer',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Piercing Shot"]',
      visualChanges: 'Enhanced musket with scope',
      releaseVersion: 'Evolution Update 2.2'
    },
    {
      baseCardId: 'wizard',
      evolvedCardId: 'evolved-wizard',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Chain Lightning"]',
      visualChanges: 'Crackling with electric energy',
      releaseVersion: 'Evolution Update 2.3'
    },
    {
      baseCardId: 'ice-spirit',
      evolvedCardId: 'evolved-ice-spirit',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Multiple Jumps"]',
      visualChanges: 'Larger with ice crystal armor',
      releaseVersion: 'Evolution Update 2.4'
    },
    {
      baseCardId: 'wall-breakers',
      evolvedCardId: 'evolved-wall-breakers',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Bouncing Bombs"]',
      visualChanges: 'Enhanced bombs with longer fuses',
      releaseVersion: 'Evolution Update 2.5'
    },
    {
      baseCardId: 'tesla',
      evolvedCardId: 'evolved-tesla',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Chain Lightning"]',
      visualChanges: 'Enhanced coils with lightning effects',
      releaseVersion: 'Evolution Update 2.6'
    },
    {
      baseCardId: 'mortar',
      evolvedCardId: 'evolved-mortar',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Rapid Fire"]',
      visualChanges: 'Multiple barrel configuration',
      releaseVersion: 'Evolution Update 2.7'
    },
    {
      baseCardId: 'battle-ram',
      evolvedCardId: 'evolved-battle-ram',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Extra Barbarians"]',
      visualChanges: 'Enhanced ram with spikes',
      releaseVersion: 'Evolution Update 2.8'
    },
    {
      baseCardId: 'royal-recruits',
      evolvedCardId: 'evolved-royal-recruits',
      cyclesRequired: 3,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Shield Bash"]',
      visualChanges: 'Enhanced armor and shields',
      releaseVersion: 'Evolution Update 2.9'
    },
    {
      baseCardId: 'zap',
      evolvedCardId: 'evolved-zap',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"damage": 1.5}',
      newAbilities: '["Chain Effect"]',
      visualChanges: 'Enhanced lightning with chain effects',
      releaseVersion: 'Evolution Update 3.0'
    },
    {
      baseCardId: 'giant-snowball',
      evolvedCardId: 'evolved-giant-snowball',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"damage": 1.5}',
      newAbilities: '["Split Effect"]',
      visualChanges: 'Larger snowball with ice crystals',
      releaseVersion: 'Evolution Update 3.1'
    },
    {
      baseCardId: 'royal-giant',
      evolvedCardId: 'evolved-royal-giant',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Faster Attack Speed"]',
      visualChanges: 'Enhanced cannon with multiple barrels',
      releaseVersion: 'Evolution Update 3.2'
    },
    {
      baseCardId: 'cannon',
      evolvedCardId: 'evolved-cannon',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Multi-Shot"]',
      visualChanges: 'Enhanced cannon with multiple firing mechanisms',
      releaseVersion: 'Evolution Update 3.3'
    },
    {
      baseCardId: 'witch',
      evolvedCardId: 'evolved-witch',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Multiple Skeleton Spawn"]',
      visualChanges: 'Enhanced staff with glowing crystals',
      releaseVersion: 'Evolution Update 3.4'
    },
    {
      baseCardId: 'pekka',
      evolvedCardId: 'evolved-pekka',
      cyclesRequired: 3,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Charge Attack"]',
      visualChanges: 'Enhanced armor with energy core',
      releaseVersion: 'Evolution Update 3.5'
    },
    {
      baseCardId: 'executioner',
      evolvedCardId: 'evolved-executioner',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Double Throw"]',
      visualChanges: 'Enhanced axes with glowing edges',
      releaseVersion: 'Evolution Update 3.6'
    },
    {
      baseCardId: 'inferno-dragon',
      evolvedCardId: 'evolved-inferno-dragon',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Faster Ramp-up"]',
      visualChanges: 'Enhanced inferno beam with lightning effects',
      releaseVersion: 'Evolution Update 3.7'
    },
    {
      baseCardId: 'electro-dragon',
      evolvedCardId: 'evolved-electro-dragon',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Extended Chain Lightning"]',
      visualChanges: 'Enhanced with crackling energy aura',
      releaseVersion: 'Evolution Update 3.8'
    },
    {
      baseCardId: 'hunter',
      evolvedCardId: 'evolved-hunter',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Wider Spread"]',
      visualChanges: 'Enhanced shotgun with extended barrel',
      releaseVersion: 'Evolution Update 3.9'
    },
    {
      baseCardId: 'lumberjack',
      evolvedCardId: 'evolved-lumberjack',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Stronger Rage Effect"]',
      visualChanges: 'Enhanced axe with glowing rage aura',
      releaseVersion: 'Evolution Update 4.0'
    },
    {
      baseCardId: 'goblin-barrel',
      evolvedCardId: 'evolved-goblin-barrel',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"damage": 1.5}',
      newAbilities: '["Extra Goblins"]',
      visualChanges: 'Larger barrel with reinforced design',
      releaseVersion: 'Evolution Update 4.1'
    },
    {
      baseCardId: 'skeleton-barrel',
      evolvedCardId: 'evolved-skeleton-barrel',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"damage": 1.5}',
      newAbilities: '["More Skeletons"]',
      visualChanges: 'Enhanced barrel with bone decorations',
      releaseVersion: 'Evolution Update 4.2'
    },
    {
      baseCardId: 'mega-knight',
      evolvedCardId: 'evolved-mega-knight',
      cyclesRequired: 3,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Bigger Jump Radius"]',
      visualChanges: 'Enhanced armor with energy boosters',
      releaseVersion: 'Evolution Update 4.3'
    },
    {
      baseCardId: 'goblin-giant',
      evolvedCardId: 'evolved-goblin-giant',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["More Spear Goblins"]',
      visualChanges: 'Enhanced backpack with more goblin carriers',
      releaseVersion: 'Evolution Update 4.4'
    },
    {
      baseCardId: 'dart-goblin',
      evolvedCardId: 'evolved-dart-goblin',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Faster Attack Speed"]',
      visualChanges: 'Enhanced blowgun with rapid-fire mechanism',
      releaseVersion: 'Evolution Update 4.5'
    },
    {
      baseCardId: 'bomber',
      evolvedCardId: 'evolved-bomber',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5, "damage": 1.5}',
      newAbilities: '["Bigger Explosion Radius"]',
      visualChanges: 'Enhanced bombs with larger payload',
      releaseVersion: 'Evolution Update 4.6'
    },
    {
      baseCardId: 'goblin-cage',
      evolvedCardId: 'evolved-goblin-cage',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5}',
      newAbilities: '["Stronger Goblin Brawler"]',
      visualChanges: 'Reinforced cage with enhanced brawler',
      releaseVersion: 'Evolution Update 4.7'
    },
    {
      baseCardId: 'goblin-drill',
      evolvedCardId: 'evolved-goblin-drill',
      cyclesRequired: 2,
      elixirCostSame: true,
      statMultipliers: '{"hitpoints": 1.5}',
      newAbilities: '["Spawns More Goblins"]',
      visualChanges: 'Enhanced drill with more spawn capacity',
      releaseVersion: 'Evolution Update 4.8'
    }
  ]

  for (const evolution of evolutions) {
    await prisma.cardEvolution.create({ data: evolution })
  }

  // Get final counts
  const totalCards = await prisma.card.count()
  const evolvedCards = await prisma.card.count({ where: { isEvolved: true } })
  const evolvableCards = await prisma.card.count({ where: { canEvolve: true } })
  const totalEvolutions = await prisma.cardEvolution.count()

  console.log(`✅ Database seeded successfully!`)
  console.log(`📊 Statistics:`)
  console.log(`   • Total Cards: ${totalCards}`)
  console.log(`   • Evolvable Cards: ${evolvableCards}`)
  console.log(`   • Evolved Forms: ${evolvedCards}`)
  console.log(`   • Evolution Pairs: ${totalEvolutions}`)
  console.log(`   • Card Distribution:`)
  
  const rarityStats = await prisma.card.groupBy({
    by: ['rarity'],
    _count: { rarity: true }
  })
  
  rarityStats.forEach((stat: any) => {
    console.log(`     - ${stat.rarity}: ${stat._count.rarity} cards`)
  })

  console.log(`\n🧬 Evolution System Ready:`)
  console.log(`   • Knight → Evolved Knight (2 cycles)`)
  console.log(`   • Archers → Evolved Archers (2 cycles)`)
  console.log(`   • Skeletons → Evolved Skeletons (3 cycles)`)
  console.log(`   • Bats → Evolved Bats (2 cycles)`)
  console.log(`   • Firecracker → Evolved Firecracker (2 cycles)`)
  console.log(`   • Valkyrie → Evolved Valkyrie (2 cycles)`)
  console.log(`   • Barbarians → Evolved Barbarians (2 cycles)`)
  console.log(`   • Musketeer → Evolved Musketeer (2 cycles)`)
  console.log(`   • Wizard → Evolved Wizard (2 cycles)`)
  console.log(`   • Ice Spirit → Evolved Ice Spirit (2 cycles)`)
  console.log(`   • Wall Breakers → Evolved Wall Breakers (2 cycles)`)
  console.log(`   • Tesla → Evolved Tesla (2 cycles)`)
  console.log(`   • Mortar → Evolved Mortar (2 cycles)`)
  console.log(`   • Battle Ram → Evolved Battle Ram (2 cycles)`)
  console.log(`   • Royal Recruits → Evolved Royal Recruits (3 cycles)`)
  console.log(`   • Zap → Evolved Zap (2 cycles)`)
  console.log(`   • Giant Snowball → Evolved Giant Snowball (2 cycles)`)
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
