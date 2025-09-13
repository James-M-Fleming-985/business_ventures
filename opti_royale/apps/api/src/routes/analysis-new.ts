import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// ============================================================================
// VALIDATION SCHEMAS FOR PLACEMENT ANALYSIS
// ============================================================================

const placementAnalysisSchema = z.object({
  videoId: z.string(),
  frameTimestamp: z.number().min(0),
  placedCard: z.string(),
  userPlacement: z.object({
    x: z.number().min(0).max(7), // 8x8 tile grid (0-7)
    y: z.number().min(0).max(7)
  }),
  optimalPlacement: z.object({
    x: z.number().min(0).max(7),
    y: z.number().min(0).max(7)
  }),
  placementScore: z.number().min(1).max(10),
  feedbackMessage: z.string(),
  strategicReasoning: z.string(),
  improvementTip: z.string().optional(),
  boardState: z.object({
    elixirCount: z.number().optional(),
    opponentElixir: z.number().optional(),
    situation: z.string().optional(),
    units: z.array(z.object({
      card: z.string(),
      position: z.object({ x: z.number(), y: z.number() }),
      isOwn: z.boolean()
    })).optional()
  })
});

const analysisQuerySchema = z.object({
  userId: z.string().optional(),
  limit: z.coerce.number().min(1).max(100).default(20),
  offset: z.coerce.number().min(0).default(0),
  sortBy: z.enum(['createdAt', 'placementScore', 'frameTimestamp']).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc')
});

// ============================================================================
// PLACEMENT ANALYSIS ROUTES
// ============================================================================

const analysisRoutes: FastifyPluginAsync = async (fastify) => {
  
  // Create new placement analysis
  fastify.post('/placement-analysis', {
    preHandler: [fastify.authenticate],
    schema: {
      body: placementAnalysisSchema
    }
  }, async (request, reply) => {
    try {
      const userId = request.user.userId;
      const analysisData = request.body as z.infer<typeof placementAnalysisSchema>;

      // Create placement analysis record
      const analysis = await prisma.placementAnalysis.create({
        data: {
          userId,
          videoId: analysisData.videoId,
          frameTimestamp: analysisData.frameTimestamp,
          placedCard: analysisData.placedCard,
          userPlacement: JSON.stringify(analysisData.userPlacement),
          optimalPlacement: JSON.stringify(analysisData.optimalPlacement),
          placementScore: analysisData.placementScore,
          confidenceLevel: 0.95, // Default high confidence for testing
          feedbackMessage: analysisData.feedbackMessage,
          strategicReasoning: analysisData.strategicReasoning,
          improvementTip: analysisData.improvementTip,
          boardState: JSON.stringify(analysisData.boardState),
          tacticalSituation: analysisData.boardState.situation || 'Unknown',
          gameTimestamp: analysisData.frameTimestamp, // Assume frame timestamp = game timestamp for now
          elixirCount: analysisData.boardState.elixirCount,
          opponentElixir: analysisData.boardState.opponentElixir
        }
      });

      // Update user progress tracking
      await updateUserProgress(userId, analysisData.placementScore);

      // Check for achievements
      await checkPlacementAchievements(userId, analysis);

      reply.code(201).send({
        success: true,
        data: {
          analysisId: analysis.id,
          placementScore: analysis.placementScore,
          feedback: analysis.feedbackMessage,
          improvement: analysis.improvementTip,
          createdAt: analysis.createdAt
        }
      });

    } catch (error) {
      console.error('Error creating placement analysis:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to create placement analysis'
      });
    }
  });

  // Test endpoint for screen recording analysis
  fastify.post('/test-screen-recording', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { 
        videoFileName, 
        frameTimestamp, 
        placedCard, 
        userPlacement,
        notes 
      } = request.body as {
        videoFileName: string;
        frameTimestamp: number;
        placedCard: string;
        userPlacement: { x: number; y: number };
        notes?: string;
      };

      // Mock AI analysis for testing with your screen recordings
      const mockOptimalPlacement = {
        x: Math.max(0, Math.min(7, userPlacement.x + (Math.random() - 0.5) * 2)),
        y: Math.max(0, Math.min(7, userPlacement.y + (Math.random() - 0.5) * 2))
      };

      const distance = Math.sqrt(
        Math.pow(userPlacement.x - mockOptimalPlacement.x, 2) + 
        Math.pow(userPlacement.y - mockOptimalPlacement.y, 2)
      );
      
      const placementScore = Math.max(1, Math.min(10, 10 - distance * 2));

      const feedback = generatePlacementFeedback(placedCard, placementScore, distance);

      reply.send({
        success: true,
        data: {
          videoFileName,
          frameTimestamp,
          placedCard,
          userPlacement,
          optimalPlacement: mockOptimalPlacement,
          placementScore: Math.round(placementScore * 10) / 10,
          feedback: feedback.message,
          reasoning: feedback.reasoning,
          improvement: feedback.improvement,
          confidence: 0.85,
          notes
        },
        message: 'Mock analysis - will be replaced with real AI when computer vision is implemented'
      });

    } catch (error) {
      console.error('Error testing screen recording analysis:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to analyze screen recording'
      });
    }
  });

  // Get placement analyses for user
  fastify.get('/placement-analyses', {
    preHandler: [fastify.authenticate],
    schema: {
      querystring: analysisQuerySchema
    }
  }, async (request, reply) => {
    try {
      const userId = request.user.userId;
      const { limit, offset, sortBy, sortOrder } = request.query as z.infer<typeof analysisQuerySchema>;

      const analyses = await prisma.placementAnalysis.findMany({
        where: { userId },
        include: {
          video: {
            select: {
              filename: true,
              duration: true,
              gameMode: true,
              matchResult: true
            }
          }
        },
        orderBy: { [sortBy]: sortOrder },
        take: limit,
        skip: offset
      });

      // Parse JSON fields for response
      const formattedAnalyses = analyses.map(analysis => ({
        ...analysis,
        userPlacement: JSON.parse(analysis.userPlacement as string),
        optimalPlacement: JSON.parse(analysis.optimalPlacement as string),
        boardState: JSON.parse(analysis.boardState as string)
      }));

      reply.send({
        success: true,
        data: formattedAnalyses,
        pagination: {
          limit,
          offset,
          total: await prisma.placementAnalysis.count({ where: { userId } })
        }
      });

    } catch (error) {
      console.error('Error fetching placement analyses:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to fetch placement analyses'
      });
    }
  });

  // Get user progress and improvement stats
  fastify.get('/progress', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const userId = request.user.userId;
      const { period = 'week' } = request.query as { period?: 'week' | 'month' | 'all' };

      let whereClause: any = { userId };
      const now = new Date();
      
      if (period === 'week') {
        const weekStart = new Date(now.setDate(now.getDate() - 7));
        whereClause.trackingDate = { gte: weekStart };
      } else if (period === 'month') {
        const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
        whereClause.trackingDate = { gte: monthStart };
      }

      const progress = await prisma.progressTracking.findMany({
        where: whereClause,
        orderBy: { trackingDate: 'desc' }
      });

      // Calculate summary statistics
      const summary = {
        totalAnalyses: progress.reduce((sum, p) => sum + p.totalAnalyses, 0),
        averageScore: progress.length > 0 
          ? progress.reduce((sum, p) => sum + p.averagePlacementScore, 0) / progress.length 
          : 0,
        bestScore: progress.length > 0 ? Math.max(...progress.map(p => p.bestPlacementScore)) : 0,
        improvement: progress.length > 1
          ? progress[0].averagePlacementScore - progress[progress.length - 1].averagePlacementScore
          : 0
      };

      reply.send({
        success: true,
        data: {
          period,
          summary,
          dailyProgress: progress
        }
      });

    } catch (error) {
      console.error('Error fetching user progress:', error);
      reply.code(500).send({
        success: false,
        error: 'Failed to fetch user progress'
      });
    }
  });

};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function updateUserProgress(userId: string, placementScore: number) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  try {
    // Get or create today's progress tracking
    const existingProgress = await prisma.progressTracking.findUnique({
      where: {
        userId_trackingDate: {
          userId,
          trackingDate: today
        }
      }
    });

    if (existingProgress) {
      // Update existing progress
      await prisma.progressTracking.update({
        where: {
          userId_trackingDate: {
            userId,
            trackingDate: today
          }
        },
        data: {
          totalAnalyses: existingProgress.totalAnalyses + 1,
          averagePlacementScore: 
            (existingProgress.averagePlacementScore * existingProgress.totalAnalyses + placementScore) / 
            (existingProgress.totalAnalyses + 1),
          bestPlacementScore: Math.max(existingProgress.bestPlacementScore, placementScore),
          worstPlacementScore: Math.min(existingProgress.worstPlacementScore || 10, placementScore)
        }
      });
    } else {
      // Create new progress entry
      await prisma.progressTracking.create({
        data: {
          userId,
          trackingDate: today,
          weekNumber: getWeekNumber(today),
          monthNumber: today.getMonth() + 1,
          totalAnalyses: 1,
          averagePlacementScore: placementScore,
          bestPlacementScore: placementScore,
          worstPlacementScore: placementScore,
          sessionsCount: 1
        }
      });
    }
  } catch (error) {
    console.error('Error updating user progress:', error);
  }
}

async function checkPlacementAchievements(userId: string, analysis: any) {
  try {
    // Check for "First Analysis" achievement
    const firstAnalysisAchievement = await prisma.achievement.findFirst({
      where: { name: 'First Analysis' }
    });

    if (firstAnalysisAchievement) {
      const existingAchievement = await prisma.userAchievement.findUnique({
        where: {
          userId_achievementId: {
            userId,
            achievementId: firstAnalysisAchievement.id
          }
        }
      });

      if (!existingAchievement) {
        await prisma.userAchievement.create({
          data: {
            userId,
            achievementId: firstAnalysisAchievement.id,
            progress: 1.0
          }
        });
      }
    }

    // Check for "Placement Perfectionist" achievement (10/10 score)
    if (analysis.placementScore === 10) {
      const perfectAchievement = await prisma.achievement.findFirst({
        where: { name: 'Placement Perfectionist' }
      });

      if (perfectAchievement) {
        const existingAchievement = await prisma.userAchievement.findUnique({
          where: {
            userId_achievementId: {
              userId,
              achievementId: perfectAchievement.id
            }
          }
        });

        if (!existingAchievement) {
          await prisma.userAchievement.create({
            data: {
              userId,
              achievementId: perfectAchievement.id,
              progress: 1.0
            }
          });
        }
      }
    }
  } catch (error) {
    console.error('Error checking achievements:', error);
  }
}

function generatePlacementFeedback(card: string, score: number, distance: number) {
  const feedbackTemplates = {
    'hog-rider': {
      good: 'Excellent bridge placement! This maximizes Hog Rider\'s damage potential.',
      average: 'Decent placement, but consider positioning closer to the bridge for faster tower reach.',
      poor: 'Suboptimal placement - Hog Rider works best when placed at the bridge for direct tower targeting.'
    },
    'giant': {
      good: 'Perfect tank placement! This gives your support troops maximum protection.',
      average: 'Good tank positioning, but consider placing slightly behind for better support troop coverage.',
      poor: 'Giant placement could be improved - position further back to build a stronger push.'
    },
    'fireball': {
      good: 'Outstanding spell placement! Maximum value achieved.',
      average: 'Good fireball usage, but positioning could be optimized for better value.',
      poor: 'Consider waiting for better fireball value - cluster more enemy troops for maximum damage.'
    }
  };

  const cardFeedback = feedbackTemplates[card as keyof typeof feedbackTemplates] || {
    good: 'Great placement! This positioning maximizes your card\'s effectiveness.',
    average: 'Decent placement, but there\'s room for improvement in positioning.',
    poor: 'Consider alternative placement options for better strategic value.'
  };

  let message, reasoning, improvement;

  if (score >= 8) {
    message = cardFeedback.good;
    reasoning = 'This placement aligns well with optimal strategic positioning.';
    improvement = 'Keep up the excellent placement decisions!';
  } else if (score >= 6) {
    message = cardFeedback.average;
    reasoning = 'The placement is functional but could be optimized for better results.';
    improvement = `Consider adjusting position by ${Math.round(distance)} tiles for better effectiveness.`;
  } else {
    message = cardFeedback.poor;
    reasoning = 'This placement doesn\'t maximize the card\'s strategic potential.';
    improvement = `Try placing ${Math.round(distance)} tiles closer to the optimal position for much better results.`;
  }

  return { message, reasoning, improvement };
}

function getWeekNumber(date: Date): number {
  const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
  const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
  return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

export default analysisRoutes;
