import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// ============================================================================
// VALIDATION SCHEMAS FOR CARD DATA
// ============================================================================

const cardQuerySchema = z.object({
  version: z.string().optional().default('current'),
  type: z.enum(['TROOP', 'SPELL', 'BUILDING']).optional(),
  rarity: z.enum(['COMMON', 'RARE', 'EPIC', 'LEGENDARY', 'CHAMPION']).optional(),
  cost: z.coerce.number().min(0).max(10).optional(),
  category: z.string().optional(),
  search: z.string().optional(),
  includeStats: z.coerce.boolean().default(true),
  limit: z.coerce.number().min(1).max(200).default(50),
  offset: z.coerce.number().min(0).default(0)
});

const cardStatsSchema = z.object({
  cardId: z.string(),
  gameVersion: z.string(),
  hitpoints: z.number().optional(),
  damage: z.number().optional(),
  dps: z.number().optional(),
  attackSpeed: z.number().optional(),
  range: z.number().optional(),
  splashRadius: z.number().optional(),
  splashDamage: z.number().optional(),
  deployTime: z.number().optional(),
  lifetime: z.number().optional(),
  spellDuration: z.number().optional(),
  cost: z.number().min(0).max(10).optional(),
  changeDescription: z.string().optional()
});

// ============================================================================
// CARD DATA ROUTES
// ============================================================================

const cardRoutes: FastifyPluginAsync = async (fastify) => {

  // Get all cards with optional filtering
  fastify.get('/cards', async (request, reply) => {
    try {
      const query = request.query as any;
      const version = query.version || 'current';
      const type = query.type;
      const rarity = query.rarity;
      const cost = query.cost ? parseInt(query.cost) : undefined;
      const category = query.category;
      const search = query.search;
      const includeStats = query.includeStats !== 'false';
      const limit = Math.min(Math.max(1, parseInt(query.limit) || 50), 200);
      const offset = Math.max(0, parseInt(query.offset) || 0);

      // Build where clause for filtering
      const where: any = {};
      
      if (type) where.type = type;
      if (rarity) where.rarity = rarity;
      if (cost !== undefined) where.cost = cost;
      if (category) where.category = category;
      if (search) {
        where.OR = [
          { name: { contains: search, mode: 'insensitive' } },
          { description: { contains: search, mode: 'insensitive' } }
        ];
      }

      // Fetch cards with simplified SQLite schema
      const cards = await prisma.card.findMany({
        where,
        orderBy: [
          { cost: 'asc' },
          { name: 'asc' }
        ],
        take: limit,
        skip: offset
      });

      // Format response for SQLite schema
      const formattedCards = cards.map((card: any) => ({
        id: card.id,
        name: card.name,
        cardType: card.cardType,
        rarity: card.rarity,
        cost: card.cost,
        description: card.description,
        hitpoints: card.hitpoints,
        damage: card.damage,
        attackSpeed: card.attackSpeed,
        range: card.range,
        gameVersion: card.gameVersion,
        usageRate: card.usageRate,
        winRate: card.winRate,
        createdAt: card.createdAt,
        updatedAt: card.updatedAt
      }));

      reply.send({
        success: true,
        data: formattedCards,
        pagination: {
          limit,
          offset,
          total: await prisma.card.count({ where })
        },
        version: version
      });

    } catch (error) {
      console.error('Error fetching cards:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to fetch card data'
      });
    }
  });

  // Get specific card by ID with full details
  fastify.get('/cards/:cardId', async (request, reply) => {
    try {
      const { cardId } = request.params as { cardId: string };
      const { version = 'current', includeHistory = false } = request.query as {
        version?: string;
        includeHistory?: boolean;
      };

      const card = await prisma.card.findUnique({
        where: { id: cardId }
      });

      if (!card) {
        return reply.code(404).send({
          success: false,
          error: 'Card not found'
        });
      }

      reply.send({
        success: true,
        data: {
          ...card
        }
      });

    } catch (error) {
      console.error('Error fetching card details:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to fetch card details'
      });
    }
  });

    // Balance changes endpoint - temporarily disabled for SQLite
  fastify.get('/balance-changes', async (request, reply) => {
    reply.send({
      success: true,
      data: [],
      message: 'Balance changes endpoint temporarily disabled in SQLite mode'
    });
  });

  // Get card meta analysis (usage rates, win rates, etc.)
  // Meta analysis endpoint - temporarily simplified for SQLite
  fastify.get('/meta-analysis', async (request, reply) => {
    try {
      // Get basic card data for meta analysis
      const cards = await prisma.card.findMany({
        orderBy: { usageRate: 'desc' },
        take: 20
      });

      const metaData = cards.map((card: any) => ({
        cardId: card.id,
        cardName: card.name,
        cardType: card.cardType,
        rarity: card.rarity,
        cost: card.cost,
        usageRate: card.usageRate || 0,
        winRate: card.winRate || 0,
        tier: (card.usageRate || 0) > 15 ? 'S' : 
              (card.usageRate || 0) > 10 ? 'A' : 
              (card.usageRate || 0) > 5 ? 'B' : 'C'
      }));

      reply.send({
        success: true,
        data: {
          timeframe: '30d',
          generatedAt: new Date().toISOString(),
          totalCards: metaData.length,
          metaCards: metaData
        }
      });

    } catch (error) {
      console.error('Error generating meta analysis:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to generate meta analysis'
      });
    }
  });

    // Admin route: Update card statistics manually - temporarily disabled for SQLite
  fastify.post('/admin/cards/:cardId/stats', {
    preHandler: [(fastify as any).authenticate] // Add admin check
  }, async (request, reply) => {
    reply.send({
      success: false,
      message: 'Admin stats endpoint temporarily disabled in SQLite mode'
    });
  });

};

export default cardRoutes;
