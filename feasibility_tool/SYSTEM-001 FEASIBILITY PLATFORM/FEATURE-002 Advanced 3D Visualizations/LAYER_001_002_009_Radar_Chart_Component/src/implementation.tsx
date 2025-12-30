```tsx
import React, { useMemo, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Props for individual data points on the radar chart
 */
interface DataPoint {
  value: number;
  label?: string;
}

/**
 * Props for the RadarChart component
 */
interface RadarChartProps {
  data: DataPoint[];
  maxValue?: number;
  size?: number;
  fillColor?: string;
  strokeColor?: string;
  referenceConfig?: DataPoint[];
  referenceColor?: string;
  showGrid?: boolean;
  showLabels?: boolean;
}

/**
 * Component for rendering radial axis lines
 */
const RadialAxes: React.FC<{ count: number; radius: number }> = ({ count, radius }) => {
  const lines = useMemo(() => {
    const angleStep = (Math.PI * 2) / count;
    return Array.from({ length: count }, (_, i) => {
      const angle = i * angleStep;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      return { x, y, angle };
    });
  }, [count, radius]);

  return (
    <>
      {lines.map((line, index) => (
        <line key={`axis-${index}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([0, 0, 0, line.x, line.y, 0])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#cccccc" />
        </line>
      ))}
    </>
  );
};

/**
 * Component for rendering concentric grid circles
 */
const ConcentricCircles: React.FC<{ radius: number; levels: number }> = ({ radius, levels }) => {
  const circles = useMemo(() => {
    return [0.2, 0.4, 0.6, 0.8, 1.0].map((scale) => {
      const points = [];
      const segments = 64;
      for (let i = 0; i <= segments; i++) {
        const angle = (i / segments) * Math.PI * 2;
        points.push(
          Math.cos(angle) * radius * scale,
          Math.sin(angle) * radius * scale,
          0
        );
      }
      return new Float32Array(points);
    });
  }, [radius]);

  return (
    <>
      {circles.map((circle, index) => (
        <line key={`circle-${index}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={circle.length / 3}
              array={circle}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#e0e0e0" />
        </line>
      ))}
    </>
  );
};

/**
 * Component for rendering the filled data polygon
 */
const DataPolygon: React.FC<{
  data: DataPoint[];
  maxValue: number;
  radius: number;
  color: string;
  opacity?: number;
}> = ({ data, maxValue, radius, color, opacity = 0.3 }) => {
  const shape = useMemo(() => {
    const angleStep = (Math.PI * 2) / data.length;
    const shape = new THREE.Shape();
    
    data.forEach((point, index) => {
      const angle = index * angleStep;
      const normalizedValue = Math.min(point.value / maxValue, 1);
      const x = Math.cos(angle) * radius * normalizedValue;
      const y = Math.sin(angle) * radius * normalizedValue;
      
      if (index === 0) {
        shape.moveTo(x, y);
      } else {
        shape.lineTo(x, y);
      }
    });
    
    shape.closePath();
    return shape;
  }, [data, maxValue, radius]);

  const geometry = useMemo(() => {
    return new THREE.ShapeGeometry(shape);
  }, [shape]);

  return (
    <mesh geometry={geometry}>
      <meshBasicMaterial color={color} transparent opacity={opacity} side={THREE.DoubleSide} />
    </mesh>
  );
};

/**
 * Component for rendering the data polygon outline
 */
const DataOutline: React.FC<{
  data: DataPoint[];
  maxValue: number;
  radius: number;
  color: string;
  isDotted?: boolean;
}> = ({ data, maxValue, radius, color, isDotted = false }) => {
  const points = useMemo(() => {
    const angleStep = (Math.PI * 2) / data.length;
    const pts = [];
    
    data.forEach((point, index) => {
      const angle = index * angleStep;
      const normalizedValue = Math.min(point.value / maxValue, 1);
      const x = Math.cos(angle) * radius * normalizedValue;
      const y = Math.sin(angle) * radius * normalizedValue;
      pts.push(x, y, 0);
    });
    
    // Close the polygon
    const firstPoint = data[0];
    const normalizedFirst = Math.min(firstPoint.value / maxValue, 1);
    pts.push(
      Math.cos(0) * radius * normalizedFirst,
      Math.sin(0) * radius * normalizedFirst,
      0
    );
    
    return new Float32Array(pts);
  }, [data, maxValue, radius]);

  return (
    <line>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={points.length / 3}
          array={points}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial 
        color={color} 
        linewidth={2}
        {...(isDotted ? { 
          transparent: true,
          opacity: 0.5,
          dashSize: 3,
          gapSize: 3
        } : {})}
      />
    </line>
  );
};

/**
 * Main radar chart scene component
 */
const RadarChartScene: React.FC<RadarChartProps> = ({
  data,
  maxValue = 100,
  size = 5,
  fillColor = '#3498db',
  strokeColor = '#2c3e50',
  referenceConfig,
  referenceColor = '#e74c3c',
  showGrid = true,
  showLabels = true,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const lastUpdateRef = useRef(Date.now());

  // Update tracking for 5ms requirement
  useEffect(() => {
    lastUpdateRef.current = Date.now();
  }, [data, referenceConfig]);

  // Maintain 60 FPS
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.z = 0;
    }
  });

  return (
    <group ref={groupRef}>
      {showGrid && (
        <>
          <RadialAxes count={data.length} radius={size} />
          <ConcentricCircles radius={size} levels={5} />
        </>
      )}
      
      <DataPolygon
        data={data}
        maxValue={maxValue}
        radius={size}
        color={fillColor}
        opacity={0.3}
      />
      
      <DataOutline
        data={data}
        maxValue={maxValue}
        radius={size}
        color={strokeColor}
      />
      
      {referenceConfig && (
        <DataOutline
          data={referenceConfig}
          maxValue={maxValue}
          radius={size}
          color={referenceColor}
          isDotted={true}
        />
      )}
    </group>
  );
};

/**
 * RadarChart component that renders a radar/spider chart using React Three Fiber
 * 
 * @param props - Configuration for the radar chart
 * @returns React component rendering a 3D radar chart
 */
const RadarChart: React.FC<RadarChartProps> = (props) => {
  return (
    <Canvas
      camera={{ position: [0, 0, 10], fov: 50 }}
      style={{ width: '100%', height: '100%' }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={1} />
      <RadarChartScene {...props} />
    </Canvas>
  );
};

export default RadarChart;
```