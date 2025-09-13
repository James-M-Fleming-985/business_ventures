// Ultra-Simple Development API Server
// No dependencies - just Node.js built-ins

const http = require('http');
const url = require('url');

// Mock database
const users = [];
let userIdCounter = 1;

// Helper function to parse JSON body
function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(JSON.parse(body));
      } catch (e) {
        resolve({});
      }
    });
  });
}

// CORS headers
function setCORS(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

// JSON response helper
function sendJSON(res, status, data) {
  setCORS(res);
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data, null, 2));
}

const server = http.createServer(async (req, res) => {
  const { pathname, query } = url.parse(req.url, true);
  const method = req.method;

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    setCORS(res);
    res.writeHead(200);
    res.end();
    return;
  }

  // Routes
  if (pathname === '/health' && method === 'GET') {
    sendJSON(res, 200, {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      users: users.length,
      server: 'Ultra-Simple Development API'
    });
    return;
  }

  if (pathname === '/api/auth/register' && method === 'POST') {
    const body = await parseBody(req);
    const { username, email, password, firstName, lastName } = body;

    if (!username || !email || !password) {
      sendJSON(res, 400, {
        error: 'Missing Required Fields',
        message: 'Username, email, and password are required'
      });
      return;
    }

    const existingUser = users.find(u => u.email === email);
    if (existingUser) {
      sendJSON(res, 400, {
        error: 'User Exists',
        message: 'Email already registered'
      });
      return;
    }

    const user = {
      id: userIdCounter++,
      username,
      email,
      firstName: firstName || '',
      lastName: lastName || '',
      role: users.length === 0 ? 'admin' : 'user',
      createdAt: new Date().toISOString()
    };

    users.push(user);

    sendJSON(res, 201, {
      message: `🎉 ${user.role === 'admin' ? 'Admin' : 'User'} account created successfully!`,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role
      },
      token: `dev-token-${user.id}`
    });
    return;
  }

  if (pathname === '/api/auth/login' && method === 'POST') {
    const body = await parseBody(req);
    const { email, password } = body;

    if (!email || !password) {
      sendJSON(res, 400, {
        error: 'Missing Credentials',
        message: 'Email and password required'
      });
      return;
    }

    const user = users.find(u => u.email === email);
    if (!user) {
      sendJSON(res, 401, {
        error: 'Invalid Credentials',
        message: 'User not found'
      });
      return;
    }

    sendJSON(res, 200, {
      message: 'Login successful',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role
      },
      token: `dev-token-${user.id}`
    });
    return;
  }

  // 404 for unknown routes
  sendJSON(res, 404, {
    error: 'Not Found',
    message: `Route ${pathname} not found`
  });
});

const PORT = 3003;
const HOST = '0.0.0.0';

server.listen(PORT, HOST, () => {
  console.log('🚀 Ultra-Simple OptiRoyale API started!');
  console.log(`📍 Server: http://localhost:${PORT}`);
  console.log('💡 Zero dependencies - maximum performance!');
  console.log('🎯 Ready to create your admin account!');
});
