import React, { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface ParallelCoordinatesProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
}

/**
 * Parallel Coordinates - Multi-dimensional visualization
 * Shows all inputs + 3 composite outputs on vertical axes with polylines
 */
const ParallelCoordinates: React.FC<ParallelCoordinatesProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory,
  onParameterHighlight
}) => {
  const svgWidth = 800;
  const svgHeight = 400;
  const padding = { top: 60, right: 40, bottom: 40, left: 40 };
  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  // Build axes: all input parameters + 3 composite scores
  const axes = useMemo(() => {
    const inputAxes = parameterSchema
      .filter(param => param.type !== 'select' && param.min_value != null && param.max_value != null) // Skip dropdowns
      .map(param => ({
        key: param.name,
        label: param.display_name || param.name,
        min: param.min_value!,
        max: param.max_value!,
        unit: param.unit || '',
        isOutput: false
      }));

    const outputAxes = [
      { key: 'performance_score', label: 'Performance', min: 0, max: 100, unit: '', isOutput: true },
      { key: 'economic_score', label: 'Economic', min: 0, max: 100, unit: '', isOutput: true },
      { key: 'durability_score', label: 'Durability', min: 0, max: 100, unit: '', isOutput: true }
    ];

    return [...inputAxes, ...outputAxes];
  }, [parameterSchema]);

  const axisSpacing = plotWidth / (axes.length - 1);

  // Normalize value to 0-1 range
  const normalize = (value: number, min: number, max: number): number => {
    if (max === min) return 0.5;
    return (value - min) / (max - min);
  };

  // Get value for an axis from result
  const getAxisValue = (result: CalculationResult, axis: typeof axes[0]): number => {
    if (axis.isOutput) {
      return result.composites?.[axis.key as keyof typeof result.composites] ?? 50;
    }
    return result.visualization_point?.[axis.key] ?? ((axis.min + axis.max) / 2);
  };

  // Build polyline path for a single configuration
  const buildPath = (result: CalculationResult, opacity = 1): string => {
    const points = axes.map((axis, i) => {
      const value = getAxisValue(result, axis);
      const normalized = normalize(value, axis.min, axis.max);
      const x = padding.left + i * axisSpacing;
      const y = padding.top + plotHeight * (1 - normalized); // Invert y for SVG
      return `${x},${y}`;
    });
    return points.join(' L ');
  };

  const currentPath = buildPath(calculationResult);
  const historyPaths = explorationHistory.slice(-20).map((result, i) => ({
    path: buildPath(result),
    opacity: 0.1 + (i / 20) * 0.3
  }));

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto', bgcolor: '#0a0a0a' }}>
      <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'auto' }}>
        <svg 
          width={svgWidth} 
          height={svgHeight}
          style={{ background: '#0a0a0a', borderRadius: '4px' }}
        >
          {/* Draw axes */}
          {axes.map((axis, i) => {
            const x = padding.left + i * axisSpacing;
            return (
              <g key={axis.key}>
                {/* Axis line */}
                <line
                  x1={x}
                  y1={padding.top}
                  x2={x}
                  y2={padding.top + plotHeight}
                  stroke={axis.isOutput ? '#9c27b0' : '#1976d2'}
                  strokeWidth={2}
                />

                {/* Axis label */}
                <text
                  x={x}
                  y={padding.top - 30}
                  textAnchor="middle"
                  fill={axis.isOutput ? '#9c27b0' : '#1976d2'}
                  fontSize="12"
                  fontWeight="bold"
                  style={{ cursor: 'pointer' }}
                  onClick={() => onParameterHighlight?.(axis.key)}
                >
                  {axis.label}
                </text>

                {/* Min/Max labels */}
                <text
                  x={x}
                  y={padding.top + plotHeight + 15}
                  textAnchor="middle"
                  fill="#888"
                  fontSize="10"
                >
                  {axis.min.toFixed(1)}{axis.unit}
                </text>
                <text
                  x={x}
                  y={padding.top - 10}
                  textAnchor="middle"
                  fill="#888"
                  fontSize="10"
                >
                  {axis.max.toFixed(1)}{axis.unit}
                </text>

                {/* Current value indicator */}
                {(() => {
                  const value = getAxisValue(calculationResult, axis);
                  const normalized = normalize(value, axis.min, axis.max);
                  const y = padding.top + plotHeight * (1 - normalized);
                  return (
                    <>
                      <circle
                        cx={x}
                        cy={y}
                        r={4}
                        fill="#ff5722"
                        stroke="white"
                        strokeWidth={2}
                      />
                      <text
                        x={x}
                        y={y - 10}
                        textAnchor="middle"
                        fill="#ff5722"
                        fontSize="10"
                        fontWeight="bold"
                      >
                        {value.toFixed(1)}
                      </text>
                    </>
                  );
                })()}
              </g>
            );
          })}

          {/* History polylines (ghost trails) */}
          {historyPaths.map((item, i) => (
            <polyline
              key={`history-${i}`}
              points={item.path}
              fill="none"
              stroke="#888888"
              strokeWidth={1.5}
              opacity={item.opacity}
            />
          ))}

          {/* Current polyline (highlighted) */}
          <polyline
            points={currentPath}
            fill="none"
            stroke="#ff5722"
            strokeWidth={3}
            opacity={0.9}
          />
        </svg>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
        Click axis labels to highlight parameters. History shows last {Math.min(explorationHistory.length, 20)} configurations.
      </Typography>
    </Box>
  );
};

export default ParallelCoordinates;
