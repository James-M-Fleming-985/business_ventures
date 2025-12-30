import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { Box, Typography } from '@mui/material';
import * as THREE from 'three';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface ParetoFrontierProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Pareto Frontier - 3D scatter plot showing trade-offs
 * Visualizes performance/economic/durability scores to identify optimal solutions
 */
const ParetoFrontier: React.FC<ParetoFrontierProps> = ({
  calculationResult,
  explorationHistory
}) => {
  // Convert scores to 3D points
  const points = useMemo(() => {
    const allResults = [...explorationHistory, calculationResult];
    return allResults.map(result => {
      const { performance_score = 50, economic_score = 50, durability_score = 50 } = 
        result.composites || {};
      
      return {
        position: new THREE.Vector3(
          (performance_score - 50) / 50,  // Scale to -1 to +1
          (economic_score - 50) / 50,
          (durability_score - 50) / 50
        ),
        scores: { performance_score, economic_score, durability_score },
        overall: result.overall_score,
        isCurrent: result === calculationResult
      };
    });
  }, [calculationResult, explorationHistory]);

  // Identify Pareto-optimal points (simplified: top 30% by overall score)
  const paretoPoints = useMemo(() => {
    const sorted = [...points].sort((a, b) => b.overall - a.overall);
    const threshold = sorted[Math.floor(sorted.length * 0.3)]?.overall || 0;
    return points.filter(p => p.overall >= threshold);
  }, [points]);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a' }}>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: [3, 3, 3], fov: 60 }} style={{ background: '#0a0a0a' }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={0.8} />
          <pointLight position={[-10, -10, -10]} intensity={0.3} />

          <OrbitControls 
            enableRotate={true}
            enableZoom={true}
            enablePan={true}
          />

          {/* Axis lines */}
          <primitive object={new THREE.AxesHelper(1.5)} />

          {/* Axis labels */}
          <Text position={[1.7, 0, 0]} fontSize={0.15} color="#1976d2">
            Performance
          </Text>
          <Text position={[0, 1.7, 0]} fontSize={0.15} color="#9c27b0">
            Economic
          </Text>
          <Text position={[0, 0, 1.7]} fontSize={0.15} color="#2e7d32">
            Durability
          </Text>

          {/* Reference planes at zero */}
          <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
            <planeGeometry args={[3, 3]} />
            <meshBasicMaterial color="#e0e0e0" opacity={0.1} transparent side={THREE.DoubleSide} />
          </mesh>

          {/* All points (history) */}
          {points.map((point, i) => {
            const isParetoOptimal = paretoPoints.includes(point);
            const color = point.isCurrent 
              ? '#ff5722'  // Current: orange
              : isParetoOptimal 
                ? '#ffd700' // Pareto: gold
                : '#888888'; // Others: gray

            const size = point.isCurrent ? 0.08 : isParetoOptimal ? 0.06 : 0.04;

            return (
              <mesh key={i} position={point.position}>
                <sphereGeometry args={[size, 16, 16]} />
                <meshStandardMaterial 
                  color={color}
                  emissive={point.isCurrent ? '#ff5722' : isParetoOptimal ? '#ffd700' : '#000000'}
                  emissiveIntensity={point.isCurrent ? 0.5 : isParetoOptimal ? 0.3 : 0}
                  transparent
                  opacity={point.isCurrent ? 1 : isParetoOptimal ? 0.9 : 0.5}
                />
              </mesh>
            );
          })}

          {/* Connect Pareto frontier points (optional - creates convex hull outline) */}
          {paretoPoints.length > 2 && paretoPoints.map((point, i) => {
            if (i === 0) return null;
            const prevPoint = paretoPoints[i - 1];
            
            const geometry = new THREE.BufferGeometry().setFromPoints([
              prevPoint.position,
              point.position
            ]);
            
            return (
              <primitive 
                key={`line-${i}`} 
                object={new THREE.Line(
                  geometry,
                  new THREE.LineBasicMaterial({ color: '#ffd700', opacity: 0.3, transparent: true })
                )}
              />
            );
          })}

          {/* Origin sphere */}
          <mesh position={[0, 0, 0]}>
            <sphereGeometry args={[0.03, 16, 16]} />
            <meshStandardMaterial color="#666666" />
          </mesh>
        </Canvas>
      </Box>

      <Box display="flex" gap={2} mt={1} justifyContent="center">
        <Typography variant="caption" color="text.secondary">
          🔴 Current
        </Typography>
        <Typography variant="caption" color="text.secondary">
          🟡 Pareto-Optimal ({paretoPoints.length})
        </Typography>
        <Typography variant="caption" color="text.secondary">
          ⚫ Others ({points.length - paretoPoints.length})
        </Typography>
      </Box>
    </Box>
  );
};

export default ParetoFrontier;
