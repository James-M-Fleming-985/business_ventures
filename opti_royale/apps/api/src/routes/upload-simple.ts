import { FastifyPluginAsync } from 'fastify';
import path from 'path';
import fs from 'fs';
import { pipeline } from 'stream/promises';

// Mock file storage - in production this would be a database
const uploads: any[] = [];

const uploadRoutes: FastifyPluginAsync = async (fastify) => {
  // Ensure uploads directory exists
  const uploadsDir = path.join(process.cwd(), 'uploads');
  if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
  }

  // Health check for upload service
  fastify.get('/health', async (request, reply) => {
    const dirExists = fs.existsSync(uploadsDir);
    
    return reply.send({
      status: 'healthy',
      service: 'upload',
      uploadsDirectory: dirExists ? 'exists' : 'missing',
      totalUploads: uploads.length,
      timestamp: new Date().toISOString()
    });
  });

  // Video upload endpoint with actual file handling
  fastify.post('/video', async (request, reply) => {
    try {
      // Handle multipart data
      const data = await request.file();
      
      if (!data) {
        return reply.code(400).send({ error: 'No file uploaded' });
      }

      // Validate file type
      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-m4v'];
      if (!allowedTypes.includes(data.mimetype)) {
        return reply.code(400).send({ 
          error: 'Invalid file type. Only MP4, MOV, and M4V files are allowed.' 
        });
      }

      // Validate file size (500MB limit)
      const maxSize = 500 * 1024 * 1024;
      if (data.file.readableLength && data.file.readableLength > maxSize) {
        return reply.code(400).send({ 
          error: 'File too large. Maximum size is 500MB.' 
        });
      }

      // Generate unique filename
      const fileExtension = path.extname(data.filename || '.mp4');
      const uniqueFilename = `${Date.now()}_${Math.random().toString(36).substring(7)}${fileExtension}`;
      const filePath = path.join(uploadsDir, uniqueFilename);

      // Save file
      await pipeline(data.file, fs.createWriteStream(filePath));

      // Create upload record
      const uploadRecord = {
        id: `upload_${Date.now()}`,
        filename: data.filename,
        storedAs: uniqueFilename,
        filePath,
        mimetype: data.mimetype,
        size: fs.statSync(filePath).size,
        status: 'completed',
        uploadedAt: new Date().toISOString(),
        processingStatus: {
          videoAnalysis: 'pending',
          cardDetection: 'pending',
          strategyAnalysis: 'pending'
        }
      };

      uploads.push(uploadRecord);

      // Start mock processing simulation
      setTimeout(() => {
        const upload = uploads.find(u => u.id === uploadRecord.id);
        if (upload) {
          upload.processingStatus.videoAnalysis = 'completed';
          upload.processingStatus.cardDetection = 'processing';
        }
      }, 2000);

      setTimeout(() => {
        const upload = uploads.find(u => u.id === uploadRecord.id);
        if (upload) {
          upload.processingStatus.cardDetection = 'completed';
          upload.processingStatus.strategyAnalysis = 'processing';
        }
      }, 4000);

      setTimeout(() => {
        const upload = uploads.find(u => u.id === uploadRecord.id);
        if (upload) {
          upload.processingStatus.strategyAnalysis = 'completed';
          upload.status = 'processed';
        }
      }, 6000);

      return reply.send({
        message: 'File uploaded successfully',
        fileId: uploadRecord.id,
        filename: uploadRecord.filename,
        size: uploadRecord.size,
        status: 'completed',
        processingStatus: uploadRecord.processingStatus
      });

    } catch (error) {
      console.error('Upload error:', error);
      return reply.code(500).send({ 
        error: 'Upload failed', 
        details: error instanceof Error ? error.message : 'Unknown error' 
      });
    }
  });

  // Get upload status
  fastify.get('/video/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const upload = uploads.find(u => u.id === id);
    
    if (!upload) {
      return reply.code(404).send({ error: 'Upload not found' });
    }
    
    return reply.send(upload);
  });

  // List user uploads
  fastify.get('/videos', async (request, reply) => {
  }, async (request, reply) => {
    const userId = (request as any).user.id;
    
    const userUploads = uploads.filter(u => u.userId === userId);
    
    return reply.send({
      uploads: userUploads,
      count: userUploads.length
    });
  });
};

export default uploadRoutes;
