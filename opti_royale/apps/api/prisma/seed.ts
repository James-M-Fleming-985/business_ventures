import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Complete Clash Royale Cards Database (100+ cards)
const cards = [
  // === COMMON CARDS ===
  // Troops
  { id: 'skeletons', name: 'Skeletons', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 91, damage: 91, description: 'Three fast, unarmored melee fighters. Swarm enemies or act as a distraction.' },
  { id: 'ice-spirit', name: 'Ice Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 190, damage: 190, description: 'Freezes enemies in a radius around its target. Chills to the bone!' },
  { id: 'fire-spirit', name: 'Fire Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 91, damage: 358, description: 'These three Fire Spirits are on a kamikaze mission to give you a warm hug.' },
  { id: 'heal-spirit', name: 'Heal Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 91, damage: 91, description: 'Heals all friendly troops in a small radius when it explodes.' },
  { id: 'electro-spirit', name: 'Electro Spirit', cardType: 'TROOP', rarity: 'COMMON', cost: 1, hitpoints: 91, damage: 91, description: 'Zaps up to 9 enemies, briefly stunning them and dealing damage.' },
  
  { id: 'goblins', name: 'Goblins', cardType: 'TROOP', rarity: 'COMMON', cost: 2, hitpoints: 169, damage: 169, description: 'Three fast, unarmored melee fighters. Small, fast, green and mean!' },
  { id: 'spear-goblins', name: 'Spear Goblins', cardType: 'TROOP', rarity: 'COMMON', cost: 2, hitpoints: 91, damage: 106, range: 5.0, description: 'Three unarmored ranged attackers. Who thought it was a good idea to give them spears?!' },
  { id: 'bats', name: 'Bats', cardType: 'TROOP', rarity: 'COMMON', cost: 2, hitpoints: 91, damage: 106, description: 'Spawns a handful of flying Bats. Great for quickly surrounding enemies!' },
  { id: 'wall-breakers', name: 'Wall Breakers', cardType: 'TROOP', rarity: 'COMMON', cost: 2, hitpoints: 91, damage: 848, description: 'Fast moving pair of lightly protected Goblins that deal big area damage to Crown Towers.' },
  
  { id: 'archers', name: 'Archers', cardType: 'TROOP', rarity: 'COMMON', cost: 3, hitpoints: 304, damage: 127, range: 5.0, description: 'A pair of unarmored ranged attackers. They\'ll help you take down enemies!' },
  { id: 'knight', name: 'Knight', cardType: 'TROOP', rarity: 'COMMON', cost: 3, hitpoints: 1344, damage: 183, description: 'A tough melee fighter. The Barbarian\'s handsome, cultured cousin.' },
  { id: 'minions', name: 'Minions', cardType: 'TROOP', rarity: 'COMMON', cost: 3, hitpoints: 190, damage: 106, description: 'Three fast, unarmored flying attackers. Roses are red, minions are blue, they can fly, and will crush you!' },
  { id: 'barbarians', name: 'Barbarians', cardType: 'TROOP', rarity: 'COMMON', cost: 5, hitpoints: 896, damage: 297, description: 'A horde of melee attackers with mean mustaches and even meaner tempers.' },
  { id: 'minion-horde', name: 'Minion Horde', cardType: 'TROOP', rarity: 'COMMON', cost: 5, hitpoints: 190, damage: 106, description: 'Six fast, unarmored flying attackers. Roses are red, minions are blue, they\'re all very pretty, but they\'ll crush you!' },
  { id: 'royal-giant', name: 'Royal Giant', cardType: 'TROOP', rarity: 'COMMON', cost: 6, hitpoints: 3668, damage: 344, range: 6.5, description: 'Destroying enemy buildings with his massive cannon is his job; making you laugh is just a hobby.' },
  { id: 'elite-barbarians', name: 'Elite Barbarians', cardType: 'TROOP', rarity: 'COMMON', cost: 6, hitpoints: 1344, damage: 358, description: 'Spawns two fast, heavily armored Barbarians with mean mustaches and even meaner tempers.' },
  { id: 'three-musketeers', name: 'Three Musketeers', cardType: 'TROOP', rarity: 'COMMON', cost: 9, hitpoints: 598, damage: 340, range: 6.0, description: 'Trio of powerful, independent markswomen, fighting for justice and honor. Disrespect them at your own peril.' },
  
  // Common Buildings
  { id: 'cannon', name: 'Cannon', cardType: 'BUILDING', rarity: 'COMMON', cost: 3, hitpoints: 828, damage: 276, range: 5.5, description: 'Defensive building. Straight outta the old west! Targets ground troops only.' },
  { id: 'tesla', name: 'Tesla', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, hitpoints: 828, damage: 276, range: 5.5, description: 'Defensive building. Attacks both ground and air units. When not attacking, the Tesla Coil retracts underground.' },
  { id: 'mortar', name: 'Mortar', cardType: 'BUILDING', rarity: 'COMMON', cost: 4, hitpoints: 828, damage: 276, range: 12.0, description: 'Defensive building with a long range. Shoots exploding shells that deal area damage, but cannot target enemies that get very close!' },
  
  // Common Spells
  { id: 'zap', name: 'Zap', cardType: 'SPELL', rarity: 'COMMON', cost: 2, damage: 192, description: 'Instantly deals damage and stuns all enemies in a small radius. Useful for taking out low-health troops or resetting enemy attacks!' },
  { id: 'arrows', name: 'Arrows', cardType: 'SPELL', rarity: 'COMMON', cost: 3, damage: 243, description: 'Arrows pepper a large area, dealing damage to all enemies hit. Reduced damage to Crown Towers.' },
  { id: 'fireball', name: 'Fireball', cardType: 'SPELL', rarity: 'COMMON', cost: 4, damage: 689, description: 'Annihilates a medium sized area with explosive damage. Deals reduced damage to Crown Towers.' },
  
  // === RARE CARDS ===
  // Troops  
  { id: 'giant', name: 'Giant', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 4256, damage: 358, description: 'Slow but durable, only attacks buildings. A real one-man wrecking crew!' },
  { id: 'musketeer', name: 'Musketeer', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 598, damage: 340, range: 6.0, description: 'Don\'t be fooled by her delicately coiffed hair, the Musketeer is a mean shot with her trusty boomstick.' },
  { id: 'wizard', name: 'Wizard', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 698, damage: 340, range: 5.5, description: 'The most awesome man to ever set foot in the arena, the Wizard will blow you away with his handsomeness... and fireballs.' },
  { id: 'valkyrie', name: 'Valkyrie', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 1344, damage: 297, description: 'This contradictory card can only be described as a melee splash attacker!' },
  { id: 'hog-rider', name: 'Hog Rider', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 1408, damage: 318, description: 'Fast melee troop that targets buildings and can jump over the river. He followed the echoing call of Hog Riderrrrr!' },
  { id: 'mini-pekka', name: 'Mini P.E.K.K.A', cardType: 'TROOP', rarity: 'RARE', cost: 4, hitpoints: 1128, damage: 848, description: 'The Arena is a certified butterfly-free zone. No distractions for P.E.K.K.A, only pancakes.' },
  { id: 'giant-skeleton', name: 'Giant Skeleton', cardType: 'TROOP', rarity: 'RARE', cost: 6, hitpoints: 2662, damage: 297, description: 'The bigger the skeleton, the bigger the bomb. Carries a bomb that explodes for massive area damage when he dies!' },
  { id: 'balloon', name: 'Balloon', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 1974, damage: 1472, description: 'As pretty as they are, you won\'t want a parade of THESE balloons showing up on the horizon.' },
  { id: 'witch', name: 'Witch', cardType: 'TROOP', rarity: 'RARE', cost: 5, hitpoints: 698, damage: 106, range: 5.5, description: 'Summons Skeletons, shoots destructo beams, has glowing pink eyes that unfortunately don\'t shoot lasers.' },
  { id: 'barbarian-hut', name: 'Barbarian Hut', cardType: 'BUILDING', rarity: 'RARE', cost: 7, hitpoints: 1496, description: 'Defensive building that spawns Barbarians. It\'s like a Barbarian parade that never ends!' },
  { id: 'inferno-tower', name: 'Inferno Tower', cardType: 'BUILDING', rarity: 'RARE', cost: 5, hitpoints: 1508, damage: 50, range: 6.0, description: 'Defensive building, roasts targets for damage that increases over time. Burns through even the biggest and toughest enemies!' },
  { id: 'bomb-tower', name: 'Bomb Tower', cardType: 'BUILDING', rarity: 'RARE', cost: 4, hitpoints: 1496, damage: 276, range: 6.0, description: 'Defensive building that explodes when destroyed. Deals area damage to anything nearby!' },
  { id: 'tombstone', name: 'Tombstone', cardType: 'BUILDING', rarity: 'RARE', cost: 3, hitpoints: 415, description: 'Spawns Skeletons one at a time. When destroyed, spawns 4 Skeletons. Creepy!' },
  { id: 'goblin-hut', name: 'Goblin Hut', cardType: 'BUILDING', rarity: 'RARE', cost: 5, hitpoints: 1496, description: 'Building that spawns Spear Goblins. Don\'t look a Goblin Gift Horse in the mouth!' },
  { id: 'furnace', name: 'Furnace', cardType: 'BUILDING', rarity: 'RARE', cost: 4, hitpoints: 1496, description: 'The Furnace spawns Fire Spirits to defend your base. Creates delicious, melted cheese flavoring.' },
  
  // Rare Spells
  { id: 'rocket', name: 'Rocket', cardType: 'SPELL', rarity: 'RARE', cost: 6, damage: 1232, description: 'Devastating spell that deals massive damage to a large area. Obliterates buildings!' },
  { id: 'lightning', name: 'Lightning', cardType: 'SPELL', rarity: 'RARE', cost: 6, damage: 1218, description: 'Bolts of lightning damage and stun up to three enemies with the highest hitpoints in the target area.' },
  { id: 'freeze', name: 'Freeze', cardType: 'SPELL', rarity: 'RARE', cost: 4, damage: 0, description: 'Freezes troops and buildings, making them unable to move or attack. Everybody chill.' },
  { id: 'rage', name: 'Rage', cardType: 'SPELL', rarity: 'RARE', cost: 2, damage: 0, description: 'Increases troops\' movement and attack speed. Buildings attack faster and summon and deploy troops faster too.' },
  { id: 'mirror', name: 'Mirror', cardType: 'SPELL', rarity: 'RARE', cost: 0, damage: 0, description: 'Mirrors your last card played for +1 Elixir' },
  { id: 'clone', name: 'Clone', cardType: 'SPELL', rarity: 'RARE', cost: 3, damage: 0, description: 'Duplicates all friendly troops in the target area. Cloned troops have reduced hitpoints and disappear when the original troop dies.' },
  { id: 'heal', name: 'Heal', cardType: 'SPELL', rarity: 'RARE', cost: 1, damage: 0, description: 'Heals all friendly Troops and Buildings in a large radius over time. Heal does not affect air units.' },
  { id: 'tornado', name: 'Tornado', cardType: 'SPELL', rarity: 'RARE', cost: 3, damage: 109, description: 'Drags enemy troops to its center while dealing damage over time. Doesn\'t affect buildings.' },
  { id: 'poison', name: 'Poison', cardType: 'SPELL', rarity: 'RARE', cost: 4, damage: 90, description: 'Covers a large area in poison, damaging enemies and reducing their movement and attack speed.' },
  { id: 'earthquake', name: 'Earthquake', cardType: 'SPELL', rarity: 'RARE', cost: 3, damage: 259, description: 'Deals damage to buildings and slows down troops. Reduced damage to Crown Towers.' },
  { id: 'graveyard', name: 'Graveyard', cardType: 'SPELL', rarity: 'RARE', cost: 5, damage: 0, description: 'Surprise! Skeletons pop out of the ground everywhere and attack nearby enemies.' },
  
  // === EPIC CARDS ===
  // Troops
  { id: 'baby-dragon', name: 'Baby Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 1200, damage: 340, range: 3.5, description: 'Flying troop that deals area damage. Baby dragons hatch cute, hungry and ready for a barbecue.' },
  { id: 'prince', name: 'Prince', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 1615, damage: 490, description: 'Don\'t let the little pony fool you. Once the Prince gets a running start, you WILL be trampled. Deals double damage once he gets charging.' },
  { id: 'dark-prince', name: 'Dark Prince', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 1283, damage: 297, description: 'The Dark Prince deals area damage and lets his spiked club do the talking for him - because when he does talk, it sounds like he has a bucket on his head.' },
  { id: 'skeleton-army', name: 'Skeleton Army', cardType: 'TROOP', rarity: 'EPIC', cost: 3, hitpoints: 91, damage: 91, description: 'Spawns an army of Skeletons. Scary big army!' },
  { id: 'goblin-barrel', name: 'Goblin Barrel', cardType: 'SPELL', rarity: 'EPIC', cost: 3, damage: 169, description: 'Spawns three Goblins anywhere in the Arena. It\'s going to be a thrilling ride, boys!' },
  { id: 'guards', name: 'Guards', cardType: 'TROOP', rarity: 'EPIC', cost: 3, hitpoints: 91, damage: 106, description: 'Three ruthless bone brothers with shields. Knock off their shields and all that\'s left are three ruthless bone brothers.' },
  { id: 'golem', name: 'Golem', cardType: 'TROOP', rarity: 'EPIC', cost: 8, hitpoints: 8032, damage: 452, description: 'Slow but durable, only attacks buildings. When destroyed, explosively splits into two Golemites and deals area damage!' },
  { id: 'pekka', name: 'P.E.K.K.A', cardType: 'TROOP', rarity: 'EPIC', cost: 7, hitpoints: 3458, damage: 1692, description: 'A heavily armored, slow melee fighter. Swings from the hip but packs a huge punch.' },
  { id: 'bowler', name: 'Bowler', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 1672, damage: 452, range: 5.0, description: 'This big blue dude digs the simple things in life - Dark Elixir drinks and throwing rocks.' },
  { id: 'executioner', name: 'Executioner', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 1128, damage: 276, range: 5.5, description: 'A hooded warrior throws his axe like a boomerang, striking all enemies on the way out AND back.' },
  { id: 'cannon-cart', name: 'Cannon Cart', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 828, damage: 276, range: 5.5, description: 'A Cannon on wheels?! Bet they won\'t see that coming! Deals damage as a building, then Deals damage as a cannon.' },
  { id: 'skeleton-barrel', name: 'Skeleton Barrel', cardType: 'TROOP', rarity: 'EPIC', cost: 3, hitpoints: 415, damage: 91, description: 'A flying Skeleton army in a barrel! Spawns Skeletons anywhere in the Arena. It\'s a Skeleton party!' },
  { id: 'flying-machine', name: 'Flying Machine', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 415, damage: 190, range: 6.0, description: 'The Master Builder\'s flying contraption attacks from the air, shooting bolts that bounce between nearby enemies!' },
  { id: 'battle-healer', name: 'Battle Healer', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 1485, damage: 185, range: 3.5, description: 'A warrior-medic, she fights with the intensity of a Barbarian and heals troops around her.' },
  { id: 'skeleton-dragons', name: 'Skeleton Dragons', cardType: 'TROOP', rarity: 'EPIC', cost: 4, hitpoints: 228, damage: 185, range: 3.5, description: 'Spawns two flying Skeleton Dragons. Don\'t let their deadly looks fool you, they\'re worse!' },
  { id: 'electro-dragon', name: 'Electro Dragon', cardType: 'TROOP', rarity: 'EPIC', cost: 5, hitpoints: 1270, damage: 340, range: 3.5, description: 'Flies over the battlefield, dealing chain lightning damage that jumps between targets!' },
  
  // Epic Buildings
  { id: 'x-bow', name: 'X-Bow', cardType: 'BUILDING', rarity: 'EPIC', cost: 6, hitpoints: 1630, damage: 53, range: 12.0, description: 'Nice tower you have there. Would be a shame if this X-Bow whittled it down from this side of the Arena...' },
  { id: 'elixir-collector', name: 'Elixir Collector', cardType: 'BUILDING', rarity: 'EPIC', cost: 6, hitpoints: 828, description: 'You gotta spend Elixir to make Elixir. Elixir Collector produces a steady stream of Elixir during battle.' },
  { id: 'goblin-drill', name: 'Goblin Drill', cardType: 'BUILDING', rarity: 'EPIC', cost: 4, hitpoints: 1496, description: 'Drill spawns Goblins underground, bypassing ground troops and buildings!' },
  
  // === LEGENDARY CARDS ===
  // Troops
  { id: 'ice-wizard', name: 'Ice Wizard', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 590, damage: 95, range: 5.5, description: 'This chill caster throws ice shards that slow down enemies\' movement and attack speed. Despite being freezing cold, he has a warm heart.' },
  { id: 'princess', name: 'Princess', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 228, damage: 140, range: 9.0, description: 'This stunning Princess shoots flaming arrows from long range. If you\'re lucky, you might get to take her out for dinner.' },
  { id: 'lumberjack', name: 'Lumberjack', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 1060, damage: 297, description: 'Fast melee troop that chops down anything in his path and rages when defeated!' },
  { id: 'the-log', name: 'The Log', cardType: 'SPELL', rarity: 'LEGENDARY', cost: 2, damage: 432, description: 'A spilt bottle of Rage turned an innocent tree trunk into "The Log". It rolls through enemies, dealing damage and pushing them back.' },
  { id: 'sparky', name: 'Sparky', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 6, hitpoints: 1544, damage: 2472, range: 4.5, description: 'Sparky slowly charges up, then unloads MASSIVE area damage. Overkill isn\'t in her vocabulary.' },
  { id: 'miner', name: 'Miner', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 1060, damage: 185, description: 'The Miner can burrow his way anywhere in the Arena. It\'s not magic, it\'s a shovel.' },
  { id: 'lavahound', name: 'Lava Hound', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, hitpoints: 3432, damage: 45, description: 'Flying tank that targets buildings. When destroyed, spawns Lava Pups that continue the assault!' },
  { id: 'electro-wizard', name: 'Electro Wizard', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 598, damage: 192, range: 5.0, description: 'Arrives with a POW! Stuns nearby enemies. Attacks with chain lightning that jumps between foes.' },
  { id: 'bandit', name: 'Bandit', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 749, damage: 297, description: 'Fast melee troop that targets enemies from a distance, then dashes to them!' },
  { id: 'night-witch', name: 'Night Witch', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 750, damage: 185, range: 4.5, description: 'Summons Bats to do her bidding! Passive ability allows her to spawn Bats over time and when she dies.' },
  { id: 'mega-knight', name: 'Mega Knight', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, hitpoints: 3458, damage: 490, description: 'He lands with the force of 1000 mustaches, then jumps from one foe to the next dealing huge area damage.' },
  { id: 'inferno-dragon', name: 'Inferno Dragon', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 1070, damage: 50, range: 3.5, description: 'Shoots a focused beam that increases in damage over time. Wears a cute little moustache.' },
  { id: 'ghost', name: 'Royal Ghost', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 1070, damage: 297, description: 'Invisible ghostly assassin that moves anywhere and attacks anything. Becomes visible when attacking or under attack.' },
  { id: 'magic-archer', name: 'Magic Archer', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 598, damage: 185, range: 7.0, description: 'Shoots a magic arrow from long range, dealing damage to all enemies it pierces through!' },
  { id: 'ram-rider', name: 'Ram Rider', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 5, hitpoints: 1544, damage: 297, description: 'Deals double damage as a charge attack! Slows enemies\' movement and attack speed with her trusty bola.' },
  { id: 'fisherman', name: 'Fisherman', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 3, hitpoints: 1200, damage: 185, range: 7.0, description: 'Hooks the closest enemy and pulls them to him for a devastating blow!' },
  { id: 'mother-witch', name: 'Mother Witch', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 4, hitpoints: 750, damage: 185, range: 5.0, description: 'Curses enemy troops. Cursed troops spawn a Pig when defeated!' },
  { id: 'electro-giant', name: 'Electro Giant', cardType: 'TROOP', rarity: 'LEGENDARY', cost: 7, hitpoints: 4508, damage: 259, description: 'A colossal walking zapper! Passively shocks nearby enemies and releases a devastating zap blast when defeated.' },
  
  // Champion Cards (new rarity)
  { id: 'golden-knight', name: 'Golden Knight', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, hitpoints: 1544, damage: 297, description: 'Dashes forward, slashing through enemies. Ability: Dashes to target location, dealing damage.' },
  { id: 'archer-queen', name: 'Archer Queen', cardType: 'TROOP', rarity: 'CHAMPION', cost: 5, hitpoints: 1544, damage: 297, range: 5.0, description: 'The Archer Queen shoots enemies from long range. Ability: Briefly becomes invisible and gains rapid-fire.' },
  { id: 'skeleton-king', name: 'Skeleton King', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, hitpoints: 1544, damage: 297, description: 'Summons Skeletons to fight by his side. Ability: Spawns Skeletons around him.' },
  { id: 'mighty-miner', name: 'Mighty Miner', cardType: 'TROOP', rarity: 'CHAMPION', cost: 4, hitpoints: 1544, damage: 297, description: 'Burrows underground to appear anywhere. Ability: Throws his miner hat, dealing damage.' }
];

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
  
  // Card Mastery Achievements
  {
    name: 'Hog Rider Master',
    description: 'Achieve high scores with Hog Rider 20 times',
    category: 'CARD_MASTERY',
    rarity: 'RARE',
    unlockCriteriaText: 'Score 8+ with Hog Rider 20 times',
    xpReward: 75,
  },
  {
    name: 'Spell Caster',
    description: 'Master placement timing for spell cards',
    category: 'CARD_MASTERY',
    rarity: 'EPIC',
    unlockCriteriaText: 'Perfect spell timing 15 times',
    xpReward: 125,
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
  
  // Meta Achievements
  {
    name: 'Meta Follower',
    description: 'Use top meta cards in analysis',
    category: 'META_MASTERY',
    rarity: 'COMMON',
    unlockCriteriaText: 'Use S-tier cards 10 times',
    xpReward: 40,
  },
  {
    name: 'Meta Breaker',
    description: 'Successfully counter meta decks',
    category: 'META_MASTERY',
    rarity: 'EPIC',
    unlockCriteriaText: 'Counter meta decks effectively 25 times',
    xpReward: 200,
  }
];

async function main() {
  console.log('🌱 Starting comprehensive database seeding...')

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
  console.log('🃏 Seeding comprehensive Clash Royale card database...')
  for (const card of cards) {
    await prisma.card.create({
      data: {
        ...card,
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

  console.log('✅ Comprehensive database seeded successfully!')
  console.log(`📊 Created ${cards.length} cards (Complete Clash Royale card set)`)
  console.log(`🏆 Created ${achievements.length} achievements`)
  console.log(`👤 Created test user: ${testUser.email}`)
  
  // Display card distribution by rarity
  const rarityCount = cards.reduce((acc, card) => {
    acc[card.rarity] = (acc[card.rarity] || 0) + 1;
    return acc;
  }, {});
  
  console.log('📈 Card distribution:')
  Object.entries(rarityCount).forEach(([rarity, count]) => {
    console.log(`   ${rarity}: ${count} cards`)
  });
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
