import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import jwt from '@fastify/jwt';
import multipart from '@fastify/multipart';
import websocket from '@fastify/websocket';
import { config } from 'dotenv';

// Load environment variables
config();

// Import routes
import authRoutes from './routes/auth';
// import userRoutes from './routes/users';
// import gamificationRoutes from './routes/gamification';
import analysisRoutes from './routes/analysis';
import cardRoutes from './routes/cards-enhanced';
import uploadRoutes from './routes/upload-simple';
import videoAnalysisRoutes from './routes/video-analysis';

// JWT type declarations
declare module '@fastify/jwt' {
  interface FastifyJWT {
    payload: { id: string; email: string; role: string };
    user: { id: string; userId: string; email: string; role: string };
  }
}

const fastify = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: process.env.NODE_ENV === 'development' ? {
      target: 'pino-pretty',
      options: {
        colorize: true
      }
    } : undefined
  }
});

// Global plugins
fastify.register(cors, {
  origin: process.env.NODE_ENV === 'production' 
    ? [process.env.FRONTEND_URL || 'https://optiroyale.com']
    : ['http://localhost:3000', 'http://localhost:3001']
});

fastify.register(helmet, {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "wss:"]
    }
  }
});

fastify.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute'
});

fastify.register(jwt, {
  secret: process.env.JWT_SECRET || 'super-secret-key-change-in-production',
  sign: {
    expiresIn: '7d'
  }
});

fastify.register(multipart, {
  limits: {
    fieldNameSize: 100,
    fieldSize: 1000000,
    fields: 10,
    fileSize: 100000000, // 100MB
    files: 1,
    headerPairs: 2000
  }
});

fastify.register(websocket);

// Authentication middleware
fastify.decorate('authenticate', async (request: any, reply: any) => {
  try {
    await request.jwtVerify();
    // Ensure userId is available (copy from id if needed)
    if (request.user && !request.user.userId) {
      request.user.userId = request.user.id;
    }
  } catch (err) {
    reply.code(401).send({ error: 'Unauthorized' });
  }
});

// Health check
fastify.get('/health', async (request, reply) => {
  return { 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.2'
  };
});

// Register route modules
fastify.register(authRoutes, { prefix: '/api/auth' });
// fastify.register(userRoutes, { prefix: '/api/users' });
// fastify.register(gamificationRoutes, { prefix: '/api/gamification' });
fastify.register(analysisRoutes, { prefix: '/api/analysis' });
fastify.register(cardRoutes, { prefix: '/api/cards' });
fastify.register(uploadRoutes, { prefix: '/api/upload' });
// fastify.register(videoAnalysisRoutes, { prefix: '/api/video' });

// Error handler
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error);
  
  if (error.validation) {
    reply.status(400).send({
      error: 'Validation Error',
      message: error.message,
      details: error.validation
    });
    return;
  }

  if (error.statusCode) {
    reply.status(error.statusCode).send({
      error: error.message
    });
    return;
  }

  reply.status(500).send({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// Start server
const start = async () => {
  try {
    const port = Number(process.env.PORT) || 3003;
    const host = process.env.HOST || '0.0.0.0';
    
    await fastify.listen({ port, host });
    fastify.log.info(`🚀 Opti Royale API server started on ${host}:${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
