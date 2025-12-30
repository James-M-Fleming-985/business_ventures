import React, { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface SensitivityAnalysisProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

interface SensitivityData {
  paramName: string;
  displayName: string;
  impact: number; // -100 to +100
  direction: 'positive' | 'negative';
}

/**
 * Sensitivity Analysis - Tornado chart showing parameter impact
 * Shows how each parameter affects the overall score
 */
const SensitivityAnalysis: React.FC<SensitivityAnalysisProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory
}) => {
  const svgWidth = 700;
  const svgHeight = 500;
  const padding = { top: 40, right: 150, bottom: 40, left: 150 };
  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  // Calculate sensitivity by analyzing correlation with overall_score in history
  const sensitivityData = useMemo<SensitivityData[]>(() => {
    if (explorationHistory.length < 3) {
      // Not enough data - use placeholder
      return parameterSchema.map(param => ({
        paramName: param.name,
        displayName: param.display_name || param.name,
        impact: Math.random() * 60 - 30, // Random placeholder
        direction: Math.random() > 0.5 ? 'positive' : 'negative'
      }));
    }

    // Calculate correlation between each parameter and overall_score
    const sensitivities = parameterSchema.map(param => {
      const paramValues: number[] = [];
      const scores: number[] = [];

      explorationHistory.forEach(result => {
        const value = result.visualization_point?.[param.name];
        if (value !== undefined && result.overall_score !== undefined) {
          paramValues.push(value);
          scores.push(result.overall_score);
        }
      });

      if (paramValues.length < 2) {
        return {
          paramName: param.name,
          displayName: param.display_name || param.name,
          impact: 0,
          direction: 'positive' as const
        };
      }

      // Simple correlation calculation
      const meanParam = paramValues.reduce((a, b) => a + b, 0) / paramValues.length;
      const meanScore = scores.reduce((a, b) => a + b, 0) / scores.length;

      let numerator = 0;
      let denomParam = 0;
      let denomScore = 0;

      for (let i = 0; i < paramValues.length; i++) {
        const diffParam = paramValues[i] - meanParam;
        const diffScore = scores[i] - meanScore;
        numerator += diffParam * diffScore;
        denomParam += diffParam * diffParam;
        denomScore += diffScore * diffScore;
      }

      const correlation = denomParam === 0 || denomScore === 0 
        ? 0 
        : numerator / Math.sqrt(denomParam * denomScore);

      return {
        paramName: param.name,
        displayName: param.display_name || param.name,
        impact: correlation * 100, // Scale to -100 to +100
        direction: correlation >= 0 ? 'positive' as const : 'negative' as const
      };
    });

    // Sort by absolute impact (tornado shape)
    return sensitivities.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
  }, [parameterSchema, explorationHistory]);

  const barHeight = plotHeight / sensitivityData.length;
  const maxImpact = Math.max(...sensitivityData.map(d => Math.abs(d.impact)), 1);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto', bgcolor: '#0a0a0a' }}>
      {explorationHistory.length < 3 && (
        <Typography variant="caption" sx={{ p: 1, color: '#ff9800' }}>
          ⚠️ Limited data ({explorationHistory.length} configurations). Explore more parameter combinations for accurate sensitivity.
        </Typography>
      )}

      <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'auto' }}>
        <svg 
          width={svgWidth} 
          height={svgHeight}
          style={{ background: '#0a0a0a', borderRadius: '4px' }}
        >
          {/* Center line */}
          <line
            x1={padding.left + plotWidth / 2}
            y1={padding.top}
            x2={padding.left + plotWidth / 2}
            y2={padding.top + plotHeight}
            stroke="#666"
            strokeWidth={2}
          />

          {/* Zero label */}
          <text
            x={padding.left + plotWidth / 2}
            y={padding.top - 10}
            textAnchor="middle"
            fill="#aaa"
            fontSize="12"
            fontWeight="bold"
          >
            0
          </text>

          {/* Negative impact label */}
          <text
            x={padding.left}
            y={padding.top - 10}
            textAnchor="start"
            fill="#f44336"
            fontSize="11"
          >
            ← Negative Impact
          </text>

          {/* Positive impact label */}
          <text
            x={padding.left + plotWidth}
            y={padding.top - 10}
            textAnchor="end"
            fill="#388e3c"
            fontSize="11"
          >
            Positive Impact →
          </text>

          {/* Bars */}
          {sensitivityData.map((data, i) => {
            const y = padding.top + i * barHeight;
            const centerX = padding.left + plotWidth / 2;
            const barWidthRatio = Math.abs(data.impact) / maxImpact;
            const barWidth = (plotWidth / 2) * barWidthRatio * 0.9; // 90% max width
            
            const barX = data.impact >= 0 ? centerX : centerX - barWidth;
            const color = data.impact >= 0 ? '#388e3c' : '#d32f2f';

            return (
              <g key={data.paramName}>
                {/* Bar */}
                <rect
                  x={barX}
                  y={y + barHeight * 0.15}
                  width={barWidth}
                  height={barHeight * 0.7}
                  fill={color}
                  opacity={0.8}
                  rx={3}
                />

                {/* Parameter label (left side) */}
                <text
                  x={padding.left - 10}
                  y={y + barHeight / 2}
                  textAnchor="end"
                  fill="#333"
                  fontSize="12"
                  dominantBaseline="middle"
                >
                  {data.displayName}
                </text>

                {/* Impact value (right side) */}
                <text
                  x={padding.left + plotWidth + 10}
                  y={y + barHeight / 2}
                  textAnchor="start"
                  fill={color}
                  fontSize="12"
                  fontWeight="bold"
                  dominantBaseline="middle"
                >
                  {data.impact >= 0 ? '+' : ''}{data.impact.toFixed(1)}
                </text>

                {/* Hover line */}
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + plotWidth}
                  y2={y}
                  stroke="#e0e0e0"
                  strokeWidth={0.5}
                />
              </g>
            );
          })}
        </svg>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
        Based on {explorationHistory.length} configurations. Explore more combinations to improve accuracy.
      </Typography>
    </Box>
  );
};

export default SensitivityAnalysis;
