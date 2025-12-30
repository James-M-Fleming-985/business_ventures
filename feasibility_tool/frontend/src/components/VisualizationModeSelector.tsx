import React, { useState, useCallback, useRef, useEffect } from 'react';
import { 
  Box, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Paper,
  Typography,
  Chip,
  Alert,
  Card,
  CardContent
} from '@mui/material';
import { Speed, Timeline } from '@mui/icons-material';
import type { ParameterSchema, CalculationResult, VisualizationMode, PerformanceMetrics } from '../types/visualization';

// Import visualization components
import TernaryDiagram from './visualizations/TernaryDiagram';
import FeasibilityVolume from './visualizations/FeasibilityVolume';
import ParallelCoordinates from './visualizations/ParallelCoordinates';
import ResponseSurface from './visualizations/ResponseSurface';
import SensitivityAnalysis from './visualizations/SensitivityAnalysis';
import CorrelationMatrix from './visualizations/CorrelationMatrix';
import ParetoFrontier from './visualizations/ParetoFrontier';
import RadarChart from './visualizations/RadarChart';

/**
 * Error Boundary Component
 */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; modeName: string },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Error in ${this.props.modeName}:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert severity="error">
          <Typography variant="h6">Visualization Error</Typography>
          <Typography variant="body2">
            Failed to render {this.props.modeName}. Error: {this.state.error?.message}
          </Typography>
        </Alert>
      );
    }

    return this.props.children;
  }
}

interface VisualizationProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
  initialMode?: string;
  hideSelector?: boolean;
}

/**
 * Performance Monitor Component
 */
const PerformanceMonitor: React.FC<{ metrics: PerformanceMetrics }> = React.memo(({ metrics }) => {
  const { fps, updateLatencyMs, frameDrops } = metrics;
  
  const getPerformanceColor = (): "success" | "warning" | "error" => {
    if (fps >= 55) return 'success';
    if (fps >= 30) return 'warning';
    return 'error';
  };

  const getLatencyColor = (): "success" | "warning" | "error" => {
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
 */
const VisualizationModeSelector: React.FC<VisualizationProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory,
  onParameterHighlight,
  initialMode,
  hideSelector = false
}) => {
  const [mode, setMode] = useState<VisualizationMode>((initialMode as VisualizationMode) || 'ternary');
  const [history, setHistory] = useState<CalculationResult[]>(explorationHistory);
  const [perfMetrics, setPerfMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    updateLatencyMs: 0,
    frameDrops: 0,
    lastMeasurement: window.performance.now()
  });
  
  const frameTimesRef = useRef<number[]>([]);
  const lastFrameRef = useRef<number>(window.performance.now());

  // Sync mode with external initialMode changes
  useEffect(() => {
    if (initialMode && initialMode !== mode) {
      setMode(initialMode as VisualizationMode);
    }
  }, [initialMode]);

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
      const now = window.performance.now();
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
        const frameDrops = frameTimesRef.current.filter(t => t > 16.67).length;

        setPerfMetrics(prev => ({
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
    const startTime = window.performance.now();
    setMode(newMode);
    const switchTime = window.performance.now() - startTime;

    if (switchTime > 200) {
      console.warn(`Mode switch took ${switchTime}ms, exceeding 200ms requirement`);
    }

    setPerfMetrics(prev => ({
      ...prev,
      updateLatencyMs: switchTime
    }));
  }, []);

  const visualizationModes = [
    { value: 'ternary' as const, label: 'Ternary Diagram', description: '3-score balance visualization' },
    { value: 'feasibility' as const, label: 'Feasibility Volume', description: '3D constraint boundaries' },
    { value: 'parallel' as const, label: 'Parallel Coordinates', description: 'Multi-dimensional view' },
    { value: 'response' as const, label: 'Response Surface', description: '2-variable interaction' },
    { value: 'sensitivity' as const, label: 'Sensitivity Analysis', description: 'Parameter impact ranking' },
    { value: 'correlation' as const, label: 'Correlation Matrix', description: 'Input-output relationships' },
    { value: 'pareto' as const, label: 'Pareto Frontier', description: 'Optimal solutions boundary' },
    { value: 'radar' as const, label: 'Radar Chart', description: 'Multi-dimensional radar' }
  ];

  const selectedModeInfo = visualizationModes.find(m => m.value === mode);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, gap: 2 }}>
      {/* Header with mode selector and performance metrics - conditionally visible */}
      {!hideSelector && (
      <Card elevation={2}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
            <FormControl sx={{ minWidth: 300 }}>
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

            <PerformanceMonitor metrics={perfMetrics} />
          </Box>

          {selectedModeInfo && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              📊 {selectedModeInfo.description}
            </Typography>
          )}
        </CardContent>
      </Card>
      )}

      {/* Visualization content area - DARK BACKGROUND, FULL HEIGHT */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#0a0a0a', position: 'relative' }}>
          {!calculationResult ? (
            <Alert severity="info" sx={{ mt: 2, mx: 2 }}>
              Adjust parameters to generate calculation results. Visualizations will appear here.
            </Alert>
          ) : (
            <Box sx={{ flex: 1, position: 'relative', overflow: 'hidden', width: '100%', height: '100%' }}>
              {/* Render selected visualization component with error boundary */}
              {mode === 'ternary' && (
                <ErrorBoundary modeName="Ternary Diagram">
                  <TernaryDiagram
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'feasibility' && (
                <ErrorBoundary modeName="Feasibility Volume">
                  <FeasibilityVolume
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'parallel' && (
                <ErrorBoundary modeName="Parallel Coordinates">
                  <ParallelCoordinates
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                    onParameterHighlight={onParameterHighlight}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'response' && (
                <ErrorBoundary modeName="Response Surface">
                  <ResponseSurface
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'sensitivity' && (
                <ErrorBoundary modeName="Sensitivity Analysis">
                  <SensitivityAnalysis
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'correlation' && (
                <ErrorBoundary modeName="Correlation Matrix">
                  <CorrelationMatrix
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'pareto' && (
                <ErrorBoundary modeName="Pareto Frontier">
                  <ParetoFrontier
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
              
              {mode === 'radar' && (
                <ErrorBoundary modeName="Radar Chart">
                  <RadarChart
                    calculationResult={calculationResult}
                    inputs={inputs}
                    parameterSchema={parameterSchema}
                    explorationHistory={history}
                  />
                </ErrorBoundary>
              )}
            </Box>
          )}
      </Box>
    </Box>
  );
};

export default VisualizationModeSelector;
