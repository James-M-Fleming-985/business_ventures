import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';

const leaderboardQuerySchema = z.object({
  timeframe: z.enum(['daily', 'weekly', 'monthly', 'allTime']).default('weekly'),
  category: z.enum(['overall', 'accuracy', 'consistency', 'improvement']).default('overall'),
  limit: z.coerce.number().min(1).max(1000).default(100),
  offset: z.coerce.number().min(0).default(0)
});

const gamificationRoutes: FastifyPluginAsync = async (fastify) => {
  // Get leaderboard
  fastify.get('/leaderboard', {
    schema: {
      querystring: leaderboardQuerySchema,
      response: {
        200: z.object({
          leaderboard: z.array(z.object({
            id: z.string(),
            username: z.string(),
            avatar: z.string().optional(),
            rating: z.number(),
            rank: z.number(),
            accuracy: z.number(),
            totalAnalyses: z.number(),
            winRate: z.number(),
            trophies: z.number(),
            currentStreak: z.number(),
            rankChange: z.number(),
            level: z.number(),
            xp: z.number()
          })),
          userRank: z.object({
            id: z.string(),
            username: z.string(),
            rating: z.number(),
            rank: z.number(),
            rankChange: z.number()
          }).optional(),
          total: z.number()
        })
      }
    }
  }, async (request, reply) => {
    const { timeframe, category, limit, offset } = request.query;
    const userId = request.user?.id;

    try {
      // Build base query based on category
      let orderByClause = 'rating DESC';
      let timeFilter = '';

      // Apply timeframe filter
      switch (timeframe) {
        case 'daily':
          timeFilter = "AND ur.updated_at >= NOW() - INTERVAL '1 day'";
          break;
        case 'weekly':
          timeFilter = "AND ur.updated_at >= NOW() - INTERVAL '1 week'";
          break;
        case 'monthly':
          timeFilter = "AND ur.updated_at >= NOW() - INTERVAL '1 month'";
          break;
        default:
          timeFilter = '';
      }

      // Apply category-specific ordering
      switch (category) {
        case 'accuracy':
          orderByClause = 'ur.average_accuracy DESC, ur.total_analyses DESC';
          break;
        case 'consistency':
          orderByClause = 'ur.current_streak DESC, ur.total_analyses DESC';
          break;
        case 'improvement':
          orderByClause = '(ur.rating - ur.initial_rating) DESC';
          break;
        default:
          orderByClause = 'ur.rating DESC';
      }

      // Get leaderboard data
      const leaderboardQuery = `
        WITH ranked_users AS (
          SELECT 
            u.id,
            u.username,
            u.avatar,
            ur.rating,
            ur.average_accuracy,
            ur.total_analyses,
            ur.win_rate,
            ur.trophies,
            ur.current_streak,
            ur.level,
            ur.xp,
            ur.rank_change_weekly,
            ROW_NUMBER() OVER (ORDER BY ${orderByClause}) as rank
          FROM users u
          JOIN user_rankings ur ON u.id = ur.user_id
          WHERE ur.rating > 0 ${timeFilter}
          ORDER BY ${orderByClause}
          LIMIT $1 OFFSET $2
        )
        SELECT * FROM ranked_users;
      `;

      const leaderboard = await fastify.pg.query(leaderboardQuery, [limit, offset]);

      // Get user's current rank if authenticated
      let userRank = null;
      if (userId) {
        const userRankQuery = `
          WITH user_position AS (
            SELECT 
              u.id,
              u.username,
              ur.rating,
              ur.rank_change_weekly,
              ROW_NUMBER() OVER (ORDER BY ${orderByClause}) as rank
            FROM users u
            JOIN user_rankings ur ON u.id = ur.user_id
            WHERE ur.rating > 0 ${timeFilter}
          )
          SELECT * FROM user_position WHERE id = $1;
        `;
        
        const userRankResult = await fastify.pg.query(userRankQuery, [userId]);
        if (userRankResult.rows.length > 0) {
          userRank = {
            id: userRankResult.rows[0].id,
            username: userRankResult.rows[0].username,
            rating: userRankResult.rows[0].rating,
            rank: userRankResult.rows[0].rank,
            rankChange: userRankResult.rows[0].rank_change_weekly
          };
        }
      }

      // Get total count
      const countQuery = `
        SELECT COUNT(*) as total
        FROM user_rankings ur
        WHERE ur.rating > 0 ${timeFilter};
      `;
      const totalResult = await fastify.pg.query(countQuery);

      reply.send({
        leaderboard: leaderboard.rows.map(row => ({
          id: row.id,
          username: row.username,
          avatar: row.avatar,
          rating: row.rating,
          rank: parseInt(row.rank),
          accuracy: parseFloat(row.average_accuracy),
          totalAnalyses: parseInt(row.total_analyses),
          winRate: parseFloat(row.win_rate),
          trophies: parseInt(row.trophies),
          currentStreak: parseInt(row.current_streak),
          rankChange: parseInt(row.rank_change_weekly),
          level: parseInt(row.level),
          xp: parseInt(row.xp)
        })),
        userRank,
        total: parseInt(totalResult.rows[0].total)
      });

    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({ error: 'Failed to fetch leaderboard' });
    }
  });

  // Get user achievements
  fastify.get('/achievements', {
    preHandler: [fastify.authenticate],
    schema: {
      response: {
        200: z.object({
          achievements: z.array(z.object({
            id: z.string(),
            name: z.string(),
            description: z.string(),
            category: z.enum(['accuracy', 'consistency', 'social', 'special', 'milestone']),
            icon: z.string(),
            rarity: z.enum(['common', 'rare', 'epic', 'legendary']),
            xpReward: z.number(),
            progress: z.number(),
            maxProgress: z.number(),
            isUnlocked: z.boolean(),
            unlockedAt: z.string().optional(),
            requirements: z.array(z.string())
          })),
          summary: z.object({
            total: z.number(),
            unlocked: z.number(),
            totalXP: z.number()
          })
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;

    try {
      const achievementsQuery = `
        SELECT 
          a.id,
          a.name,
          a.description,
          a.category,
          a.icon,
          a.rarity,
          a.xp_reward,
          a.requirements,
          COALESCE(ua.progress, 0) as progress,
          a.max_progress,
          ua.unlocked_at IS NOT NULL as is_unlocked,
          ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = $1
        ORDER BY 
          CASE WHEN ua.unlocked_at IS NOT NULL THEN 0 ELSE 1 END,
          a.rarity DESC,
          a.name;
      `;

      const result = await fastify.pg.query(achievementsQuery, [userId]);

      const achievements = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        description: row.description,
        category: row.category,
        icon: row.icon,
        rarity: row.rarity,
        xpReward: parseInt(row.xp_reward),
        progress: parseInt(row.progress),
        maxProgress: parseInt(row.max_progress),
        isUnlocked: row.is_unlocked,
        unlockedAt: row.unlocked_at?.toISOString(),
        requirements: Array.isArray(row.requirements) ? row.requirements : []
      }));

      const summary = {
        total: achievements.length,
        unlocked: achievements.filter(a => a.isUnlocked).length,
        totalXP: achievements.filter(a => a.isUnlocked).reduce((sum, a) => sum + a.xpReward, 0)
      };

      reply.send({ achievements, summary });

    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({ error: 'Failed to fetch achievements' });
    }
  });

  // Check and award achievements
  fastify.post('/achievements/check', {
    preHandler: [fastify.authenticate],
    schema: {
      body: z.object({
        analysisResult: z.object({
          accuracy: z.number(),
          placementScore: z.number(),
          gameResult: z.enum(['win', 'loss']),
          cardsUsed: z.array(z.string())
        })
      }),
      response: {
        200: z.object({
          newAchievements: z.array(z.object({
            id: z.string(),
            name: z.string(),
            xpReward: z.number()
          })),
          progressUpdates: z.array(z.object({
            id: z.string(),
            name: z.string(),
            progress: z.number(),
            maxProgress: z.number()
          }))
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;
    const { analysisResult } = request.body;

    try {
      // Get user's current stats
      const userStatsQuery = `
        SELECT 
          ur.total_analyses,
          ur.average_accuracy,
          ur.current_streak,
          ur.longest_streak,
          ur.win_rate,
          ur.level
        FROM user_rankings ur
        WHERE ur.user_id = $1;
      `;
      
      const userStats = await fastify.pg.query(userStatsQuery, [userId]);
      if (userStats.rows.length === 0) {
        reply.status(404).send({ error: 'User stats not found' });
        return;
      }

      const stats = userStats.rows[0];
      const newAchievements: any[] = [];
      const progressUpdates: any[] = [];

      // Check achievements
      const achievementChecks = [
        // First Analysis
        {
          condition: stats.total_analyses === 1,
          achievementId: 'first_analysis'
        },
        // Accuracy achievements
        {
          condition: analysisResult.accuracy >= 95,
          achievementId: 'perfectionist'
        },
        // Streak achievements
        {
          condition: stats.current_streak >= 5,
          achievementId: 'streak_master'
        },
        // Analysis count milestones
        {
          condition: stats.total_analyses >= 100,
          achievementId: 'centurion'
        },
        {
          condition: stats.total_analyses >= 1000,
          achievementId: 'grand_master'
        }
      ];

      // Process each achievement check
      for (const check of achievementChecks) {
        if (check.condition) {
          // Check if achievement already unlocked
          const existingQuery = `
            SELECT id FROM user_achievements 
            WHERE user_id = $1 AND achievement_id = $2;
          `;
          const existing = await fastify.pg.query(existingQuery, [userId, check.achievementId]);
          
          if (existing.rows.length === 0) {
            // Award achievement
            const achievementQuery = `
              SELECT id, name, xp_reward
              FROM achievements
              WHERE id = $1;
            `;
            const achievement = await fastify.pg.query(achievementQuery, [check.achievementId]);
            
            if (achievement.rows.length > 0) {
              // Insert user achievement
              await fastify.pg.query(`
                INSERT INTO user_achievements (user_id, achievement_id, progress, unlocked_at)
                VALUES ($1, $2, 1, NOW());
              `, [userId, check.achievementId]);

              newAchievements.push({
                id: achievement.rows[0].id,
                name: achievement.rows[0].name,
                xpReward: parseInt(achievement.rows[0].xp_reward)
              });

              // Award XP
              await fastify.pg.query(`
                UPDATE user_rankings 
                SET xp = xp + $1
                WHERE user_id = $2;
              `, [achievement.rows[0].xp_reward, userId]);
            }
          }
        }
      }

      // Update progressive achievements
      const progressiveAchievements = [
        {
          id: 'analysis_addict',
          progress: stats.total_analyses,
          maxProgress: 500
        },
        {
          id: 'accuracy_expert',
          progress: Math.floor(stats.average_accuracy),
          maxProgress: 90
        }
      ];

      for (const prog of progressiveAchievements) {
        await fastify.pg.query(`
          INSERT INTO user_achievements (user_id, achievement_id, progress)
          VALUES ($1, $2, $3)
          ON CONFLICT (user_id, achievement_id)
          DO UPDATE SET progress = GREATEST(user_achievements.progress, $3);
        `, [userId, prog.id, prog.progress]);

        progressUpdates.push(prog);
      }

      reply.send({ newAchievements, progressUpdates });

    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({ error: 'Failed to check achievements' });
    }
  });

  // Update user rating after analysis
  fastify.post('/rating/update', {
    preHandler: [fastify.authenticate],
    schema: {
      body: z.object({
        analysisResult: z.object({
          accuracy: z.number(),
          placementScore: z.number(),
          gameResult: z.enum(['win', 'loss']),
          optimalPlacement: z.boolean()
        })
      }),
      response: {
        200: z.object({
          newRating: z.number(),
          ratingChange: z.number(),
          newRank: z.number(),
          xpGained: z.number()
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;
    const { analysisResult } = request.body;

    try {
      // Calculate rating change using ELO-like system
      const baseRatingChange = 32; // K-factor
      const accuracyMultiplier = analysisResult.accuracy / 100;
      const placementMultiplier = analysisResult.placementScore / 100;
      const resultMultiplier = analysisResult.gameResult === 'win' ? 1 : 0.5;
      const optimalBonus = analysisResult.optimalPlacement ? 1.2 : 1;

      const ratingChange = Math.round(
        baseRatingChange * 
        accuracyMultiplier * 
        placementMultiplier * 
        resultMultiplier * 
        optimalBonus
      );

      // Calculate XP gain
      const baseXP = 25;
      const xpGained = Math.round(baseXP * accuracyMultiplier * optimalBonus);

      // Update user rankings
      const updateQuery = `
        UPDATE user_rankings 
        SET 
          rating = rating + $1,
          total_analyses = total_analyses + 1,
          average_accuracy = (average_accuracy * total_analyses + $2) / (total_analyses + 1),
          current_streak = CASE 
            WHEN $3 = 'win' AND $4 = true THEN current_streak + 1 
            ELSE 0 
          END,
          longest_streak = GREATEST(longest_streak, CASE 
            WHEN $3 = 'win' AND $4 = true THEN current_streak + 1 
            ELSE 0 
          END),
          win_rate = (win_rate * total_analyses + CASE WHEN $3 = 'win' THEN 100 ELSE 0 END) / (total_analyses + 1),
          xp = xp + $5,
          level = FLOOR((xp + $5) / 1000) + 1,
          updated_at = NOW()
        WHERE user_id = $6
        RETURNING rating, level;
      `;

      const result = await fastify.pg.query(updateQuery, [
        ratingChange,
        analysisResult.accuracy,
        analysisResult.gameResult,
        analysisResult.optimalPlacement,
        xpGained,
        userId
      ]);

      // Recalculate ranks (this could be optimized with a background job)
      await fastify.pg.query(`
        WITH ranked_users AS (
          SELECT 
            user_id,
            ROW_NUMBER() OVER (ORDER BY rating DESC) as new_rank
          FROM user_rankings
          WHERE rating > 0
        )
        UPDATE user_rankings ur
        SET current_rank = ru.new_rank
        FROM ranked_users ru
        WHERE ur.user_id = ru.user_id;
      `);

      // Get updated rank
      const rankQuery = `
        SELECT current_rank FROM user_rankings WHERE user_id = $1;
      `;
      const rankResult = await fastify.pg.query(rankQuery, [userId]);

      reply.send({
        newRating: parseInt(result.rows[0].rating),
        ratingChange,
        newRank: parseInt(rankResult.rows[0].current_rank),
        xpGained
      });

    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({ error: 'Failed to update rating' });
    }
  });

  // Get user profile
  fastify.get('/profile', {
    preHandler: [fastify.authenticate],
    schema: {
      response: {
        200: z.object({
          profile: z.object({
            id: z.string(),
            username: z.string(),
            email: z.string(),
            avatar: z.string().optional(),
            level: z.number(),
            xp: z.number(),
            xpToNextLevel: z.number(),
            rating: z.number(),
            rank: z.number(),
            tier: z.string(),
            trophies: z.number(),
            totalAnalyses: z.number(),
            averageAccuracy: z.number(),
            winRate: z.number(),
            currentStreak: z.number(),
            longestStreak: z.number(),
            joinedAt: z.string(),
            lastActive: z.string(),
            achievements: z.object({
              total: z.number(),
              unlocked: z.number(),
              recent: z.array(z.object({
                id: z.string(),
                name: z.string(),
                icon: z.string(),
                unlockedAt: z.string()
              }))
            }),
            statistics: z.object({
              totalPlaytime: z.number(),
              favoriteCard: z.string(),
              mostImprovedCard: z.string(),
              weeklyProgress: z.array(z.object({
                week: z.string(),
                analyses: z.number(),
                accuracy: z.number()
              }))
            })
          })
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;

    try {
      // Get user profile data
      const profileQuery = `
        SELECT 
          u.id,
          u.username,
          u.email,
          u.avatar,
          u.created_at,
          u.last_active,
          ur.level,
          ur.xp,
          ur.rating,
          ur.current_rank,
          ur.trophies,
          ur.total_analyses,
          ur.average_accuracy,
          ur.win_rate,
          ur.current_streak,
          ur.longest_streak
        FROM users u
        LEFT JOIN user_rankings ur ON u.id = ur.user_id
        WHERE u.id = $1;
      `;

      const profileResult = await fastify.pg.query(profileQuery, [userId]);
      if (profileResult.rows.length === 0) {
        reply.status(404).send({ error: 'Profile not found' });
        return;
      }

      const profile = profileResult.rows[0];

      // Get tier based on rating
      const getTier = (rating: number) => {
        if (rating >= 2500) return 'Legendary';
        if (rating >= 2000) return 'Master';
        if (rating >= 1500) return 'Champion';
        if (rating >= 1000) return 'Expert';
        return 'Beginner';
      };

      // Get recent achievements
      const recentAchievementsQuery = `
        SELECT a.id, a.name, a.icon, ua.unlocked_at
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.id
        WHERE ua.user_id = $1 AND ua.unlocked_at IS NOT NULL
        ORDER BY ua.unlocked_at DESC
        LIMIT 5;
      `;
      const recentAchievements = await fastify.pg.query(recentAchievementsQuery, [userId]);

      // Get achievement counts
      const achievementCountQuery = `
        SELECT 
          COUNT(*) as total_achievements,
          COUNT(ua.unlocked_at) as unlocked_achievements
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = $1;
      `;
      const achievementCounts = await fastify.pg.query(achievementCountQuery, [userId]);

      // Get weekly progress (simplified)
      const weeklyProgressQuery = `
        SELECT 
          DATE_TRUNC('week', created_at) as week,
          COUNT(*) as analyses,
          AVG(accuracy_score) as accuracy
        FROM analysis_history
        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '8 weeks'
        GROUP BY DATE_TRUNC('week', created_at)
        ORDER BY week DESC;
      `;
      const weeklyProgress = await fastify.pg.query(weeklyProgressQuery, [userId]);

      reply.send({
        profile: {
          id: profile.id,
          username: profile.username,
          email: profile.email,
          avatar: profile.avatar,
          level: parseInt(profile.level) || 1,
          xp: parseInt(profile.xp) || 0,
          xpToNextLevel: 1000 - (parseInt(profile.xp) || 0) % 1000,
          rating: parseInt(profile.rating) || 1000,
          rank: parseInt(profile.current_rank) || 0,
          tier: getTier(parseInt(profile.rating) || 1000),
          trophies: parseInt(profile.trophies) || 0,
          totalAnalyses: parseInt(profile.total_analyses) || 0,
          averageAccuracy: parseFloat(profile.average_accuracy) || 0,
          winRate: parseFloat(profile.win_rate) || 0,
          currentStreak: parseInt(profile.current_streak) || 0,
          longestStreak: parseInt(profile.longest_streak) || 0,
          joinedAt: profile.created_at.toISOString(),
          lastActive: profile.last_active?.toISOString() || new Date().toISOString(),
          achievements: {
            total: parseInt(achievementCounts.rows[0].total_achievements),
            unlocked: parseInt(achievementCounts.rows[0].unlocked_achievements),
            recent: recentAchievements.rows.map(row => ({
              id: row.id,
              name: row.name,
              icon: row.icon,
              unlockedAt: row.unlocked_at.toISOString()
            }))
          },
          statistics: {
            totalPlaytime: 0, // TODO: implement playtime tracking
            favoriteCard: 'Hog Rider', // TODO: calculate from analysis history
            mostImprovedCard: 'Fireball', // TODO: calculate improvement metrics
            weeklyProgress: weeklyProgress.rows.map(row => ({
              week: row.week.toISOString().split('T')[0],
              analyses: parseInt(row.analyses),
              accuracy: parseFloat(row.accuracy) || 0
            }))
          }
        }
      });

    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({ error: 'Failed to fetch profile' });
    }
  });
};

export default gamificationRoutes;
