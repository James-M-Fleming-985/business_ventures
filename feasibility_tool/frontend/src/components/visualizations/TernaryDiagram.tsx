import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import { Box, Typography } from '@mui/material';
import * as THREE from 'three';
import type { CalculationResult, ParameterSchema } from '../../types/visualization';

interface TernaryDiagramProps {
  calculationResult: CalculationResult;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

/**
 * Ternary Diagram - Visualizes 3 composite scores using barycentric coordinates
 * Maps performance/economic/durability scores to a triangular coordinate system
 */
const TernaryDiagram: React.FC<TernaryDiagramProps> = ({
  calculationResult,
  explorationHistory
}) => {
  // Convert scores (0-100) to barycentric coordinates
  const barycentricPoint = useMemo(() => {
    const { performance_score = 0, economic_score = 0, durability_score = 0 } = 
      calculationResult.composites || {};
    
    // Normalize scores to sum to 1
    const total = performance_score + economic_score + durability_score;
    if (total === 0) return new THREE.Vector3(0, 0, 0);
    
    const p = performance_score / total;
    const e = economic_score / total;
    const d = durability_score / total;
    
    // Convert to Cartesian coordinates (equilateral triangle)
    // Vertices: Performance (0, 1), Economic (-√3/2, -1/2), Durability (√3/2, -1/2)
    const x = (e * (-Math.sqrt(3) / 2) + d * (Math.sqrt(3) / 2));
    const y = (p * 1 + e * (-0.5) + d * (-0.5));
    
    return new THREE.Vector3(x, y, 0);
  }, [calculationResult]);

  // Convert history to barycentric points
  const historyPoints = useMemo(() => {
    return explorationHistory.map(result => {
      const { performance_score = 0, economic_score = 0, durability_score = 0 } = 
        result.composites || {};
      
      const total = performance_score + economic_score + durability_score;
      if (total === 0) return new THREE.Vector3(0, 0, 0);
      
      const p = performance_score / total;
      const e = economic_score / total;
      const d = durability_score / total;
      
      const x = (e * (-Math.sqrt(3) / 2) + d * (Math.sqrt(3) / 2));
      const y = (p * 1 + e * (-0.5) + d * (-0.5));
      
      return new THREE.Vector3(x, y, 0);
    });
  }, [explorationHistory]);

  // Triangle vertices
  const vertices = useMemo(() => [
    new THREE.Vector3(0, 1, 0),                    // Performance (top)
    new THREE.Vector3(-Math.sqrt(3) / 2, -0.5, 0), // Economic (bottom-left)
    new THREE.Vector3(Math.sqrt(3) / 2, -0.5, 0)   // Durability (bottom-right)
  ], []);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a' }}>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: [0, 0, 3], fov: 50 }} style={{ background: '#0a0a0a' }}>
          <ambientLight intensity={0.6} />
          <pointLight position={[10, 10, 10]} intensity={0.8} />
          
          <OrbitControls 
            enableRotate={true}
            enableZoom={true}
            enablePan={true}
            minDistance={1}
            maxDistance={5}
          />

          {/* Triangle outline */}
          <Line
            points={[...vertices, vertices[0]]} // Close the triangle
            color="#1976d2"
            lineWidth={2}
          />

          {/* Vertex labels */}
          <Text
            position={[0, 1.3, 0]}
            fontSize={0.15}
            color="#1976d2"
            anchorX="center"
            anchorY="middle"
          >
            Performance
          </Text>
          <Text
            position={[-Math.sqrt(3) / 2 - 0.3, -0.5, 0]}
            fontSize={0.15}
            color="#9c27b0"
            anchorX="center"
            anchorY="middle"
          >
            Economic
          </Text>
          <Text
            position={[Math.sqrt(3) / 2 + 0.3, -0.5, 0]}
            fontSize={0.15}
            color="#2e7d32"
            anchorX="center"
            anchorY="middle"
          >
            Durability
          </Text>

          {/* Grid lines (optional - shows 20%, 40%, 60%, 80% isolines) */}
          {[0.2, 0.4, 0.6, 0.8].map((t, i) => {
            // Lines parallel to each edge
            const performanceLines = [
              new THREE.Vector3(-Math.sqrt(3) / 2 * (1 - t), -0.5 + 1.5 * t, 0),
              new THREE.Vector3(Math.sqrt(3) / 2 * (1 - t), -0.5 + 1.5 * t, 0)
            ];
            
            return (
              <Line
                key={`grid-${i}`}
                points={performanceLines}
                color="#cccccc"
                lineWidth={0.5}
                opacity={0.3}
              />
            );
          })}

          {/* History trail (ghost points) */}
          {historyPoints.slice(-20).map((point, i) => (
            <mesh key={`history-${i}`} position={point}>
              <sphereGeometry args={[0.02, 16, 16]} />
              <meshStandardMaterial 
                color="#888888" 
                opacity={0.3 + (i / 20) * 0.4}
                transparent
              />
            </mesh>
          ))}

          {/* Current point (highlighted) */}
          <mesh position={barycentricPoint}>
            <sphereGeometry args={[0.05, 32, 32]} />
            <meshStandardMaterial color="#ff5722" emissive="#ff5722" emissiveIntensity={0.5} />
          </mesh>

          {/* Connecting line from current to center */}
          <Line
            points={[new THREE.Vector3(0, 0, 0), barycentricPoint]}
            color="#ff5722"
            lineWidth={1}
            opacity={0.6}
            dashed
            dashSize={0.05}
            gapSize={0.025}
          />

          {/* Center reference point */}
          <mesh position={[0, 0, 0]}>
            <sphereGeometry args={[0.015, 16, 16]} />
            <meshStandardMaterial color="#666666" />
          </mesh>
        </Canvas>
      </Box>
    </Box>
  );
};

export default TernaryDiagram;
