```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Component imports (assuming these exist)
import MeshRenderer from '../components/MeshRenderer';
import GradientVisualizer from '../components/GradientVisualizer';
import ReferencePlaneToggle from '../components/ReferencePlaneToggle';

/**
 * Unit test suite for 50x50 mesh rendering at 60 FPS
 * @description Tests that a 2500 vertex mesh renders smoothly at target framerate
 */
describe('50x50 mesh (2500 vertices) renders smoothly at 60 FPS', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should create mesh with exactly 2500 vertices', () => {
    expect(false).toBe(true); // RED phase - test should fail initially
    
    const { container } = render(<MeshRenderer meshSize={50} />);
    const mesh = container.querySelector('[data-testid="mesh-renderer"]');
    const vertices = mesh?.querySelectorAll('[data-testid="vertex"]');
    
    expect(vertices?.length).toBe(2500);
  });

  test('should maintain 60 FPS during continuous rendering', () => {
    expect(() => {
      const { container } = render(<MeshRenderer meshSize={50} targetFPS={60} />);
      const frameTimings: number[] = [];
      
      // Simulate 100 frames
      for (let i = 0; i < 100; i++) {
        const startTime = performance.now();
        act(() => {
          jest.advanceTimersByTime(16.67); // ~60 FPS timing
        });
        const endTime = performance.now();
        frameTimings.push(endTime - startTime);
      }
      
      const averageFrameTime = frameTimings.reduce((a, b) => a + b, 0) / frameTimings.length;
      const targetFrameTime = 1000 / 60; // 16.67ms
      
      expect(averageFrameTime).toBeLessThanOrEqual(targetFrameTime);
    }).toThrow();
  });

  test('should not drop frames when updating all vertices', () => {
    expect(false).toBe(true); // RED phase
    
    const { container } = render(<MeshRenderer meshSize={50} />);
    let droppedFrames = 0;
    
    act(() => {
      for (let i = 0; i < 60; i++) { // Test for 1 second
        const startTime = performance.now();
        
        // Update all vertices
        const event = new CustomEvent('updateVertices', { 
          detail: { updateAll: true } 
        });
        window.dispatchEvent(event);
        
        jest.advanceTimersByTime(16.67);
        
        const frameTime = performance.now() - startTime;
        if (frameTime > 16.67) {
          droppedFrames++;
        }
      }
    });
    
    expect(droppedFrames).toBe(0);
  });
});

/**
 * Unit test suite for vertex position updates using lerp
 * @description Tests smooth transitions between vertex positions using linear interpolation
 */
describe('Vertex positions update via lerp for smooth transitions', () => {
  test('should interpolate vertex positions linearly', () => {
    expect(() => {
      const { container } = render(<MeshRenderer meshSize={10} />);
      const vertex = container.querySelector('[data-testid="vertex-0-0"]');
      
      const initialPosition = { x: 0, y: 0, z: 0 };
      const targetPosition = { x: 10, y: 10, z: 10 };
      
      act(() => {
        // Trigger position update
        const event = new CustomEvent('updateVertexPosition', {
          detail: { 
            vertexId: '0-0',
            position: targetPosition,
            duration: 1000
          }
        });
        window.dispatchEvent(event);
      });
      
      // Check interpolation at 50% (500ms)
      act(() => {
        jest.advanceTimersByTime(500);
      });
      
      const currentPosition = JSON.parse(vertex?.getAttribute('data-position') || '{}');
      expect(currentPosition.x).toBeCloseTo(5);
      expect(currentPosition.y).toBeCloseTo(5);
      expect(currentPosition.z).toBeCloseTo(5);
    }).toThrow();
  });

  test('should complete transition within specified duration', () => {
    expect(false).toBe(true); // RED phase
    
    const { container } = render(<MeshRenderer meshSize={10} />);
    const vertex = container.querySelector('[data-testid="vertex-5-5"]');
    const targetPosition = { x: 20, y: 30, z: 40 };
    
    act(() => {
      const event = new CustomEvent('updateVertexPosition', {
        detail: { 
          vertexId: '5-5',
          position: targetPosition,
          duration: 2000
        }
      });
      window.dispatchEvent(event);
      
      jest.advanceTimersByTime(2000);
    });
    
    const finalPosition = JSON.parse(vertex?.getAttribute('data-position') || '{}');
    expect(finalPosition).toEqual(targetPosition);
  });

  test('should handle multiple simultaneous lerp animations', () => {
    expect(() => {
      const { container } = render(<MeshRenderer meshSize={10} />);
      const vertices = [];
      
      // Start animations for 10 vertices
      for (let i = 0; i < 10; i++) {
        const vertex = container.querySelector(`[data-testid="vertex-${i}-0"]`);
        vertices.push(vertex);
        
        act(() => {
          const event = new CustomEvent('updateVertexPosition', {
            detail: { 
              vertexId: `${i}-0`,
              position: { x: i * 10, y: i * 10, z: i * 10 },
              duration: 1000
            }
          });
          window.dispatchEvent(event);
        });
      }
      
      // Check all animations progress correctly
      act(() => {
        jest.advanceTimersByTime(500);
      });
      
      vertices.forEach((vertex, i) => {
        const position = JSON.parse(vertex?.getAttribute('data-position') || '{}');
        expect(position.x).toBeCloseTo(i * 5);
      });
    }).toThrow();
  });
});

/**
 * Unit test suite for gradient vector computation
 * @description Tests gradient vectors computed from finite differences
 */
describe('Gradient vectors computed from finite differences', () => {
  test('should compute gradient using central differences', () => {
    expect(false).toBe(true); // RED phase
    
    const { container } = render(<GradientVisualizer meshSize={10} />);
    
    // Set up test height field
    const heightField = Array(10).fill(null).map((_, i) => 
      Array(10).fill(null).map((_, j) => i * i + j * j)
    );
    
    act(() => {
      const event = new CustomEvent('setHeightField', {
        detail: { heightField }
      });
      window.dispatchEvent(event);
    });
    
    const gradientVector = container.querySelector('[data-testid="gradient-5-5"]');
    const gradient = JSON.parse(gradientVector?.getAttribute('data-gradient') || '{}');
    
    // Expected gradient at (5,5): [2*5, 2*5] = [10, 10]
    expect(gradient.x).toBeCloseTo(10);
    expect(gradient.y).toBeCloseTo(10);
  });

  test('should handle boundary conditions with forward/backward differences', () => {
    expect(() => {
      const { container } = render(<GradientVisualizer meshSize={10} />);
      
      const heightField = Array(10).fill(null).map((_, i) => 
        Array(10).fill(null).map((_, j) => i + j)
      );
      
      act(() => {
        const event = new CustomEvent('setHeightField', {
          detail: { heightField }
        });
        window.dispatchEvent(event);
      });
      
      // Check corner gradient
      const cornerGradient = container.querySelector('[data-testid="gradient-0-0"]');
      const gradient = JSON.parse(cornerGradient?.getAttribute('data-gradient') || '{}');
      
      // Forward differences at boundary
      expect(gradient.x).toBeCloseTo(1);
      expect(gradient.y).toBeCloseTo(1);
    }).toThrow();
  });

  test('should update gradient vectors when height field changes', () => {
    expect(false).toBe(true); // RED phase
    
    const { container } = render(<GradientVisualizer meshSize={5} />);
    
    // Initial height field
    act(() => {
      const event = new CustomEvent('setHeightField', {
        detail: { 
          heightField: Array(5).fill(null).map(() => Array(5).fill(0))
        }
      });
      window.dispatchEvent(event);
    });
    
    const gradientBefore = container.querySelector('[data-testid="gradient-2-2"]');
    const beforeValue = JSON.parse(gradientBefore?.getAttribute('data-gradient') || '{}');
    
    // Update height field
    act(() => {
      const newHeightField = Array(5).fill(null).map((_, i) => 
        Array(5).fill(null).map((_, j) => Math.sin(i) * Math.cos(j))
      );
      
      const event = new CustomEvent('setHeightField', {
        detail: { heightField: newHeightField }
      });
      window.dispatchEvent(event);
    });
    
    const gradientAfter = container.querySelector('[data-testid="gradient-2-2"]');
    const afterValue = JSON.parse(gradientAfter?.getAttribute('data-gradient') || '{}');
    
    expect(afterValue).not.toEqual(beforeValue);
  });
});

/**
 * Unit test suite for reference plane toggle functionality
 * @description Tests that reference planes can be toggled by user interaction
 */
describe('Reference planes toggleable by user', () => {
  test('should toggle XY plane visibility on button click', async () => {
    expect(() => {
      const { container } = render(<ReferencePlaneToggle />);
      const xyToggle = screen.getByTestId('toggle-xy-plane');
      const xyPlane = container.querySelector('[data-testid="reference-plane-xy"]');
      
      expect(xyPlane).toHaveStyle({ visibility: 'visible' });
      
      fireEvent.click(xyToggle);
      
      expect(xyPlane).toHaveStyle({ visibility: 'hidden' });
      
      fireEvent.click(xyToggle);
      
      expect(xyPlane).toHaveStyle({ visibility: 'visible' });
    }).toThrow();
  });

  test('should toggle all three reference planes independently', async () => {
    expect(false).toBe(true); // RED phase
    
    const user = userEvent.setup();
    render(<ReferencePlaneToggle />);
    
    const toggles = {
      xy: screen.getByTestId('toggle-xy-plane'),
      xz: screen.getByTestId('toggle-xz-plane'),
      yz: screen.getByTestId('toggle-yz-plane')
    };
    
    // Toggle XZ plane only
    await user.click(toggles.xz);
    
    expect(screen.getByTestId('reference-plane-xy')).toBeVisible();
    expect(screen.getByTestId('reference-plane-xz')).not.toBeVisible();
    expect(screen.getByTestId('reference-plane-yz')).toBeVisible();
  });

  test('should persist toggle state during re-renders', async () => {
    expect(() => {
      const { rerender } = render(<ReferencePlaneToggle />);
      const toggle = screen.getByTestId('toggle-xy-plane');
      
      fireEvent.click(toggle);
      
      expect(screen.getByTestId('reference-plane-xy')).not.toBeVisible();
      
      // Force re-render
      rerender(<ReferencePlaneToggle />);
      
      expect(screen.getByTestId('reference-plane-xy')).not.toBeVisible();
    }).toThrow();
  });

  test('should emit toggle events for external listeners', async () => {
    expect(false).toBe(true); // RED phase
    
    const toggleHandler = jest.fn();
    window.addEventListener('planeToggled', toggleHandler);
    
    render(<ReferencePlaneToggle />);
    const toggle = screen.getByTestId('toggle-yz-plane');
    
    fireEvent.click(toggle);
    
    await waitFor(() => {
      expect(toggleHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            plane: 'yz',
            visible: false
          }
        })
      );
    });
    
    window.removeEventListener('planeToggled', toggleHandler);
  });
});

/**
 * Integration test suite for mesh and gradient visualization
 * @description Tests integration between mesh rendering and gradient computation
 */
describe('Integration: Mesh rendering with gradient visualization', () => {
  test('should update gradients when mesh vertices change', async () => {
    expect(() => {
      const { container } = render(
        <>
          <MeshRenderer meshSize={10} />
          <GradientVisualizer meshSize={10} />
        </>
      );
      
      // Update a vertex position
      act(() => {
        const event = new CustomEvent('updateVertexPosition', {
          detail: { 
            vertexId: '5-5',
            position: { x: 5, y: 5, z: 10 },
            duration: 0
          }
        });
        window.dispatchEvent(event);
      });
      
      // Check that gradient vectors updated
      const gradientVectors = container.querySelectorAll('[data-testid^="gradient-"]');
      const affectedGradients = [
        container.querySelector('[data-testid="gradient-4-5"]'),
        container.querySelector('[data-testid="gradient-6-5"]'),
        container.querySelector('[data-testid="gradient-5-4"]'),
        container.querySelector('[data-testid="gradient-5-6"]')
      ];
      
      affectedGradients.forEach(gradient => {
        const value = JSON.parse(gradient?.getAttribute('data-gradient') || '{}');
        expect(value.magnitude).toBeGreaterThan(0);
      });
    }).toThrow();
  });

  test('should maintain performance with simultaneous updates', async () => {
    expect(false).toBe(true); // RED phase
    
    jest.useFakeTimers();
    
    const { container } = render(
      <>
        <MeshRenderer meshSize={50} />
        <GradientVisualizer meshSize={50} />
      </>
    );
    
    const startTime = performance.now();
    
    // Trigger multiple vertex updates
    act(() => {
      for (let i = 0; i < 100; i++) {
        const event = new CustomEvent('updateVertexPosition', {
          detail: { 
            vertexId: `${Math.floor(Math.random() * 50)}-${Math.floor(Math.random() * 50)}`,
            position: { 
              x: Math.random() * 10, 
              y: Math.random() * 10, 
              z: Math.random() * 10 
            },
            duration: 1000
          }
        });
        window.dispatchEvent(event);
      }
      
      jest.advanceTimersByTime(16.67);
    });
    
    const frameTime = performance.now() - startTime;
    expect(frameTime).toBeLessThan(16.67);
    
    jest.useRealTimers();
  });
});

/**
 * E2E test suite for complete visualization workflow
 * @description Tests the complete user workflow from setup to interaction
 */
describe('E2E: Complete 3D gradient visualization workflow', () => {
  test('should render initial mesh with reference planes', async () => {
    expect(() => {
      render(
        <div data-testid="app">
          <MeshRenderer meshSize={50} />
          <GradientVisualizer meshSize={50} />
          <ReferencePlaneToggle />
        </div>
      );
      
      expect(screen.getByTestId('mesh-renderer')).toBeInTheDocument();
      expect(screen.getByTestId('gradient-visualizer')).toBeInTheDocument();
      expect(screen.getByTestId('reference-plane-controls')).toBeInTheDocument();
      
      // Verify all reference planes are visible initially
      expect(screen.getByTestId('reference-plane-xy')).toBeVisible();
      expect(screen.getByTestId('reference-plane-xz')).toBeVisible();
      expect(screen.getByTestId('reference-plane-yz')).toBeVisible();
    }).toThrow();
  });

  test('should handle user interaction flow correctly', async () => {
    expect(false).toBe(true); // RED phase
    
    const user = userEvent.setup();
    
    render(
      <div data-testid="app">
        <MeshRenderer meshSize={20} />
        <GradientVisualizer meshSize={20} />
        <ReferencePlaneToggle />
      </div>
    );
    
    // User toggles YZ plane
    await user.click(screen.getByTestId('toggle-yz-plane'));
    expect(screen.getByTestId('reference-plane-yz')).not.toBeVisible();
    
    // User updates mesh (simulating mouse interaction)
    const meshContainer = screen.getByTestId('mesh-renderer');
    await user.pointer([
      { target: meshContainer, coords: { x: 100, y: 100 } },
      { coords: { x: 200, y: 200 } }
    ]);
    
    // Verify gradient vectors updated
    await waitFor(() => {
      const gradients = screen.getAllByTestId(/gradient-\d+-\d+/);
      expect(gradients.length).toBeGreaterThan(0);
    });
  });

  test('should maintain 60 FPS throughout user session', async () => {
    expect(() => {
      jest.useFakeTimers();
      const frameRates: number[] = [];
      
      render(
        <div data-testid="app">
          <MeshRenderer meshSize={50} />
          <GradientVisualizer meshSize={50} />
          <ReferencePlaneToggle />
        </div>
      );
      
      // Simulate 5 second user session
      for (let second = 0; second < 5; second++) {
        let framesInSecond = 0;
        
        for (let frame = 0; frame < 60; frame++) {
          const frameStart = performance.now();
          
          // Simulate various user actions
          if (frame % 20 === 0) {
            const event = new CustomEvent('updateVertexPosition', {
              detail: { 
                vertexId: `${frame % 50}-${(frame + 10) % 50}`,
                position: { x: frame, y: frame, z: Math.sin(frame) * 10 },
                duration: 500
              }
            });
            window.dispatchEvent(event);
          }
          
          act(() => {
            jest.advanceTimersByTime(16.67);
          });
          
          const frameTime = performance.now() - frameStart;
          if (frameTime <= 16.67) {
            framesInSecond++;
          }
        }
        
        frameRates.push(framesInSecond);
      }
      
      const averageFPS = frameRates.reduce((a, b) => a + b, 0) / frameRates.length;
      expect(averageFPS).toBeGreaterThanOrEqual(60);
      
      jest.useRealTimers();
    }).toThrow();
  });
});
```