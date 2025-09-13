const Fastify = require('fastify');

const fastify = Fastify({
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true
      }
    }
  }
});

// Basic health check route
fastify.get('/health', async (request, reply) => {
  return { status: 'ok', message: 'Server is running!' };
});

// Start server
const start = async () => {
  try {
    const port = 3003;
    const host = '0.0.0.0';
    
    await fastify.listen({ port, host });
    fastify.log.info(`🚀 Test API server started on ${host}:${port}`);
    fastify.log.info('Authentication middleware test successful!');
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
