import React, { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import * as THREE from 'three';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface ResponseSurfaceProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Response Surface - 3D surface showing how overall_score varies
 * Allows user to select 2 parameters for X/Y axes, Z shows overall_score
 */
const ResponseSurface: React.FC<ResponseSurfaceProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory
}) => {
  // Default to first two parameters
  const [xParam, setXParam] = useState(parameterSchema[0]?.name || '');
  const [yParam, setYParam] = useState(parameterSchema[1]?.name || parameterSchema[0]?.name || '');

  // Build response surface from history
  const surfaceData = useMemo(() => {
    if (!xParam || !yParam || explorationHistory.length < 3) {
      return null;
    }

    const xParamInfo = parameterSchema.find(p => p.name === xParam);
    const yParamInfo = parameterSchema.find(p => p.name === yParam);

    if (!xParamInfo || !yParamInfo) return null;

    // Create grid
    const gridSize = 20;
    const grid: number[][] = Array(gridSize).fill(0).map(() => Array(gridSize).fill(0));

    // Map history points to grid
    const xRange = xParamInfo.max - xParamInfo.min;
    const yRange = yParamInfo.max - yParamInfo.min;

    const pointsInGrid: Map<string, number[]> = new Map();

    explorationHistory.forEach(result => {
      const xVal = result.visualization_point?.[xParam];
      const yVal = result.visualization_point?.[yParam];
      const score = result.overall_score;

      if (xVal === undefined || yVal === undefined || score === undefined) return;

      const xIdx = Math.floor(((xVal - xParamInfo.min) / xRange) * (gridSize - 1));
      const yIdx = Math.floor(((yVal - yParamInfo.min) / yRange) * (gridSize - 1));

      const key = `${xIdx},${yIdx}`;
      if (!pointsInGrid.has(key)) {
        pointsInGrid.set(key, []);
      }
      pointsInGrid.get(key)!.push(score);
    });

    // Average scores in each cell
    pointsInGrid.forEach((scores, key) => {
      const [xIdx, yIdx] = key.split(',').map(Number);
      grid[yIdx][xIdx] = scores.reduce((a, b) => a + b, 0) / scores.length;
    });

    // Interpolate missing cells (simple averaging)
    for (let i = 0; i < gridSize; i++) {
      for (let j = 0; j < gridSize; j++) {
        if (grid[i][j] === 0) {
          // Average from neighbors
          const neighbors: number[] = [];
          if (i > 0 && grid[i - 1][j] > 0) neighbors.push(grid[i - 1][j]);
          if (i < gridSize - 1 && grid[i + 1][j] > 0) neighbors.push(grid[i + 1][j]);
          if (j > 0 && grid[i][j - 1] > 0) neighbors.push(grid[i][j - 1]);
          if (j < gridSize - 1 && grid[i][j + 1] > 0) neighbors.push(grid[i][j + 1]);

          if (neighbors.length > 0) {
            grid[i][j] = neighbors.reduce((a, b) => a + b, 0) / neighbors.length;
          } else {
            grid[i][j] = 50; // Default
          }
        }
      }
    }

    return {
      grid,
      xParamInfo,
      yParamInfo,
      gridSize
    };
  }, [xParam, yParam, parameterSchema, explorationHistory]);

  // Build mesh geometry
  const surfaceGeometry = useMemo(() => {
    if (!surfaceData) return null;

    const { grid, gridSize } = surfaceData;
    const geometry = new THREE.PlaneGeometry(2, 2, gridSize - 1, gridSize - 1);
    
    const positions = geometry.attributes.position.array as Float32Array;
    
    for (let i = 0; i < gridSize; i++) {
      for (let j = 0; j < gridSize; j++) {
        const idx = (i * gridSize + j) * 3;
        positions[idx + 2] = (grid[i][j] / 100) * 1.5; // Scale height
      }
    }

    geometry.computeVertexNormals();
    return geometry;
  }, [surfaceData]);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a', p: 1 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Response surface: Select 2 parameters to see how overall score varies with their interaction.
      </Typography>

      {/* Parameter selectors */}
      <Box display="flex" gap={2} mb={2}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>X Axis</InputLabel>
          <Select
            value={xParam}
            label="X Axis"
            onChange={(e) => setXParam(e.target.value)}
          >
            {parameterSchema.map(p => (
              <MenuItem key={p.name} value={p.name}>
                {p.display_name || p.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Y Axis</InputLabel>
          <Select
            value={yParam}
            label="Y Axis"
            onChange={(e) => setYParam(e.target.value)}
          >
            {parameterSchema.map(p => (
              <MenuItem key={p.name} value={p.name}>
                {p.display_name || p.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {explorationHistory.length < 3 && (
        <Typography variant="caption" color="warning.main" sx={{ mb: 1 }}>
          ⚠️ Limited data. Explore more parameter combinations for accurate surface.
        </Typography>
      )}

      <Box sx={{ flex: 1, position: 'relative' }}>
        {surfaceGeometry && surfaceData ? (
          <Canvas camera={{ position: [3, 3, 3], fov: 60 }} style={{ background: '#0a0a0a' }}>
            <ambientLight intensity={0.6} />
            <pointLight position={[10, 10, 10]} intensity={0.8} />
            <pointLight position={[-10, -10, -10]} intensity={0.3} />

            <OrbitControls />

            {/* Response surface */}
            <mesh geometry={surfaceGeometry} rotation={[-Math.PI / 2, 0, 0]}>
              <meshStandardMaterial 
                color="#1976d2"
                wireframe={false}
                side={THREE.DoubleSide}
                vertexColors={false}
              />
            </mesh>

            {/* Wireframe overlay */}
            <mesh geometry={surfaceGeometry} rotation={[-Math.PI / 2, 0, 0]}>
              <meshBasicMaterial 
                color="#333333"
                wireframe={true}
                opacity={0.3}
                transparent
              />
            </mesh>

            {/* Base plane */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
              <planeGeometry args={[2, 2]} />
              <meshBasicMaterial color="#e0e0e0" opacity={0.5} transparent />
            </mesh>

            {/* Axis labels */}
            <Text position={[1.3, 0, 0]} fontSize={0.12} color="#1976d2">
              {surfaceData.xParamInfo.display_name || surfaceData.xParamInfo.name}
            </Text>
            <Text position={[0, 0, 1.3]} fontSize={0.12} color="#9c27b0">
              {surfaceData.yParamInfo.display_name || surfaceData.yParamInfo.name}
            </Text>
            <Text position={[0, 1.3, 0]} fontSize={0.12} color="#2e7d32">
              Overall Score
            </Text>

            <primitive object={new THREE.AxesHelper(1.2)} />
          </Canvas>
        ) : (
          <Box 
            display="flex" 
            justifyContent="center" 
            alignItems="center" 
            height="100%"
            bgcolor="#f5f5f5"
          >
            <Typography color="text.secondary">
              Not enough data to generate surface. Explore more parameter combinations.
            </Typography>
          </Box>
        )}
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
        Based on {explorationHistory.length} configurations
      </Typography>
    </Box>
  );
};

export default ResponseSurface;
