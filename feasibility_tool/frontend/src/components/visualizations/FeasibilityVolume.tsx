import React, { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Box, Typography, Slider, FormControl, InputLabel } from '@mui/material';
import * as THREE from 'three';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface FeasibilityVolumeProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Feasibility Volume - 3D volumetric visualization
 * Shows feasible parameter space as a volume where overall_score > threshold
 */
const FeasibilityVolume: React.FC<FeasibilityVolumeProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory
}) => {
  const [scoreThreshold, setScoreThreshold] = useState(60);

  // Build voxel grid showing feasible regions
  const voxelData = useMemo(() => {
    if (explorationHistory.length < 5) {
      return { voxels: [], bounds: null };
    }

    // Use first 3 NUMERIC parameters for 3D visualization
    const params = parameterSchema
      .filter(p => p.type !== 'select' && p.min_value != null && p.max_value != null)
      .slice(0, 3);
    if (params.length < 3) {
      return { voxels: [], bounds: null };
    }

    const gridSize = 15;
    const voxels: Array<{ position: THREE.Vector3; score: number; isFeasible: boolean }> = [];

    // Map history to grid
    const ranges = params.map(p => ({ min: p.min_value!, max: p.max_value!, span: p.max_value! - p.min_value! }));

    explorationHistory.forEach(result => {
      const paramVals = params.map(p => result.visualization_point?.[p.name]);
      if (paramVals.some(v => v === undefined)) return;

      const score = result.overall_score;
      if (score === undefined) return;

      // Map to grid coordinates (-1 to 1)
      const gridPos = paramVals.map((val, i) => {
        const normalized = (val! - ranges[i].min) / ranges[i].span;
        return (normalized - 0.5) * 2;
      });

      voxels.push({
        position: new THREE.Vector3(gridPos[0], gridPos[1], gridPos[2]),
        score,
        isFeasible: score >= scoreThreshold
      });
    });

    return {
      voxels,
      bounds: {
        params,
        ranges
      }
    };
  }, [parameterSchema, explorationHistory, scoreThreshold]);

  const feasibleCount = voxelData.voxels.filter(v => v.isFeasible).length;
  const totalCount = voxelData.voxels.length;
  const feasibilityRatio = totalCount > 0 ? (feasibleCount / totalCount) * 100 : 0;

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a' }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        3D feasibility volume: Green = feasible (score ≥ threshold), Red = infeasible. Adjust threshold below.
      </Typography>

      {explorationHistory.length < 5 && (
        <Typography variant="caption" color="warning.main" sx={{ mb: 1 }}>
          ⚠️ Limited data ({explorationHistory.length} configurations). Explore more for accurate volume.
        </Typography>
      )}

      {/* Score threshold slider */}
      <Box sx={{ mb: 2, px: 2 }}>
        <FormControl fullWidth>
          <InputLabel shrink>
            Feasibility Threshold: {scoreThreshold}
          </InputLabel>
          <Slider
            value={scoreThreshold}
            onChange={(_, val) => setScoreThreshold(val as number)}
            min={0}
            max={100}
            step={5}
            marks={[
              { value: 0, label: '0' },
              { value: 50, label: '50' },
              { value: 100, label: '100' }
            ]}
            valueLabelDisplay="auto"
            sx={{ mt: 3 }}
          />
        </FormControl>
      </Box>

      {/* Stats */}
      <Typography variant="caption" color="text.secondary" sx={{ mb: 1, textAlign: 'center' }}>
        Feasibility: {feasibleCount}/{totalCount} points ({feasibilityRatio.toFixed(1)}%)
      </Typography>

      <Box sx={{ flex: 1, position: 'relative' }}>
        {voxelData.voxels.length > 0 && voxelData.bounds ? (
        <Canvas camera={{ position: [3, 3, 3], fov: 60 }} style={{ background: '#0a0a0a' }}>
            <ambientLight intensity={0.6} />
            <pointLight position={[10, 10, 10]} intensity={0.8} />
            <pointLight position={[-10, -10, -10]} intensity={0.3} />

            <OrbitControls />

            {/* Bounding box */}
            <lineSegments>
              <edgesGeometry args={[new THREE.BoxGeometry(2, 2, 2)]} />
              <lineBasicMaterial color="#666666" />
            </lineSegments>

            {/* Voxels */}
            {voxelData.voxels.map((voxel, i) => (
              <mesh key={i} position={voxel.position}>
                <boxGeometry args={[0.15, 0.15, 0.15]} />
                <meshStandardMaterial 
                  color={voxel.isFeasible ? '#4caf50' : '#f44336'}
                  transparent
                  opacity={voxel.isFeasible ? 0.7 : 0.3}
                  emissive={voxel.isFeasible ? '#4caf50' : '#f44336'}
                  emissiveIntensity={0.2}
                />
              </mesh>
            ))}

            {/* Current point (highlighted) */}
            {(() => {
              const params = voxelData.bounds.params;
              const ranges = voxelData.bounds.ranges;
              const currentVals = params.map(p => inputs[p.name] || ((p.min + p.max) / 2));
              
              const gridPos = currentVals.map((val, i) => {
                const normalized = (val - ranges[i].min) / ranges[i].span;
                return (normalized - 0.5) * 2;
              });

              return (
                <mesh position={new THREE.Vector3(gridPos[0], gridPos[1], gridPos[2])}>
                  <sphereGeometry args={[0.12, 16, 16]} />
                  <meshStandardMaterial 
                    color="#ff5722"
                    emissive="#ff5722"
                    emissiveIntensity={0.5}
                  />
                </mesh>
              );
            })()}

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
              Not enough data. Explore parameter space to build feasibility volume.
            </Typography>
          </Box>
        )}
      </Box>

      {voxelData.bounds && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
          Axes: {voxelData.bounds.params.map(p => p.display_name || p.name).join(' × ')}
        </Typography>
      )}
    </Box>
  );
};

export default FeasibilityVolume;
