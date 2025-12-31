/**
 * Register Page
 * New user registration form
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Box, TextField, Button, Typography, Alert, Paper } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

export const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(password)) {
      setError('Password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(password)) {
      setError('Password must contain at least one lowercase letter');
      return;
    }

    if (!/[0-9]/.test(password)) {
      setError('Password must contain at least one number');
      return;
    }

    setLoading(true);

    try {
      await register(email, password, fullName);
      navigate('/app');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
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
            Create Account
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Start your feasibility analysis journey
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            label="Full Name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            fullWidth
            autoComplete="name"
            sx={{ marginBottom: 2 }}
          />

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
            autoComplete="new-password"
            helperText="At least 8 characters, 1 uppercase, 1 lowercase, 1 number"
            sx={{ marginBottom: 2 }}
          />

          <TextField
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            fullWidth
            autoComplete="new-password"
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
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#667eea', textDecoration: 'none', fontWeight: 600 }}>
              Sign in
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
