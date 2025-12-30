import React, { useMemo } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface RadarChartProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Radar Chart - Spider chart showing composite scores on radial axes
 */
const RadarChart: React.FC<RadarChartProps> = ({
  calculationResult,
  explorationHistory
}) => {
  const size = 400;
  const center = size / 2;
  const maxRadius = size / 2 - 60;

  // Get all component scores from calculation result
  const scores = useMemo(() => {
    const components = calculationResult.components || {};
    const composites = calculationResult.composites || {};
    
    return [
      { label: 'Performance', value: composites.performance_score || 0, color: '#1976d2' },
      { label: 'Economic', value: composites.economic_score || 0, color: '#9c27b0' },
      { label: 'Durability', value: composites.durability_score || 0, color: '#2e7d32' },
      { label: 'Overall', value: calculationResult.overall_score || 0, color: '#ff5722' },
    ];
  }, [calculationResult]);

  const numAxes = scores.length;
  const angleStep = (2 * Math.PI) / numAxes;

  // Convert polar to cartesian
  const polarToCartesian = (angle: number, radius: number) => ({
    x: center + radius * Math.cos(angle - Math.PI / 2),
    y: center + radius * Math.sin(angle - Math.PI / 2)
  });

  // Build polygon path for scores
  const buildPolygon = (values: number[]): string => {
    return values.map((value, i) => {
      const angle = i * angleStep;
      const radius = (value / 100) * maxRadius;
      const point = polarToCartesian(angle, radius);
      return `${point.x},${point.y}`;
    }).join(' ');
  };

  const currentPolygon = buildPolygon(scores.map(s => s.value));

  // History polygons
  const historyPolygons = useMemo(() => {
    return explorationHistory.slice(-10).map((result, i) => {
      const values = [
        result.composites?.performance_score || 0,
        result.composites?.economic_score || 0,
        result.composites?.durability_score || 0,
        result.overall_score || 0
      ];
      return {
        path: buildPolygon(values),
        opacity: 0.1 + (i / 10) * 0.2
      };
    });
  }, [explorationHistory]);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: '#0a0a0a', p: 1 }}>
      <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <svg width={size} height={size} style={{ background: '#0a0a0a', borderRadius: '4px' }}>
          {/* Background circles (grid) */}
          {[0.2, 0.4, 0.6, 0.8, 1.0].map((scale, i) => (
            <circle
              key={`grid-${i}`}
              cx={center}
              cy={center}
              r={maxRadius * scale}
              fill="none"
              stroke="#e0e0e0"
              strokeWidth={1}
            />
          ))}

          {/* Radial axes */}
          {scores.map((score, i) => {
            const angle = i * angleStep;
            const endpoint = polarToCartesian(angle, maxRadius);
            const labelPoint = polarToCartesian(angle, maxRadius + 30);

            return (
              <g key={score.label}>
                {/* Axis line */}
                <line
                  x1={center}
                  y1={center}
                  x2={endpoint.x}
                  y2={endpoint.y}
                  stroke="#bdbdbd"
                  strokeWidth={1}
                />

                {/* Axis label */}
                <text
                  x={labelPoint.x}
                  y={labelPoint.y}
                  textAnchor="middle"
                  fill={score.color}
                  fontSize="13"
                  fontWeight="bold"
                  dominantBaseline="middle"
                >
                  {score.label}
                </text>

                {/* Value labels at max radius */}
                <text
                  x={endpoint.x}
                  y={endpoint.y}
                  textAnchor="middle"
                  fill="#999"
                  fontSize="10"
                  dominantBaseline="middle"
                >
                  100
                </text>
              </g>
            );
          })}

          {/* History polygons (ghost trails) */}
          {historyPolygons.map((item, i) => (
            <polygon
              key={`history-${i}`}
              points={item.path}
              fill="#888888"
              fillOpacity={item.opacity * 0.3}
              stroke="#888888"
              strokeWidth={1}
              strokeOpacity={item.opacity}
            />
          ))}

          {/* Current polygon (highlighted) */}
          <polygon
            points={currentPolygon}
            fill="#ff5722"
            fillOpacity={0.25}
            stroke="#ff5722"
            strokeWidth={3}
          />

          {/* Score points on current polygon */}
          {scores.map((score, i) => {
            const angle = i * angleStep;
            const radius = (score.value / 100) * maxRadius;
            const point = polarToCartesian(angle, radius);

            return (
              <circle
                key={`point-${i}`}
                cx={point.x}
                cy={point.y}
                r={5}
                fill={score.color}
                stroke="white"
                strokeWidth={2}
              />
            );
          })}

          {/* Center point */}
          <circle
            cx={center}
            cy={center}
            r={3}
            fill="#666"
          />
        </svg>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
        History shows last {Math.min(explorationHistory.length, 10)} configurations
      </Typography>
    </Box>
  );
};

export default RadarChart;
