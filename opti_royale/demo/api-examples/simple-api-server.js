// Minimal API Server for Development
// Standard approach: Start simple, add complexity later

const fastify = require('fastify')({ 
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: { colorize: true }
    }
  }
});

// Mock user database (in-memory for development)
const users = [];
let userIdCounter = 1;

// Basic plugins
fastify.register(require('@fastify/cors'), {
  origin: ['http://localhost:3000', 'http://localhost:3001']
});

// Health check
fastify.get('/health', async () => {
  return { 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    users: users.length
  };
});

// User Registration - Admin Account Creation
fastify.post('/api/auth/register', async (request, reply) => {
  const { username, email, password, firstName, lastName } = request.body;
  
  // Validation
  if (!username || !email || !password) {
    return reply.status(400).send({
      error: 'Missing Required Fields',
      message: 'Username, email, and password are required'
    });
  }
  
  // Check if user exists
  const existingUser = users.find(u => u.email === email);
  if (existingUser) {
    return reply.status(400).send({
      error: 'User Exists',
      message: 'Email already registered'
    });
  }
  
  // Create user (admin privileges for first user)
  const user = {
    id: userIdCounter++,
    username,
    email,
    firstName: firstName || '',
    lastName: lastName || '',
    role: users.length === 0 ? 'admin' : 'user', // First user is admin
    createdAt: new Date().toISOString()
  };
  
  users.push(user);
  
  reply.status(201).send({
    message: `${user.role === 'admin' ? 'Admin' : 'User'} account created successfully!`,
    user: {
      id: user.id,
      username: user.username,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      role: user.role
    },
    token: `mock-jwt-token-${user.id}` // Mock token for development
  });
});

// User Login
fastify.post('/api/auth/login', async (request, reply) => {
  const { email, password } = request.body;
  
  if (!email || !password) {
    return reply.status(400).send({
      error: 'Missing Credentials',
      message: 'Email and password required'
    });
  }
  
  const user = users.find(u => u.email === email);
  if (!user) {
    return reply.status(401).send({
      error: 'Invalid Credentials',
      message: 'User not found'
    });
  }
  
  // In development, accept any password
  reply.send({
    message: 'Login successful',
    user: {
      id: user.id,
      username: user.username,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      role: user.role
    },
    token: `mock-jwt-token-${user.id}`
  });
});

// Video Upload Endpoint (Mock)
fastify.post('/api/video/upload', async (request, reply) => {
  // Simulate file upload processing
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  reply.send({
    message: 'Video uploaded successfully',
    videoId: `video_${Date.now()}`,
    status: 'processing'
  });
});

// Video Analysis Endpoint (Mock)
fastify.post('/api/video/analyze', async (request, reply) => {
  const { videoId } = request.body;
  
  // Simulate analysis
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  reply.send({
    videoId,
    analysis: {
      matches: Math.floor(Math.random() * 10) + 1,
      wins: Math.floor(Math.random() * 8) + 1,
      averageElixir: (Math.random() * 2 + 3).toFixed(1),
      recommendations: [
        'Consider using Lightning Spell against Inferno Tower',
        'Your Hog Rider timing could be improved',
        'Try baiting their Fireball before playing Minion Horde'
      ],
      confidence: (Math.random() * 0.3 + 0.7).toFixed(2)
    },
    timestamp: new Date().toISOString()
  });
});

// Start server
const start = async () => {
  try {
    await fastify.listen({ port: 3003, host: '0.0.0.0' });
    console.log('🚀 OptiRoyale Development API started on http://localhost:3003');
    console.log('💡 This is a minimal development server - perfect for getting started!');
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
