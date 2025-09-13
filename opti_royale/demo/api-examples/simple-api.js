const fastify = require('fastify')({ 
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: { colorize: true }
    }
  }
});

// Mock user database
let users = [
  {
    id: '1',
    username: 'james_admin',
    email: 'james@optiroyale.com',
    role: 'admin',
    firstName: 'James',
    lastName: 'Fleming'
  }
];

// Register CORS
fastify.register(require('@fastify/cors'), {
  origin: ['http://localhost:3000', 'http://localhost:3001']
});

// Register multipart for file uploads
fastify.register(require('@fastify/multipart'), {
  limits: {
    fileSize: 100000000 // 100MB
  }
});

// Health check
fastify.get('/health', async (request, reply) => {
  return { 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.3'
  };
});

// Register user (admin account creation)
fastify.post('/api/auth/register', async (request, reply) => {
  const { username, email, password, firstName, lastName } = request.body;
  
  if (!username || !email || !password) {
    return reply.status(400).send({ 
      error: 'Missing Required Fields',
      message: 'Username, email, and password are required'
    });
  }
  
  // Check if user exists
  const existingUser = users.find(u => u.email === email || u.username === username);
  if (existingUser) {
    return reply.status(400).send({
      error: 'User Already Exists',
      message: 'Email or username already registered'
    });
  }
  
  const newUser = {
    id: (users.length + 1).toString(),
    username,
    email,
    firstName: firstName || '',
    lastName: lastName || '',
    role: username.includes('admin') ? 'admin' : 'user',
    createdAt: new Date().toISOString()
  };
  
  users.push(newUser);
  
  reply.status(201).send({
    message: 'Account created successfully',
    user: { ...newUser, password: undefined },
    token: 'mock-jwt-token-' + newUser.id
  });
});

// Login
fastify.post('/api/auth/login', async (request, reply) => {
  const { email, password } = request.body;
  
  const user = users.find(u => u.email === email);
  if (!user) {
    return reply.status(401).send({ error: 'Invalid credentials' });
  }
  
  reply.send({
    message: 'Login successful',
    user: { ...user, password: undefined },
    token: 'mock-jwt-token-' + user.id
  });
});

// Video upload endpoint
fastify.post('/api/upload', async (request, reply) => {
  try {
    const data = await request.file();
    
    if (!data) {
      return reply.status(400).send({ error: 'No file uploaded' });
    }
    
    // Mock file processing
    const fileId = 'video_' + Date.now();
    
    reply.send({
      message: 'Video uploaded successfully',
      fileId,
      filename: data.filename,
      mimetype: data.mimetype,
      size: data.file.bytesRead || 0
    });
    
  } catch (error) {
    fastify.log.error(error);
    reply.status(500).send({ error: 'Upload failed' });
  }
});

// Video analysis endpoint
fastify.post('/api/video/analyze', async (request, reply) => {
  const { fileId } = request.body;
  
  if (!fileId) {
    return reply.status(400).send({ error: 'File ID required' });
  }
  
  // Mock analysis results
  const analysisResult = {
    id: 'analysis_' + Date.now(),
    fileId,
    status: 'completed',
    results: {
      overallScore: 78,
      arenaLevel: 12,
      cardsDetected: ['Wizard', 'Giant', 'Fireball', 'Skeleton Army'],
      recommendations: [
        'Consider using Zap instead of Arrows for better elixir efficiency',
        'Your Giant placement timing could be improved',
        'Try to wait for elixir advantage before pushing'
      ],
      frameAnalysis: {
        totalFrames: 1247,
        keyFrames: 23,
        cardsPlayed: 12,
        averageElixir: 3.8
      },
      confidence: 0.87
    },
    processingTime: '2.3s',
    createdAt: new Date().toISOString()
  };
  
  reply.send(analysisResult);
});

// Get user profile
fastify.get('/api/users/profile', async (request, reply) => {
  // Mock auth - in real app would verify JWT
  const user = users[0]; // Return first user for now
  
  reply.send({
    user: { ...user, password: undefined },
    stats: {
      videosAnalyzed: 12,
      averageScore: 76,
      improvement: '+8%',
      currentTrophies: 4200
    }
  });
});

// Start server
const start = async () => {
  try {
    const port = 3003;
    const host = '0.0.0.0';
    
    await fastify.listen({ port, host });
    fastify.log.info(`🚀 Simple OptiRoyale API server started on ${host}:${port}`);
    console.log(`✅ API endpoints available:
    - POST /api/auth/register (Create account)
    - POST /api/auth/login (Login)
    - POST /api/upload (Upload video)
    - POST /api/video/analyze (Analyze video)
    - GET /api/users/profile (Get profile)
    - GET /health (Health check)`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
