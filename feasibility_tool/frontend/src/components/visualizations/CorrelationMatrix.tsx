import React, { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface CorrelationMatrixProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Correlation Matrix - Heatmap showing relationships
 * Shows correlations between parameters and scores
 */
const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory
}) => {
  const cellSize = 60;
  const labelWidth = 120;
  const padding = 10;

  // Build correlation matrix
  const { variables, correlations } = useMemo(() => {
    const vars = [
      ...parameterSchema.map(p => ({ 
        key: p.name, 
        label: p.display_name || p.name,
        type: 'input' as const
      })),
      { key: 'performance_score', label: 'Performance', type: 'output' as const },
      { key: 'economic_score', label: 'Economic', type: 'output' as const },
      { key: 'durability_score', label: 'Durability', type: 'output' as const },
      { key: 'overall_score', label: 'Overall', type: 'output' as const }
    ];

    if (explorationHistory.length < 3) {
      // Not enough data - return placeholder
      const n = vars.length;
      const corr = Array(n).fill(0).map(() => Array(n).fill(0));
      for (let i = 0; i < n; i++) corr[i][i] = 1; // Diagonal = 1
      return { variables: vars, correlations: corr };
    }

    // Extract data for each variable
    const data: number[][] = vars.map(v => {
      return explorationHistory.map(result => {
        if (v.type === 'output') {
          if (v.key === 'overall_score') return result.overall_score || 0;
          return result.composites?.[v.key as keyof typeof result.composites] || 0;
        }
        return result.visualization_point?.[v.key] || 0;
      });
    });

    // Calculate correlation matrix
    const n = vars.length;
    const corr: number[][] = Array(n).fill(0).map(() => Array(n).fill(0));

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) {
          corr[i][j] = 1;
          continue;
        }

        const xi = data[i];
        const xj = data[j];

        const meanI = xi.reduce((a, b) => a + b, 0) / xi.length;
        const meanJ = xj.reduce((a, b) => a + b, 0) / xj.length;

        let numerator = 0;
        let denomI = 0;
        let denomJ = 0;

        for (let k = 0; k < xi.length; k++) {
          const diffI = xi[k] - meanI;
          const diffJ = xj[k] - meanJ;
          numerator += diffI * diffJ;
          denomI += diffI * diffI;
          denomJ += diffJ * diffJ;
        }

        const correlation = (denomI === 0 || denomJ === 0) 
          ? 0 
          : numerator / Math.sqrt(denomI * denomJ);

        corr[i][j] = correlation;
      }
    }

    return { variables: vars, correlations: corr };
  }, [parameterSchema, explorationHistory]);

  const matrixWidth = variables.length * cellSize + labelWidth;
  const matrixHeight = variables.length * cellSize + labelWidth;

  // Color scale for correlation (-1 to +1)
  const getColor = (correlation: number): string => {
    if (correlation > 0) {
      // Positive: white to green
      const intensity = Math.floor(correlation * 200);
      return `rgb(${200 - intensity}, 255, ${200 - intensity})`;
    } else {
      // Negative: white to red
      const intensity = Math.floor(Math.abs(correlation) * 200);
      return `rgb(255, ${200 - intensity}, ${200 - intensity})`;
    }
  };

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto', bgcolor: '#0a0a0a' }}>
      {explorationHistory.length < 3 && (
        <Typography variant="caption" sx={{ p: 1, color: '#ff9800' }}>
          ⚠️ Limited data ({explorationHistory.length} configurations). Correlations may not be accurate.
        </Typography>
      )}

      <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'auto', p: 2 }}>
        <svg 
          width={matrixWidth + padding * 2} 
          height={matrixHeight + padding * 2}
          style={{ background: '#0a0a0a', borderRadius: '4px' }}
        >
          {/* Column labels (top) */}
          {variables.map((v, i) => {
            const x = labelWidth + i * cellSize + cellSize / 2;
            const y = labelWidth - 10;

            return (
              <text
                key={`col-${i}`}
                x={x}
                y={y}
                textAnchor="end"
                fill={v.type === 'output' ? '#9c27b0' : '#1976d2'}
                fontSize="10"
                fontWeight="bold"
                transform={`rotate(-45, ${x}, ${y})`}
              >
                {v.label}
              </text>
            );
          })}

          {/* Row labels (left) */}
          {variables.map((v, i) => {
            const x = labelWidth - 10;
            const y = labelWidth + i * cellSize + cellSize / 2;

            return (
              <text
                key={`row-${i}`}
                x={x}
                y={y}
                textAnchor="end"
                fill={v.type === 'output' ? '#9c27b0' : '#1976d2'}
                fontSize="10"
                fontWeight="bold"
                dominantBaseline="middle"
              >
                {v.label}
              </text>
            );
          })}

          {/* Correlation cells */}
          {correlations.map((row, i) =>
            row.map((corr, j) => {
              const x = labelWidth + j * cellSize;
              const y = labelWidth + i * cellSize;
              const color = getColor(corr);

              return (
                <g key={`cell-${i}-${j}`}>
                  <rect
                    x={x}
                    y={y}
                    width={cellSize}
                    height={cellSize}
                    fill={color}
                    stroke="#fff"
                    strokeWidth={1}
                  />
                  <text
                    x={x + cellSize / 2}
                    y={y + cellSize / 2}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill={Math.abs(corr) > 0.5 ? '#000' : '#666'}
                    fontSize="11"
                    fontWeight="bold"
                  >
                    {corr.toFixed(2)}
                  </text>
                </g>
              );
            })
          )}
        </svg>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
        Based on {explorationHistory.length} configurations. Values range from -1 (negative) to +1 (positive).
      </Typography>
    </Box>
  );
};

export default CorrelationMatrix;
