import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { 
  Box, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Paper,
  Typography,
  Chip,
  Alert
} from '@mui/material';
import { Speed, Timeline } from '@mui/icons-material';

// Import shared types from central location
interface ParameterSchema {
  name: string;
  type: string;
  min_value?: number;
  max_value?: number;
  default: any;
  unit: string;
  description: string;
  options?: string[];
}

interface ComponentResult {
  value: number;
  unit: string;
  formula: string;
  calculation_steps: string[];
  normalized: number;
}

interface CalculationResult {
  components: Record<string, ComponentResult>;
  composites: Record<string, number>;
  visualization_point: { x: number; y: number; z: number };
  overall_score: number;
  metadata?: any;
}

interface VisualizationProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
}

type VisualizationMode =
  | 'ternary'
  | 'feasibility'
  | 'parallel'
  | 'response'
  | 'sensitivity'
  | 'correlation'
  | 'pareto'
  | 'radar';

interface PerformanceMetrics {
  fps: number;
  updateLatencyMs: number;
  frameDrops: number;
  lastMeasurement: number;
}

/**
 * Performance Monitor Component
 * Tracks FPS and update latency in real-time
 */
const PerformanceMonitor: React.FC<{ metrics: PerformanceMetrics }> = React.memo(({ metrics }) => {
  const { fps, updateLatencyMs, frameDrops } = metrics;
  
  const getPerformanceColor = () => {
    if (fps >= 55) return 'success';
    if (fps >= 30) return 'warning';
    return 'error';
  };

  const getLatencyColor = () => {
    if (updateLatencyMs <= 5) return 'success';
    if (updateLatencyMs <= 10) return 'warning';
    return 'error';
  };

  return (
    <Box display="flex" gap={1} alignItems="center">
      <Chip
        icon={<Speed />}
        label={`${fps.toFixed(1)} FPS`}
        size="small"
        color={getPerformanceColor()}
        variant="outlined"
      />
      <Chip
        icon={<Timeline />}
        label={`${updateLatencyMs.toFixed(1)}ms`}
        size="small"
        color={getLatencyColor()}
        variant="outlined"
      />
      {frameDrops > 0 && (
        <Chip
          label={`${frameDrops} drops`}
          size="small"
          color="warning"
        />
      )}
    </Box>
  );
});

PerformanceMonitor.displayName = 'PerformanceMonitor';

/**
 * Main Visualization Mode Selector Component
 * Orchestrates visualization mode switching and manages state/history/performance
 */
const VisualizationModeSelector: React.FC<VisualizationProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory,
  onParameterHighlight
}) => {
  const [mode, setMode] = useState<VisualizationMode>('ternary');
  const [history, setHistory] = useState<CalculationResult[]>(explorationHistory);
  const [performance, setPerformance] = useState<PerformanceMetrics>({
    fps: 60,
    updateLatencyMs: 0,
    frameDrops: 0,
    lastMeasurement: performance.now()
  });
  
  const frameTimesRef = useRef<number[]>([]);
  const lastFrameRef = useRef<number>(performance.now());

  // Track history - limit to 100 entries
  useEffect(() => {
    if (calculationResult) {
      setHistory(prev => {
        const newHistory = [...prev, calculationResult];
        return newHistory.slice(-100); // Keep last 100 only
      });
    }
  }, [calculationResult]);

  // Performance monitoring
  useEffect(() => {
    let animationFrameId: number;

    const measurePerformance = () => {
      const now = performance.now();
      const frameTime = now - lastFrameRef.current;
      lastFrameRef.current = now;

      frameTimesRef.current.push(frameTime);
      if (frameTimesRef.current.length > 60) {
        frameTimesRef.current.shift();
      }

      // Calculate FPS from last 60 frames
      if (frameTimesRef.current.length > 10) {
        const avgFrameTime = frameTimesRef.current.reduce((a, b) => a + b, 0) / frameTimesRef.current.length;
        const fps = 1000 / avgFrameTime;
        const frameDrops = frameTimesRef.current.filter(t => t > 16.67).length; // Count frames > 60 FPS threshold

        setPerformance(prev => ({
          ...prev,
          fps: Math.min(fps, 60),
          frameDrops,
          lastMeasurement: now
        }));
      }

      animationFrameId = requestAnimationFrame(measurePerformance);
    };

    animationFrameId = requestAnimationFrame(measurePerformance);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  // Handle mode switching with performance tracking
  const handleModeChange = useCallback((newMode: VisualizationMode) => {
    const startTime = performance.now();
    setMode(newMode);
    const switchTime = performance.now() - startTime;

    if (switchTime > 200) {
      console.warn(`Mode switch took ${switchTime}ms, exceeding 200ms requirement`);
    }

    setPerformance(prev => ({
      ...prev,
      updateLatencyMs: switchTime
    }));
  }, []);

  const visualizationModes = [
    { value: 'ternary', label: 'Ternary Diagram', description: '3-score balance visualization' },
    { value: 'feasibility', label: 'Feasibility Volume', description: '3D constraint boundaries' },
    { value: 'parallel', label: 'Parallel Coordinates', description: 'Multi-dimensional view' },
    { value: 'response', label: 'Response Surface', description: '2-variable interaction' },
    { value: 'sensitivity', label: 'Sensitivity Analysis', description: 'Parameter impact ranking' },
    { value: 'correlation', label: 'Correlation Matrix', description: 'Input-output relationships' },
    { value: 'pareto', label: 'Pareto Frontier', description: 'Optimal solutions boundary' },
    { value: 'radar', label: 'Radar Chart', description: 'Multi-dimensional radar' }
  ];

  const selectedModeInfo = visualizationModes.find(m => m.value === mode);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with mode selector and performance metrics */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <FormControl sx={{ minWidth: 250 }}>
            <InputLabel>Visualization Mode</InputLabel>
            <Select
              value={mode}
              label="Visualization Mode"
              onChange={(e) => handleModeChange(e.target.value as VisualizationMode)}
            >
              {visualizationModes.map(({ value, label, description }) => (
                <MenuItem key={value} value={value}>
                  <Box>
                    <Typography variant="body1">{label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <PerformanceMonitor metrics={performance} />
        </Box>

        {selectedModeInfo && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {selectedModeInfo.description}
          </Typography>
        )}
      </Paper>

      {/* Visualization content area */}
      <Paper sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {!calculationResult ? (
          <Alert severity="info">
            Adjust parameters to see visualization. Calculation results will appear here.
          </Alert>
        ) : (
          <Box sx={{ flex: 1, position: 'relative' }}>
            {/* Placeholder for actual visualization components - will be replaced with real components */}
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2
              }}
            >
              <Typography variant="h6" color="text.secondary">
                {selectedModeInfo?.label}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Visualization component will render here
              </Typography>
              
              {/* Show current scores */}
              {calculationResult.composites && (
                <Box display="flex" gap={2} mt={2}>
                  <Chip 
                    label={`Performance: ${calculationResult.composites.performance_score?.toFixed(1) || 'N/A'}`}
                    color="primary"
                  />
                  <Chip 
                    label={`Economic: ${calculationResult.composites.economic_score?.toFixed(1) || 'N/A'}`}
                    color="secondary"
                  />
                  <Chip 
                    label={`Durability: ${calculationResult.composites.durability_score?.toFixed(1) || 'N/A'}`}
                    color="success"
                  />
                </Box>
              )}

              <Typography variant="caption" color="text.secondary">
                History: {history.length} configurations | Overall Score: {calculationResult.overall_score.toFixed(1)}
              </Typography>
            </Box>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

VisualizationModeSelector.displayName = 'VisualizationModeSelector';

export default VisualizationModeSelector;