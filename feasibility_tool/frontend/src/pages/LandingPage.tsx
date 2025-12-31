/**
 * Landing Page - Home page for unauthenticated users
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Container, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import { Science, Speed, AttachMoney, TrendingUp } from '@mui/icons-material';

export const LandingPage: React.FC = () => {
  return (
    <Box sx={{ bgcolor: '#f8f9fa' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 12,
          textAlign: 'center'
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="h2" fontWeight="bold" gutterBottom>
            Transform Your Feasibility Analysis
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.95 }}>
            Advanced 3D visualizations, delta analysis, and AI-powered insights for engineering feasibility studies
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              component={Link}
              to="/register"
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: '#667eea',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                textTransform: 'none',
                '&:hover': { bgcolor: '#f0f0f0' }
              }}
            >
              Start Free Trial
            </Button>
            <Button
              component={Link}
              to="/login"
              variant="outlined"
              size="large"
              sx={{
                borderColor: 'white',
                color: 'white',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                textTransform: 'none',
                '&:hover': { borderColor: '#f0f0f0', bgcolor: 'rgba(255,255,255,0.1)' }
              }}
            >
              Sign In
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography variant="h3" textAlign="center" fontWeight="bold" gutterBottom>
          Powerful Features
        </Typography>
        <Typography variant="h6" textAlign="center" color="text.secondary" sx={{ mb: 6 }}>
          Everything you need for comprehensive feasibility analysis
        </Typography>

        <Grid container spacing={4}>
          <Grid item xs={12} md={6} lg={3}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
              <Science sx={{ fontSize: 60, color: '#667eea', mb: 2 }} />
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  9 Visualization Modes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Delta Cube, Ternary, Feasibility Volume, Parallel Coordinates, Response Surface, and more
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
              <Speed sx={{ fontSize: 60, color: '#764ba2', mb: 2 }} />
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Real-time Delta Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Compare against baselines with instant ΔP, ΔE, ΔD calculations and hover tooltips
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
              <TrendingUp sx={{ fontSize: 60, color: '#667eea', mb: 2 }} />
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Actionable Insights
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  AI-powered recommendations based on your exploration patterns and cost analysis
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
              <AttachMoney sx={{ fontSize: 60, color: '#764ba2', mb: 2 }} />
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Multi-Domain Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Performance, Durability, and Economic domains with transparent formula explanations
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Pricing Section */}
      <Box sx={{ bgcolor: 'white', py: 10 }}>
        <Container maxWidth="lg">
          <Typography variant="h3" textAlign="center" fontWeight="bold" gutterBottom>
            Simple, Transparent Pricing
          </Typography>
          <Typography variant="h6" textAlign="center" color="text.secondary" sx={{ mb: 6 }}>
            Choose the plan that fits your needs
          </Typography>

          <Grid container spacing={4} justifyContent="center">
            <Grid item xs={12} md={6} lg={5}>
              <Card sx={{ textAlign: 'center', p: 4, border: '2px solid #e0e0e0' }}>
                <Typography variant="h5" fontWeight="bold" gutterBottom>
                  Free
                </Typography>
                <Typography variant="h3" fontWeight="bold" sx={{ my: 2 }}>
                  £0
                  <Typography component="span" variant="h6" color="text.secondary">
                    /month
                  </Typography>
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Perfect for getting started
                </Typography>
                <Box sx={{ textAlign: 'left', mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ 5 explorations per month</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Basic visualizations</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Baseline comparison</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Export results</Typography>
                </Box>
                <Button
                  component={Link}
                  to="/register"
                  variant="outlined"
                  fullWidth
                  size="large"
                  sx={{ textTransform: 'none' }}
                >
                  Get Started Free
                </Button>
              </Card>
            </Grid>

            <Grid item xs={12} md={6} lg={5}>
              <Card
                sx={{
                  textAlign: 'center',
                  p: 4,
                  border: '3px solid #667eea',
                  position: 'relative',
                  boxShadow: 3
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    top: -15,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    bgcolor: '#667eea',
                    color: 'white',
                    px: 3,
                    py: 0.5,
                    borderRadius: 20,
                    fontWeight: 'bold'
                  }}
                >
                  POPULAR
                </Box>
                <Typography variant="h5" fontWeight="bold" gutterBottom>
                  Pro
                </Typography>
                <Typography variant="h3" fontWeight="bold" sx={{ my: 2 }}>
                  £9.99
                  <Typography component="span" variant="h6" color="text.secondary">
                    /month
                  </Typography>
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  For serious professionals
                </Typography>
                <Box sx={{ textAlign: 'left', mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Unlimited explorations</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ All 9 visualization modes</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Multiple baselines</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Exploration history export</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ Priority support</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>✓ API access</Typography>
                </Box>
                <Button
                  component={Link}
                  to="/register"
                  variant="contained"
                  fullWidth
                  size="large"
                  sx={{
                    textTransform: 'none',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #65408d 100%)',
                    }
                  }}
                >
                  Start Pro Trial
                </Button>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: '#1a1a1a', color: 'white', py: 4, textAlign: 'center' }}>
        <Typography variant="body2">
          © 2025 Feasibility Platform · Powered by AI · Built for Engineers
        </Typography>
      </Box>
    </Box>
  );
};
