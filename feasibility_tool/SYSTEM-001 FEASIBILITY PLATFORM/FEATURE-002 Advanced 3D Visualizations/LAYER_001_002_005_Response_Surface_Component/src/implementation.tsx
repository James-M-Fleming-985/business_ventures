```tsx
import React, { useState, useMemo, useRef, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { OrbitControls } from '@react-three/drei';

/**
 * Input variable names for the response surface
 */
const INPUT_VARIABLES = [
  'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x10', 'x11', 'x12', 'x13'
] as const;

type InputVariable = typeof INPUT_VARIABLES[number];

interface ResponseSurfaceProps {
  /**
   * Function to compute response value for given inputs
   */
  computeResponse?: (inputs: Record<string, number>) => number;
  /**
   * Current input values
   */
  currentInputs?: Record<string, number>;
  /**
   * Grid resolution (default: 30)
   */
  gridSize?: number;
}

interface SurfaceGeometry {
  positions: Float32Array;
  colors: Float32Array;
  indices: Uint32Array;
}

/**
 * Computes surface geometry and colors for the response surface
 */
function computeSurfaceGeometry(
  xVar: InputVariable,
  yVar: InputVariable,
  gridSize: number,
  currentInputs: Record<string, number>,
  computeResponse: (inputs: Record<string, number>) => number
): SurfaceGeometry {
  const positions = new Float32Array(gridSize * gridSize * 3);
  const colors = new Float32Array(gridSize * gridSize * 3);
  const indices: number[] = [];

  let minZ = Infinity;
  let maxZ = -Infinity;
  const zValues: number[] = [];

  // Compute Z values and find min/max
  for (let i = 0; i < gridSize; i++) {
    for (let j = 0; j < gridSize; j++) {
      const x = (i / (gridSize - 1)) * 2 - 1;
      const y = (j / (gridSize - 1)) * 2 - 1;
      
      const inputs = { ...currentInputs };
      inputs[xVar] = x;
      inputs[yVar] = y;
      
      const z = computeResponse(inputs);
      zValues.push(z);
      minZ = Math.min(minZ, z);
      maxZ = Math.max(maxZ, z);
    }
  }

  // Normalize Z values and create positions/colors
  const zRange = maxZ - minZ || 1;
  
  for (let i = 0; i < gridSize; i++) {
    for (let j = 0; j < gridSize; j++) {
      const idx = i * gridSize + j;
      const x = (i / (gridSize - 1)) * 2 - 1;
      const y = (j / (gridSize - 1)) * 2 - 1;
      const z = (zValues[idx] - minZ) / zRange;
      
      positions[idx * 3] = x;
      positions[idx * 3 + 1] = y;
      positions[idx * 3 + 2] = z;
      
      // Heat map coloring (blue -> green -> red)
      const hue = (1.0 - z) * 240 / 360;
      const color = new THREE.Color().setHSL(hue, 1.0, 0.5);
      colors[idx * 3] = color.r;
      colors[idx * 3 + 1] = color.g;
      colors[idx * 3 + 2] = color.b;
    }
  }

  // Create indices for triangles
  for (let i = 0; i < gridSize - 1; i++) {
    for (let j = 0; j < gridSize - 1; j++) {
      const topLeft = i * gridSize + j;
      const topRight = topLeft + 1;
      const bottomLeft = (i + 1) * gridSize + j;
      const bottomRight = bottomLeft + 1;
      
      indices.push(topLeft, bottomLeft, topRight);
      indices.push(bottomLeft, bottomRight, topRight);
    }
  }

  return {
    positions,
    colors,
    indices: new Uint32Array(indices)
  };
}

/**
 * Surface mesh component for rendering the response surface
 */
const SurfaceMesh: React.FC<{
  xVar: InputVariable;
  yVar: InputVariable;
  gridSize: number;
  currentInputs: Record<string, number>;
  computeResponse: (inputs: Record<string, number>) => number;
}> = ({ xVar, yVar, gridSize, currentInputs, computeResponse }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const geometryRef = useRef<THREE.BufferGeometry>(null);

  const targetGeometry = useMemo(() => {
    const startTime = performance.now();
    const geometry = computeSurfaceGeometry(xVar, yVar, gridSize, currentInputs, computeResponse);
    const endTime = performance.now();
    
    // Ensure computation takes less than 1 second
    if (endTime - startTime > 1000) {
      console.warn(`Surface computation took ${endTime - startTime}ms`);
    }
    
    return geometry;
  }, [xVar, yVar, gridSize, currentInputs, computeResponse]);

  useFrame(() => {
    if (!geometryRef.current) return;
    
    const positions = geometryRef.current.attributes.position.array as Float32Array;
    const colors = geometryRef.current.attributes.color.array as Float32Array;
    const targetPositions = targetGeometry.positions;
    const targetColors = targetGeometry.colors;
    
    // Smooth morphing
    for (let i = 0; i < positions.length; i++) {
      positions[i] += (targetPositions[i] - positions[i]) * 0.1;
      colors[i] += (targetColors[i] - colors[i]) * 0.1;
    }
    
    geometryRef.current.attributes.position.needsUpdate = true;
    geometryRef.current.attributes.color.needsUpdate = true;
  });

  return (
    <mesh ref={meshRef}>
      <bufferGeometry ref={geometryRef}>
        <bufferAttribute
          attach="attributes-position"
          count={gridSize * gridSize}
          array={targetGeometry.positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={gridSize * gridSize}
          array={targetGeometry.colors}
          itemSize={3}
        />
        <bufferAttribute
          attach="index"
          count={targetGeometry.indices.length}
          array={targetGeometry.indices}
          itemSize={1}
        />
      </bufferGeometry>
      <meshBasicMaterial vertexColors side={THREE.DoubleSide} />
    </mesh>
  );
};

/**
 * Current point indicator component
 */
const CurrentPointIndicator: React.FC<{
  xVar: InputVariable;
  yVar: InputVariable;
  currentInputs: Record<string, number>;
  computeResponse: (inputs: Record<string, number>) => number;
}> = ({ xVar, yVar, currentInputs, computeResponse }) => {
  const x = currentInputs[xVar] || 0;
  const y = currentInputs[yVar] || 0;
  const z = computeResponse(currentInputs);
  
  // Normalize z to [0, 1] range for visualization
  const normalizedZ = Math.max(0, Math.min(1, z));
  
  return (
    <group position={[x, y, 0]}>
      <mesh>
        <cylinderGeometry args={[0.02, 0.02, 2, 8]} />
        <meshBasicMaterial color="yellow" />
      </mesh>
    </group>
  );
};

/**
 * Main Response Surface Component
 */
const ResponseSurfaceComponent: React.FC<ResponseSurfaceProps> = ({
  computeResponse = (inputs) => {
    // Default implementation: simple quadratic response
    let sum = 0;
    for (const key in inputs) {
      sum += inputs[key] * inputs[key];
    }
    return sum / Object.keys(inputs).length;
  },
  currentInputs = INPUT_VARIABLES.reduce((acc, v) => ({ ...acc, [v]: 0 }), {}),
  gridSize = 30
}) => {
  const [xVariable, setXVariable] = useState<InputVariable>('x1');
  const [yVariable, setYVariable] = useState<InputVariable>('x2');

  const handleXChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setXVariable(event.target.value as InputVariable);
  }, []);

  const handleYChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setYVariable(event.target.value as InputVariable);
  }, []);

  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px', backgroundColor: '#f0f0f0', display: 'flex', gap: '20px' }}>
        <label>
          X Variable:
          <select value={xVariable} onChange={handleXChange} style={{ marginLeft: '10px' }}>
            {INPUT_VARIABLES.map(variable => (
              <option key={variable} value={variable}>
                {variable}
              </option>
            ))}
          </select>
        </label>
        <label>
          Y Variable:
          <select value={yVariable} onChange={handleYChange} style={{ marginLeft: '10px' }}>
            {INPUT_VARIABLES.map(variable => (
              <option key={variable} value={variable}>
                {variable}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div style={{ flex: 1 }}>
        <Canvas camera={{ position: [2, 2, 2], fov: 45 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <SurfaceMesh
            xVar={xVariable}
            yVar={yVariable}
            gridSize={gridSize}
            currentInputs={currentInputs}
            computeResponse={computeResponse}
          />
          <CurrentPointIndicator
            xVar={xVariable}
            yVar={yVariable}
            currentInputs={currentInputs}
            computeResponse={computeResponse}
          />
          <OrbitControls />
          <gridHelper args={[2, 10]} rotation={[Math.PI / 2, 0, 0]} />
        </Canvas>
      </div>
    </div>
  );
};

export default ResponseSurfaceComponent;
```