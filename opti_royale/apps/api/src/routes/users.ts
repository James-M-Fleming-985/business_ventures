import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';

// Validation schemas
const updateProfileSchema = z.object({
  firstName: z.string().min(1).max(50).optional(),
  lastName: z.string().min(1).max(50).optional(),
  bio: z.string().max(500).optional(),
  avatar: z.string().url().optional(),
  preferences: z.object({
    notifications: z.object({
      email: z.boolean().optional(),
      push: z.boolean().optional(),
      achievements: z.boolean().optional(),
      leaderboard: z.boolean().optional()
    }).optional(),
    privacy: z.object({
      profileVisible: z.boolean().optional(),
      statsVisible: z.boolean().optional(),
      achievementsVisible: z.boolean().optional()
    }).optional()
  }).optional()
});

const getUsersQuerySchema = z.object({
  search: z.string().optional(),
  limit: z.coerce.number().min(1).max(100).default(20),
  offset: z.coerce.number().min(0).default(0),
  sortBy: z.enum(['username', 'rating', 'level', 'createdAt']).default('rating'),
  sortOrder: z.enum(['asc', 'desc']).default('desc')
});

// Mock user data - will be replaced with Prisma
let users: any[] = [
  {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    bio: 'Clash Royale enthusiast looking to improve my gameplay!',
    avatar: 'https://example.com/avatar1.jpg',
    isEmailVerified: true,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date(),
    profile: {
      level: 15,
      xp: 2450,
      rating: 1850,
      totalAnalyses: 47,
      winRate: 0.68,
      currentStreak: 5,
      longestStreak: 12,
      preferences: {
        notifications: {
          email: true,
          push: true,
          achievements: true,
          leaderboard: false
        },
        privacy: {
          profileVisible: true,
          statsVisible: true,
          achievementsVisible: true
        }
      }
    }
  },
  {
    id: '2',
    username: 'progamer123',
    email: 'pro@example.com',
    firstName: 'Pro',
    lastName: 'Gamer',
    bio: 'Top 1000 Clash Royale player. Always looking for new strategies!',
    avatar: 'https://example.com/avatar2.jpg',
    isEmailVerified: true,
    createdAt: new Date('2023-12-15'),
    updatedAt: new Date(),
    profile: {
      level: 28,
      xp: 5680,
      rating: 2450,
      totalAnalyses: 156,
      winRate: 0.82,
      currentStreak: 15,
      longestStreak: 24,
      preferences: {
        notifications: {
          email: false,
          push: true,
          achievements: true,
          leaderboard: true
        },
        privacy: {
          profileVisible: true,
          statsVisible: true,
          achievementsVisible: true
        }
      }
    }
  }
];

const userRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all users (with pagination and search)
  fastify.get('/', {
    schema: {
      querystring: getUsersQuerySchema,
      response: {
        200: z.object({
          users: z.array(z.object({
            id: z.string(),
            username: z.string(),
            firstName: z.string().optional(),
            lastName: z.string().optional(),
            bio: z.string().optional(),
            avatar: z.string().optional(),
            level: z.number(),
            rating: z.number(),
            totalAnalyses: z.number(),
            winRate: z.number(),
            createdAt: z.string()
          })),
          total: z.number(),
          hasMore: z.boolean()
        })
      }
    }
  }, async (request, reply) => {
    const { search, limit, offset, sortBy, sortOrder } = request.query;

    try {
      let filteredUsers = users;

      // Apply search filter
      if (search) {
        filteredUsers = users.filter(user => 
          user.username.toLowerCase().includes(search.toLowerCase()) ||
          (user.firstName && user.firstName.toLowerCase().includes(search.toLowerCase())) ||
          (user.lastName && user.lastName.toLowerCase().includes(search.toLowerCase()))
        );
      }

      // Apply sorting
      filteredUsers.sort((a, b) => {
        let aValue, bValue;
        
        switch (sortBy) {
          case 'username':
            aValue = a.username;
            bValue = b.username;
            break;
          case 'rating':
            aValue = a.profile?.rating || 0;
            bValue = b.profile?.rating || 0;
            break;
          case 'level':
            aValue = a.profile?.level || 0;
            bValue = b.profile?.level || 0;
            break;
          case 'createdAt':
            aValue = new Date(a.createdAt).getTime();
            bValue = new Date(b.createdAt).getTime();
            break;
          default:
            aValue = a.profile?.rating || 0;
            bValue = b.profile?.rating || 0;
        }

        if (sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });

      // Apply pagination
      const total = filteredUsers.length;
      const paginatedUsers = filteredUsers.slice(offset, offset + limit);

      // Format response
      const formattedUsers = paginatedUsers.map(user => ({
        id: user.id,
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        bio: user.bio,
        avatar: user.avatar,
        level: user.profile?.level || 1,
        rating: user.profile?.rating || 1000,
        totalAnalyses: user.profile?.totalAnalyses || 0,
        winRate: user.profile?.winRate || 0,
        createdAt: user.createdAt.toISOString()
      }));

      reply.send({
        users: formattedUsers,
        total,
        hasMore: offset + limit < total
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Users Fetch Failed',
        message: 'An error occurred while fetching users'
      });
    }
  });

  // Get user by ID
  fastify.get('/:id', {
    schema: {
      params: z.object({
        id: z.string()
      }),
      response: {
        200: z.object({
          user: z.object({
            id: z.string(),
            username: z.string(),
            firstName: z.string().optional(),
            lastName: z.string().optional(),
            bio: z.string().optional(),
            avatar: z.string().optional(),
            isEmailVerified: z.boolean(),
            createdAt: z.string(),
            profile: z.object({
              level: z.number(),
              xp: z.number(),
              rating: z.number(),
              totalAnalyses: z.number(),
              winRate: z.number(),
              currentStreak: z.number(),
              longestStreak: z.number()
            })
          })
        }),
        404: z.object({
          error: z.string(),
          message: z.string()
        })
      }
    }
  }, async (request, reply) => {
    const { id } = request.params;

    try {
      const user = users.find(u => u.id === id);

      if (!user) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User with the specified ID does not exist'
        });
      }

      // Check privacy settings if viewing another user's profile
      const requestingUser = request.user;
      const isOwnProfile = requestingUser && requestingUser.id === id;
      
      if (!isOwnProfile && user.profile?.preferences?.privacy?.profileVisible === false) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User with the specified ID does not exist'
        });
      }

      reply.send({
        user: {
          id: user.id,
          username: user.username,
          firstName: user.firstName,
          lastName: user.lastName,
          bio: user.bio,
          avatar: user.avatar,
          isEmailVerified: user.isEmailVerified,
          createdAt: user.createdAt.toISOString(),
          profile: {
            level: user.profile?.level || 1,
            xp: user.profile?.xp || 0,
            rating: user.profile?.rating || 1000,
            totalAnalyses: user.profile?.totalAnalyses || 0,
            winRate: user.profile?.winRate || 0,
            currentStreak: user.profile?.currentStreak || 0,
            longestStreak: user.profile?.longestStreak || 0
          }
        }
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'User Fetch Failed',
        message: 'An error occurred while fetching user'
      });
    }
  });

  // Update user profile
  fastify.put('/profile', {
    preHandler: fastify.authenticate,
    schema: {
      body: updateProfileSchema,
      response: {
        200: z.object({
          message: z.string(),
          user: z.object({
            id: z.string(),
            username: z.string(),
            firstName: z.string().optional(),
            lastName: z.string().optional(),
            bio: z.string().optional(),
            avatar: z.string().optional(),
            updatedAt: z.string()
          })
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;
    const updates = request.body;

    try {
      const userIndex = users.findIndex(u => u.id === userId);
      if (userIndex === -1) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User not found'
        });
      }

      const user = users[userIndex];

      // Update user fields
      if (updates.firstName !== undefined) user.firstName = updates.firstName;
      if (updates.lastName !== undefined) user.lastName = updates.lastName;
      if (updates.bio !== undefined) user.bio = updates.bio;
      if (updates.avatar !== undefined) user.avatar = updates.avatar;
      
      // Update preferences
      if (updates.preferences) {
        if (!user.profile) user.profile = {};
        if (!user.profile.preferences) user.profile.preferences = {};
        
        if (updates.preferences.notifications) {
          user.profile.preferences.notifications = {
            ...user.profile.preferences.notifications,
            ...updates.preferences.notifications
          };
        }
        
        if (updates.preferences.privacy) {
          user.profile.preferences.privacy = {
            ...user.profile.preferences.privacy,
            ...updates.preferences.privacy
          };
        }
      }

      user.updatedAt = new Date();

      reply.send({
        message: 'Profile updated successfully',
        user: {
          id: user.id,
          username: user.username,
          firstName: user.firstName,
          lastName: user.lastName,
          bio: user.bio,
          avatar: user.avatar,
          updatedAt: user.updatedAt.toISOString()
        }
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Profile Update Failed',
        message: 'An error occurred while updating profile'
      });
    }
  });

  // Get user statistics
  fastify.get('/:id/stats', {
    schema: {
      params: z.object({
        id: z.string()
      }),
      response: {
        200: z.object({
          stats: z.object({
            level: z.number(),
            xp: z.number(),
            rating: z.number(),
            rank: z.number().optional(),
            totalAnalyses: z.number(),
            winRate: z.number(),
            currentStreak: z.number(),
            longestStreak: z.number(),
            avgAccuracy: z.number(),
            totalPlayTime: z.number(),
            favoriteCards: z.array(z.string()),
            recentActivity: z.array(z.object({
              type: z.string(),
              description: z.string(),
              timestamp: z.string()
            }))
          })
        }),
        404: z.object({
          error: z.string(),
          message: z.string()
        })
      }
    }
  }, async (request, reply) => {
    const { id } = request.params;

    try {
      const user = users.find(u => u.id === id);

      if (!user) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User with the specified ID does not exist'
        });
      }

      // Check if stats are visible
      const requestingUser = request.user;
      const isOwnProfile = requestingUser && requestingUser.id === id;
      
      if (!isOwnProfile && user.profile?.preferences?.privacy?.statsVisible === false) {
        return reply.status(403).send({
          error: 'Stats Private',
          message: 'This user\'s statistics are private'
        });
      }

      // Calculate rank (simplified)
      const userRating = user.profile?.rating || 1000;
      const higherRatedUsers = users.filter(u => (u.profile?.rating || 1000) > userRating);
      const rank = higherRatedUsers.length + 1;

      // Mock recent activity
      const recentActivity = [
        {
          type: 'analysis',
          description: 'Completed video analysis',
          timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30 minutes ago
        },
        {
          type: 'achievement',
          description: 'Unlocked "Analysis Expert" achievement',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString() // 2 hours ago
        },
        {
          type: 'streak',
          description: 'Extended win streak to 5 games',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString() // 6 hours ago
        }
      ];

      reply.send({
        stats: {
          level: user.profile?.level || 1,
          xp: user.profile?.xp || 0,
          rating: user.profile?.rating || 1000,
          rank,
          totalAnalyses: user.profile?.totalAnalyses || 0,
          winRate: user.profile?.winRate || 0,
          currentStreak: user.profile?.currentStreak || 0,
          longestStreak: user.profile?.longestStreak || 0,
          avgAccuracy: 0.76, // Mock data
          totalPlayTime: 145, // Hours, mock data
          favoriteCards: ['Lightning', 'Hog Rider', 'Wizard'], // Mock data
          recentActivity
        }
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Stats Fetch Failed',
        message: 'An error occurred while fetching user statistics'
      });
    }
  });

  // Delete user account
  fastify.delete('/account', {
    preHandler: fastify.authenticate,
    schema: {
      response: {
        200: z.object({
          message: z.string()
        })
      }
    }
  }, async (request, reply) => {
    const userId = request.user.id;

    try {
      const userIndex = users.findIndex(u => u.id === userId);
      if (userIndex === -1) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User not found'
        });
      }

      // In production, you would:
      // 1. Soft delete or archive user data
      // 2. Anonymize analysis data
      // 3. Remove from leaderboards
      // 4. Cancel subscriptions
      
      users.splice(userIndex, 1);

      reply.send({
        message: 'Account deleted successfully'
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Account Deletion Failed',
        message: 'An error occurred while deleting account'
      });
    }
  });
};

export default userRoutes;
