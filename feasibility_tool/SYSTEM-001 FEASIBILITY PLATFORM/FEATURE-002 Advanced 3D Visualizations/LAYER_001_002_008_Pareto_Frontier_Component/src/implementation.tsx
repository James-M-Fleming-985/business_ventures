```tsx
import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface ParetoFrontierComponentProps {
  objectives: Point3D[];
  currentPoint?: Point3D;
  onFrontierUpdate?: (frontier: Point3D[]) => void;
}

/**
 * Calculates the convex hull of 3D points using Graham's scan algorithm
 * @param points Array of 3D points
 * @returns Array of points forming the convex hull
 */
function computeConvexHull(points: Point3D[]): Point3D[] {
  if (points.length < 3) return points;

  // Project to 2D for simplicity (using x and y)
  const points2D = points.map(p => ({ x: p.x, y: p.y, original: p }));
  
  // Sort by x, then y
  points2D.sort((a, b) => a.x - b.x || a.y - b.y);

  // Cross product of vectors OA and OB
  const cross = (O: any, A: any, B: any) => {
    return (A.x - O.x) * (B.y - O.y) - (A.y - O.y) * (B.x - O.x);
  };

  // Build lower hull
  const lower: any[] = [];
  for (const p of points2D) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  // Build upper hull
  const upper: any[] = [];
  for (let i = points2D.length - 1; i >= 0; i--) {
    const p = points2D[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  // Remove duplicates
  upper.pop();
  lower.pop();
  
  return lower.concat(upper).map(p => p.original);
}

/**
 * Calculates the minimum distance from a point to the frontier
 * @param point Current point
 * @param frontier Array of frontier points
 * @returns Minimum distance to frontier
 */
function calculateDistanceToFrontier(point: Point3D, frontier: Point3D[]): number {
  if (frontier.length === 0) return Infinity;
  
  let minDistance = Infinity;
  
  for (let i = 0; i < frontier.length; i++) {
    const j = (i + 1) % frontier.length;
    const p1 = frontier[i];
    const p2 = frontier[j];
    
    // Distance from point to line segment p1-p2
    const A = point.x - p1.x;
    const B = point.y - p1.y;
    const C = point.z - p1.z;
    const D = p2.x - p1.x;
    const E = p2.y - p1.y;
    const F = p2.z - p1.z;
    
    const dot = A * D + B * E + C * F;
    const lenSq = D * D + E * E + F * F;
    let param = -1;
    
    if (lenSq !== 0) param = dot / lenSq;
    
    let xx, yy, zz;
    
    if (param < 0) {
      xx = p1.x;
      yy = p1.y;
      zz = p1.z;
    } else if (param > 1) {
      xx = p2.x;
      yy = p2.y;
      zz = p2.z;
    } else {
      xx = p1.x + param * D;
      yy = p1.y + param * E;
      zz = p1.z + param * F;
    }
    
    const dx = point.x - xx;
    const dy = point.y - yy;
    const dz = point.z - zz;
    const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
    
    minDistance = Math.min(minDistance, distance);
  }
  
  return minDistance;
}

/**
 * Generates sample points for the Pareto frontier
 * @param count Number of points to generate
 * @returns Array of sample points
 */
function generateSamplePoints(count: number): Point3D[] {
  const points: Point3D[] = [];
  
  for (let i = 0; i < count; i++) {
    const theta = (i / count) * Math.PI * 0.5;
    const phi = Math.random() * Math.PI * 0.5;
    
    points.push({
      x: Math.sin(theta) * Math.cos(phi),
      y: Math.sin(theta) * Math.sin(phi),
      z: Math.cos(theta)
    });
  }
  
  return points;
}

/**
 * Frontier visualization component
 */
const FrontierVisualization: React.FC<{
  frontier: Point3D[];
  currentPoint?: Point3D;
  distance: number;
}> = ({ frontier, currentPoint, distance }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const { camera } = useThree();

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.001;
    }
  });

  const frontierGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const vertices: number[] = [];
    
    frontier.forEach(point => {
      vertices.push(point.x, point.y, point.z);
    });
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.computeBoundingSphere();
    
    return geometry;
  }, [frontier]);

  return (
    <group>
      {/* Pareto Frontier */}
      <line>
        <bufferGeometry attach="geometry" {...frontierGeometry} />
        <lineBasicMaterial attach="material" color="#00ff00" linewidth={2} />
      </line>
      
      {/* Color zones */}
      <mesh ref={meshRef}>
        <planeGeometry args={[10, 10, 50, 50]} />
        <shaderMaterial
          uniforms={{
            distance: { value: distance },
            time: { value: 0 }
          }}
          vertexShader={`
            varying vec2 vUv;
            void main() {
              vUv = uv;
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `}
          fragmentShader={`
            uniform float distance;
            varying vec2 vUv;
            
            void main() {
              float d = length(vUv - vec2(0.5));
              vec3 color;
              
              if (distance < 0.1) {
                color = vec3(0.0, 1.0, 0.0); // Optimal - green
              } else if (distance < 0.3) {
                color = vec3(1.0, 1.0, 0.0); // Near optimal - yellow
              } else {
                color = vec3(1.0, 0.0, 0.0); // Sub-optimal - red
              }
              
              gl_FragColor = vec4(color, 0.3);
            }
          `}
          transparent
        />
      </mesh>
      
      {/* Current point */}
      {currentPoint && (
        <mesh position={[currentPoint.x, currentPoint.y, currentPoint.z]}>
          <sphereGeometry args={[0.05, 16, 16]} />
          <meshBasicMaterial color="#ff0000" />
        </mesh>
      )}
      
      {/* Distance display */}
      <group position={[0, 2, 0]}>
        <mesh>
          <planeGeometry args={[2, 0.5]} />
          <meshBasicMaterial color="#333333" opacity={0.8} transparent />
        </mesh>
      </group>
    </group>
  );
};

/**
 * Main Pareto Frontier Component
 * Visualizes Pareto frontier with convex hull computation and optimality zones
 */
const ParetoFrontierComponent: React.FC<ParetoFrontierComponentProps> = ({
  objectives,
  currentPoint,
  onFrontierUpdate
}) => {
  const [frontier, setFrontier] = useState<Point3D[]>([]);
  const [distance, setDistance] = useState<number>(0);
  const previousObjectivesRef = useRef<Point3D[]>([]);

  /**
   * Check if objectives have changed significantly (>10% delta)
   */
  const hasSignificantChange = useCallback((prev: Point3D[], curr: Point3D[]): boolean => {
    if (prev.length !== curr.length) return true;
    
    for (let i = 0; i < prev.length; i++) {
      const deltaX = Math.abs(prev[i].x - curr[i].x);
      const deltaY = Math.abs(prev[i].y - curr[i].y);
      const deltaZ = Math.abs(prev[i].z - curr[i].z);
      
      const maxPrev = Math.max(Math.abs(prev[i].x), Math.abs(prev[i].y), Math.abs(prev[i].z));
      const threshold = maxPrev * 0.1;
      
      if (deltaX > threshold || deltaY > threshold || deltaZ > threshold) {
        return true;
      }
    }
    
    return false;
  }, []);

  /**
   * Compute frontier when objectives change significantly
   */
  useEffect(() => {
    const shouldRecompute = objectives.length === 0 || 
      hasSignificantChange(previousObjectivesRef.current, objectives);
    
    if (shouldRecompute) {
      // Generate at least 30 sample points
      const sampleCount = Math.max(30, objectives.length);
      const samplePoints = objectives.length > 0 ? objectives : generateSamplePoints(sampleCount);
      
      // Compute convex hull
      const newFrontier = computeConvexHull(samplePoints);
      setFrontier(newFrontier);
      
      // Update reference
      previousObjectivesRef.current = [...objectives];
      
      // Notify parent
      if (onFrontierUpdate) {
        onFrontierUpdate(newFrontier);
      }
    }
  }, [objectives, hasSignificantChange, onFrontierUpdate]);

  /**
   * Calculate distance when current point or frontier changes
   */
  useEffect(() => {
    if (currentPoint && frontier.length > 0) {
      const dist = calculateDistanceToFrontier(currentPoint, frontier);
      setDistance(dist);
    }
  }, [currentPoint, frontier]);

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <Canvas
        camera={{ position: [3, 3, 3], fov: 75 }}
        gl={{ antialias: true }}
        frameloop="always"
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <FrontierVisualization
          frontier={frontier}
          currentPoint={currentPoint}
          distance={distance}
        />
        <gridHelper args={[10, 10]} />
        <axesHelper args={[5]} />
      </Canvas>
      
      <div style={{
        position: 'absolute',
        top: 10,
        left: 10,
        background: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px'
      }}>
        <h3>Pareto Frontier Visualization</h3>
        <p>Frontier Points: {frontier.length}</p>
        {currentPoint && (
          <>
            <p>Current Point: ({currentPoint.x.toFixed(2)}, {currentPoint.y.toFixed(2)}, {currentPoint.z.toFixed(2)})</p>
            <p>Distance to Frontier: {distance.toFixed(3)}</p>
            <p>Optimality: {
              distance < 0.1 ? 'Optimal' :
              distance < 0.3 ? 'Near Optimal' :
              'Sub-optimal'
            }</p>
          </>
        )}
      </div>
    </div>
  );
};

export default ParetoFrontierComponent;
```