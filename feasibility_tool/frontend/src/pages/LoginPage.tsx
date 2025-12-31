/**
 * Login Page
 * User authentication form
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Box, TextField, Button, Typography, Alert, Paper } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/app');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 2
      }}
    >
      <Paper
        elevation={6}
        sx={{
          width: '100%',
          maxWidth: 450,
          padding: 4,
          borderRadius: 3
        }}
      >
        <Box sx={{ textAlign: 'center', marginBottom: 3 }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Welcome Back
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sign in to access your feasibility platform
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            fullWidth
            autoComplete="email"
            sx={{ marginBottom: 2 }}
          />

          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            fullWidth
            autoComplete="current-password"
            sx={{ marginBottom: 3 }}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading}
            sx={{
              marginBottom: 2,
              py: 1.5,
              textTransform: 'none',
              fontSize: '1.1rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #65408d 100%)',
              }
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#667eea', textDecoration: 'none', fontWeight: 600 }}>
              Sign up
            </Link>
          </Typography>
        </Box>

        <Box sx={{ textAlign: 'center', marginTop: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <Link to="/" style={{ color: '#667eea', textDecoration: 'none' }}>
              ← Back to home
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};
