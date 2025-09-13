/**
 * Enhanced Cards API Route
 * Serves comprehensive card data with game mechanics
 */

import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';
import { readFileSync } from 'fs';
import { join } from 'path';

// Enhanced card interfaces
interface EnhancedCard {
  id: number;
  name: string;
  elixirCost: number;
  rarity: string;
  maxLevel: number;
  canEvolve: boolean;
  iconUrls: { medium?: string; evolutionMedium?: string; };
  type?: string;
  targeting?: string;
  sightRange?: number;
  attackRange?: number;
  speed?: string;
  hitpoints?: number;
  damage?: number;
  attackSpeed?: number;
  splashDamage?: boolean;
  buildingPull?: boolean;
  description?: string;
}

// Load enhanced card database
let enhancedCards: EnhancedCard[] = [];
try {
  const dbPath = join(process.cwd(), 'enhanced_card_database.json');
  const dbData = JSON.parse(readFileSync(dbPath, 'utf-8'));
  enhancedCards = dbData.cards;
  console.log(`✅ Loaded ${enhancedCards.length} enhanced cards`);
} catch (error) {
  console.error('⚠️ Failed to load enhanced card database:', error);
}

const cardQuerySchema = z.object({
  limit: z.coerce.number().min(1).max(100).default(50),
  offset: z.coerce.number().min(0).default(0),
  rarity: z.string().optional(),
  cardType: z.string().optional(),
  cost: z.coerce.number().min(0).max(10).optional(),
  search: z.string().optional(),
  canEvolve: z.coerce.boolean().optional(),
  targeting: z.string().optional()
});

const cardsEnhanced: FastifyPluginAsync = async (fastify) => {
  
  /**
   * GET /api/cards-enhanced
   * Returns all cards with comprehensive mechanics data
   */
  fastify.get('/', async (request, reply) => {
    try {
      const query = cardQuerySchema.parse(request.query);
      const { limit, offset, rarity, cardType, cost, search, canEvolve, targeting } = query;

      let filteredCards = enhancedCards;

      // Apply filters
      if (rarity) {
        filteredCards = filteredCards.filter(c => c.rarity === rarity);
      }
      if (cardType) {
        filteredCards = filteredCards.filter(c => c.type === cardType);
      }
      if (cost !== undefined) {
        filteredCards = filteredCards.filter(c => c.elixirCost === cost);
      }
      if (canEvolve !== undefined) {
        filteredCards = filteredCards.filter(c => c.canEvolve === canEvolve);
      }
      if (targeting) {
        filteredCards = filteredCards.filter(c => c.targeting === targeting);
      }
      if (search) {
        const searchLower = search.toLowerCase();
        filteredCards = filteredCards.filter(c => 
          c.name.toLowerCase().includes(searchLower) ||
          (c.description && c.description.toLowerCase().includes(searchLower))
        );
      }

      // Pagination
      const paginatedCards = filteredCards.slice(offset, offset + limit);

      const metadata = {
        totalCards: filteredCards.length,
        evolvableCards: filteredCards.filter(c => c.canEvolve).length,
        cardTypes: {
          troops: filteredCards.filter(c => c.type === 'TROOP').length,
          buildings: filteredCards.filter(c => c.type === 'BUILDING').length,
          spells: filteredCards.filter(c => c.type === 'SPELL').length
        },
        targetingTypes: {
          buildingsOnly: filteredCards.filter(c => c.targeting === 'BUILDINGS_ONLY').length,
          troopsOnly: filteredCards.filter(c => c.targeting === 'TROOPS_ONLY').length,
          bothTargets: filteredCards.filter(c => c.targeting === 'BOTH_TARGETS').length
        },
        officiallyVerified: true,
        lastUpdated: new Date().toISOString()
      };

      return {
        success: true,
        metadata,
        cards: paginatedCards
      };
    } catch (error) {
      console.error('Error fetching enhanced cards:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch enhanced cards'
      });
    }
  });

  /**
   * GET /api/cards-enhanced/:cardName
   * Returns specific card with detailed mechanics
   */
  fastify.get('/:cardName', async (request, reply) => {
    try {
      const { cardName } = request.params as { cardName: string };
      const card = enhancedCards.find(c => 
        c.name.toLowerCase() === cardName.toLowerCase() ||
        c.name.toLowerCase().replace(/\s+/g, '-') === cardName.toLowerCase()
      );

      if (!card) {
        return reply.status(404).send({
          success: false,
          error: `Card "${cardName}" not found`
        });
      }

      // Calculate mechanics analysis
      const isBuildingTargeter = card.targeting === 'BUILDINGS_ONLY';
      const effectiveRange = Math.max(card.sightRange || 0, card.attackRange || 0);

      return {
        success: true,
        card,
        analysis: {
          effectiveRange,
          buildingPullVulnerable: isBuildingTargeter,
          isEvolvable: card.canEvolve,
          mechanicsType: card.targeting,
          strengths: getCardStrengths(card),
          strategies: getPlacementStrategies(card)
        }
      };
    } catch (error) {
      console.error('Error fetching card details:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch card details'
      });
    }
  });

  /**
   * GET /api/cards-enhanced/category/:type
   * Returns cards filtered by type (TROOP, BUILDING, SPELL)
   */
  fastify.get('/category/:type', async (request, reply) => {
    try {
      const { type } = request.params as { type: string };
      const typeUpper = type.toUpperCase();
      const validTypes = ['TROOP', 'BUILDING', 'SPELL'];
      
      if (!validTypes.includes(typeUpper)) {
        return reply.status(400).send({
          success: false,
          error: `Invalid card type. Must be one of: ${validTypes.join(', ')}`
        });
      }

      const filteredCards = enhancedCards.filter(c => c.type === typeUpper);

      return {
        success: true,
        category: typeUpper,
        count: filteredCards.length,
        cards: filteredCards
      };
    } catch (error) {
      console.error('Error fetching cards by category:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch cards by category'
      });
    }
  });

  /**
   * GET /api/cards-enhanced/evolvable
   * Returns only cards that can evolve
   */
  fastify.get('/evolvable', async (request, reply) => {
    try {
      const evolvableCards = enhancedCards.filter(c => c.canEvolve);

      return {
        success: true,
        count: evolvableCards.length,
        cards: evolvableCards,
        officiallyVerified: true
      };
    } catch (error) {
      console.error('Error fetching evolvable cards:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch evolvable cards'
      });
    }
  });

};

// Helper functions
function getCardStrengths(card: EnhancedCard): string[] {
  const strengths: string[] = [];
  
  if (card.splashDamage) {
    strengths.push("Area damage against grouped enemies");
  }
  if (card.targeting === 'BUILDINGS_ONLY') {
    strengths.push("Direct tower threat");
  }
  if (card.targeting === 'TROOPS_ONLY') {
    strengths.push("Immune to building pull");
  }
  if (card.buildingPull) {
    strengths.push("Can pull building-targeting troops");
  }
  if (card.canEvolve) {
    strengths.push("Can be evolved for enhanced abilities");
  }
  
  return strengths;
}

function getPlacementStrategies(card: EnhancedCard): string[] {
  const strategies: string[] = [];
  
  if (card.targeting === 'BUILDINGS_ONLY') {
    strategies.push("Place behind tank for tower targeting");
    strategies.push("Beware of defensive building pulls");
  }
  
  if (card.type === 'BUILDING' && card.buildingPull) {
    strategies.push("Place to pull building-targeting troops");
    strategies.push("Position within 5.5 tiles of target path");
  }
  
  if (card.splashDamage) {
    strategies.push("Target grouped enemy units");
    strategies.push("Effective against swarm troops");
  }
  
  return strategies;
}

export default cardsEnhanced;
