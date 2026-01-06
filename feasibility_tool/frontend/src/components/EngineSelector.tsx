import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { Science, Engineering } from '@mui/icons-material';
import axios from 'axios';
import type { EngineMetadata } from '../types/visualization';

// Use VITE_API_URL and add protocol if missing (same as App.tsx)
let API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
if (API_BASE_URL && !API_BASE_URL.startsWith('http://') && !API_BASE_URL.startsWith('https://')) {
  API_BASE_URL = `https://${API_BASE_URL}`;
}
console.log('🔧 EngineSelector API_BASE_URL:', API_BASE_URL);

interface EngineSelectorProps {
  onEngineSelect: (engineId: string) => void;
  selectedEngineId?: string;
}

export default function EngineSelector({ onEngineSelect, selectedEngineId }: EngineSelectorProps) {
  const [engines, setEngines] = useState<EngineMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEngines();
  }, []);

  const fetchEngines = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/api/engines`);
      
      if (response.data.success && response.data.data) {
        setEngines(response.data.data);
      } else {
        throw new Error('Failed to load engines');
      }
    } catch (err) {
      console.error('Error fetching engines:', err);
      setError(err instanceof Error ? err.message : 'Failed to load engines');
    } finally {
      setLoading(false);
    }
  };

  const getEngineIcon = (domain: string) => {
    if (domain.toLowerCase().includes('energy')) return <Engineering />;
    return <Science />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Select Calculation Engine
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose a mathematical engine to analyze your system. Each engine provides specialized calculations for different domains.
      </Typography>

      <Grid container spacing={3}>
        {engines.map((engine) => (
          <Grid item xs={12} sm={6} md={4} key={engine.engine_id}>
            <Card
              sx={{
                height: '100%',
                border: selectedEngineId === engine.engine_id ? 2 : 0,
                borderColor: 'primary.main',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardActionArea
                onClick={() => onEngineSelect(engine.engine_id)}
                sx={{ height: '100%' }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    {getEngineIcon(engine.domain)}
                    <Typography variant="h6" component="div">
                      {engine.name}
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: '60px' }}>
                    {engine.description}
                  </Typography>

                  <Box display="flex" gap={1} flexWrap="wrap">
                    <Chip label={engine.domain} size="small" color="primary" variant="outlined" />
                    <Chip label={`v${engine.version}`} size="small" variant="outlined" />
                    {selectedEngineId === engine.engine_id && (
                      <Chip label="Selected" size="small" color="primary" />
                    )}
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {engines.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No engines registered. Add engines to the registry to get started.
        </Alert>
      )}
    </Box>
  );
}
