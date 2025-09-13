import { FastifyPluginAsync } from 'fastify';
import bcrypt from 'bcryptjs';

interface RegisterBody {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

interface LoginBody {
  email: string;
  password: string;
}

interface ChangePasswordBody {
  currentPassword: string;
  newPassword: string;
}

interface RefreshTokenBody {
  refreshToken: string;
}

interface ResetPasswordBody {
  email: string;
}

// Mock database for now - will be replaced with Prisma
let users: any[] = [
  {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    password: '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', // password
    firstName: 'Test',
    lastName: 'User',
    isEmailVerified: true,
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

const authRoutes: FastifyPluginAsync = async (fastify) => {
  // Register new user
  fastify.post('/register', async (request, reply) => {
    const { username, email, password, firstName, lastName } = request.body as RegisterBody;

    try {
      // Basic validation
      if (!username || !email || !password) {
        return reply.status(400).send({
          error: 'Missing Required Fields',
          message: 'Username, email, and password are required'
        });
      }

      if (username.length < 3 || password.length < 8) {
        return reply.status(400).send({
          error: 'Validation Error',
          message: 'Username must be at least 3 characters, password at least 8 characters'
        });
      }

      // Check if user already exists
      const existingUser = users.find(u => u.email === email || u.username === username);
      if (existingUser) {
        return reply.status(400).send({
          error: 'User Already Exists',
          message: existingUser.email === email ? 'Email already registered' : 'Username already taken'
        });
      }

      // Hash password
      const saltRounds = 12;
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // Create new user
      const newUser = {
        id: (users.length + 1).toString(),
        username,
        email,
        password: hashedPassword,
        firstName,
        lastName,
        isEmailVerified: false,
        createdAt: new Date(),
        updatedAt: new Date()
      };

      users.push(newUser);

      // Generate JWT token
      const token = fastify.jwt.sign(
        { id: newUser.id, email: newUser.email, role: 'user' },
        { expiresIn: '7d' }
      );

      reply.status(201).send({
        message: 'User registered successfully',
        user: {
          id: newUser.id,
          username: newUser.username,
          email: newUser.email,
          firstName: newUser.firstName,
          lastName: newUser.lastName
        },
        token
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Registration Failed',
        message: 'An error occurred during registration'
      });
    }
  });

  // Login user
  fastify.post('/login', async (request, reply) => {
    const { email, password } = request.body as LoginBody;

    try {
      // Basic validation
      if (!email || !password) {
        return reply.status(400).send({
          error: 'Missing Credentials',
          message: 'Email and password are required'
        });
      }

      // Find user by email
      const user = users.find(u => u.email === email);
      if (!user) {
        return reply.status(401).send({
          error: 'Invalid Credentials',
          message: 'Email or password is incorrect'
        });
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password);
      if (!isValidPassword) {
        return reply.status(401).send({
          error: 'Invalid Credentials',
          message: 'Email or password is incorrect'
        });
      }

      // Generate JWT token
      const token = fastify.jwt.sign(
        { id: user.id, email: user.email, role: 'user' },
        { expiresIn: '7d' }
      );

      reply.send({
        message: 'Login successful',
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName
        },
        token
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Login Failed',
        message: 'An error occurred during login'
      });
    }
  });

  // Get current user profile
  fastify.get('/me', {
    preHandler: [(fastify as any).authenticate]
  }, async (request: any, reply) => {
    try {
      const userId = request.user.id;
      const user = users.find(u => u.id === userId);

      if (!user) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User profile not found'
        });
      }

      reply.send({
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          isEmailVerified: user.isEmailVerified,
          createdAt: user.createdAt.toISOString(),
          updatedAt: user.updatedAt.toISOString()
        }
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Profile Fetch Failed',
        message: 'An error occurred while fetching profile'
      });
    }
  });

  // Change password
  fastify.put('/change-password', {
    preHandler: [(fastify as any).authenticate]
  }, async (request: any, reply) => {
    const { currentPassword, newPassword } = request.body as ChangePasswordBody;
    const userId = request.user.id;

    try {
      if (!currentPassword || !newPassword) {
        return reply.status(400).send({
          error: 'Missing Fields',
          message: 'Current password and new password are required'
        });
      }

      if (newPassword.length < 8) {
        return reply.status(400).send({
          error: 'Invalid Password',
          message: 'New password must be at least 8 characters'
        });
      }

      const user = users.find(u => u.id === userId);
      if (!user) {
        return reply.status(404).send({
          error: 'User Not Found',
          message: 'User not found'
        });
      }

      // Verify current password
      const isValidPassword = await bcrypt.compare(currentPassword, user.password);
      if (!isValidPassword) {
        return reply.status(400).send({
          error: 'Invalid Password',
          message: 'Current password is incorrect'
        });
      }

      // Hash new password
      const saltRounds = 12;
      const hashedNewPassword = await bcrypt.hash(newPassword, saltRounds);

      // Update password
      user.password = hashedNewPassword;
      user.updatedAt = new Date();

      reply.send({
        message: 'Password changed successfully'
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        error: 'Password Change Failed',
        message: 'An error occurred while changing password'
      });
    }
  });

  // Logout (token invalidation would be handled client-side or with Redis blacklist)
  fastify.post('/logout', {
    preHandler: [(fastify as any).authenticate]
  }, async (request, reply) => {
    // In a production environment, you would:
    // 1. Add the token to a blacklist in Redis
    // 2. Set an expiration time equal to the token's remaining life
    
    reply.send({
      message: 'Logged out successfully'
    });
  });

  // Health check for auth routes
  fastify.get('/health', async (request, reply) => {
    reply.send({
      status: 'healthy',
      service: 'auth',
      timestamp: new Date().toISOString()
    });
  });
};

export default authRoutes;
