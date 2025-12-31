/**
 * App Wrapper Component
 * Wraps the existing App.tsx with authentication
 */
import React from 'react';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import App from '../App';

export const AppWrapper: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#0a0a0a' }}>
      {/* Top Navigation Bar */}
      <AppBar position="static" sx={{ bgcolor: '#1a1a1a' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Feasibility Platform
          </Typography>
          <Typography variant="body2" sx={{ mr: 3, color: '#aaa' }}>
            {user?.email} {user?.is_superuser && '(Admin)'} · {user?.subscription_tier === 'pro' ? 'Pro' : 'Free'}
          </Typography>
          <Button
            onClick={handleLogout}
            sx={{
              color: 'white',
              textTransform: 'none',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* Main Application */}
      <App />
    </Box>
  );
};
