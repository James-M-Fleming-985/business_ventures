import { useState, useEffect, useMemo } from 'react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline, Box, Typography, Paper, Grid, Slider, Select, MenuItem, FormControl, Tooltip, IconButton, Accordion, AccordionSummary, AccordionDetails, Tabs, Tab, Drawer, List, ListItem, ListItemText, Divider, Button, Dialog, DialogTitle, DialogContent, DialogActions, Chip } from '@mui/material'
import { Info, ExpandMore, History, Bookmark, Close } from '@mui/icons-material'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Text, Html } from '@react-three/drei'
import axios from 'axios'
import * as THREE from 'three'
import EngineSelector from './components/EngineSelector'
import VisualizationModeSelector from './components/VisualizationModeSelector'

// Use VITE_API_URL and add protocol if missing (same as AuthContext)
let API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
if (API_BASE_URL && !API_BASE_URL.startsWith('http://') && !API_BASE_URL.startsWith('https://')) {
  API_BASE_URL = `https://${API_BASE_URL}`;
}
console.log('🔧 App API_BASE_URL:', API_BASE_URL);

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00bcd4' },
    secondary: { main: '#ff9800' },
  },
})

interface ParameterSchema {
  name: string
  display_name?: string
  type: string
  min_value?: number
  max_value?: number
  default: any
  unit: string
  description: string
  options?: string[]  // For dropdown/select inputs
}

interface ComponentResult {
  value: number
  unit: string
  formula: string
  calculation_steps: string[]
  normalized: number
}

interface CalculationResult {
  components: Record<string, ComponentResult>
  composites: Record<string, number>
  visualization_point: Record<string, number>
  overall_score: number
}

// 3D Delta Cube Visualization
function ProfileShapeVisualization({ 
  currentScores,
  baselineScores,
  brightness,
  result,
  baseline
}: { 
  currentScores: { performance: number; durability: number; economic: number } | null;
  baselineScores: { performance: number; durability: number; economic: number } | null;
  brightness: number;
  result: any;
  baseline: any;
}) {
  const [hoveredSphere, setHoveredSphere] = useState<string | null>(null);
  
  // Calculate deltas if baseline exists, otherwise use absolute scores
  const displayScores = useMemo(() => {
    if (!currentScores) return null
    
    if (baselineScores) {
      // Delta mode: show difference from baseline
      return {
        performance: currentScores.performance - baselineScores.performance,
        durability: currentScores.durability - baselineScores.durability,
        economic: currentScores.economic - baselineScores.economic
      }
    } else {
      // Absolute mode: center around 50
      return {
        performance: currentScores.performance - 50,
        durability: currentScores.durability - 50,
        economic: currentScores.economic - 50
      }
    }
  }, [currentScores, baselineScores])
  
  const [animatedScores, setAnimatedScores] = useState(displayScores)
  
  // Animate score changes
  useEffect(() => {
    if (displayScores) {
      setAnimatedScores(displayScores)
    }
  }, [displayScores])
  
  // Create triangular profile shape from deltas
  const profileGeometry = useMemo(() => {
    if (!animatedScores) return null
    
    const geometry = new THREE.BufferGeometry()
    
    // Deltas are already centered (can be -100 to +100)
    const perfPos = animatedScores.performance
    const durPos = animatedScores.durability
    const econPos = animatedScores.economic
    
    // Define vertices for the triangular profile
    const vertices = new Float32Array([
      // Triangle face
      perfPos, 0, 0,        // Performance vertex
      0, durPos, 0,         // Durability vertex  
      0, 0, econPos,        // Economic vertex
    ])
    
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3))
    geometry.computeVertexNormals()
    
    return geometry
  }, [animatedScores])
  
  // Create line geometry for profile edges
  const profileLines = useMemo(() => {
    if (!animatedScores) return null
    
    const perfPos = animatedScores.performance
    const durPos = animatedScores.durability
    const econPos = animatedScores.economic
    
    const points = [
      new THREE.Vector3(perfPos, 0, 0),
      new THREE.Vector3(0, durPos, 0),
      new THREE.Vector3(0, 0, econPos),
      new THREE.Vector3(perfPos, 0, 0), // Close the triangle
    ]
    
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [animatedScores])
  
  // Calculate color based on overall performance
  const profileColor = useMemo(() => {
    if (!animatedScores) return '#888'
    const avg = (animatedScores.performance + animatedScores.durability + animatedScores.economic) / 3
    if (avg < 40) return '#f44336'      // Red - poor
    if (avg < 60) return '#ff9800'      // Orange - moderate  
    if (avg < 80) return '#ffeb3b'      // Yellow - good
    return '#4caf50'                     // Green - excellent
  }, [animatedScores])

  return (
    <>
      {/* Profile Shape - Filled Triangle */}
      {profileGeometry && animatedScores && (
        <>
          <mesh geometry={profileGeometry}>
            <meshStandardMaterial 
              color={profileColor}
              transparent
              opacity={brightness * 0.7}
              side={THREE.DoubleSide}
            />
          </mesh>
          
          {/* Profile Wireframe - THICKER */}
          {profileLines && (
            <lineSegments geometry={profileLines}>
              <lineBasicMaterial color={profileColor} linewidth={5} />
            </lineSegments>
          )}
          
          {/* Vertex spheres at each score point with hover tooltips */}
          <mesh 
            position={[animatedScores.performance, 0, 0]}
            onPointerOver={(e) => { e.stopPropagation(); setHoveredSphere('performance'); }}
            onPointerOut={(e) => { e.stopPropagation(); setHoveredSphere(null); }}
          >
            <sphereGeometry args={[3, 32, 32]} />
            <meshStandardMaterial color="#00bcd4" emissive="#00bcd4" emissiveIntensity={hoveredSphere === 'performance' ? 2.0 : 1.2} />
          </mesh>
          <Text position={[animatedScores.performance, 8, 0]} fontSize={4} color="#00bcd4">
            {animatedScores.performance > 0 ? '+' : ''}{animatedScores.performance.toFixed(1)}
          </Text>
          {hoveredSphere === 'performance' && currentScores && (
            <Html position={[animatedScores.performance, 15, 0]}>
              <div style={{ 
                background: 'rgba(0, 188, 212, 0.95)', 
                color: 'white', 
                padding: '8px 12px', 
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
              }}>
                {baselineScores ? (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '12px' }}>ΔPerformance (EV)</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Current: {currentScores.performance.toFixed(1)}</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Baseline: {baselineScores.performance.toFixed(1)}</div>
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.3)', marginTop: '4px', paddingTop: '4px', fontSize: '10px' }}>
                      {currentScores.performance.toFixed(1)} - {baselineScores.performance.toFixed(1)} = <span style={{ fontWeight: 'bold', fontSize: '12px' }}>{(currentScores.performance - baselineScores.performance).toFixed(1)}</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Performance Score</div>
                    <div style={{ fontSize: '16px', marginBottom: '6px', color: '#fff', fontWeight: 'bold' }}>{currentScores.performance.toFixed(1)}/100</div>
                    <div style={{ fontSize: '9px', opacity: 0.7, marginBottom: '6px', fontStyle: 'italic' }}>
                      Position = {currentScores.performance.toFixed(1)} - 50 = {animatedScores.performance.toFixed(1)}
                    </div>
                    {result?.components && (
                      <>
                        <div style={{ fontSize: '9px', opacity: 0.8, marginTop: '6px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                          Based on: pressure drop, flow velocity, safety margin
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9, marginTop: '4px' }}>
                          Velocity: {result.components.velocity?.value.toFixed(2)} {result.components.velocity?.unit}
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9 }}>
                          Reynolds: {result.components.reynolds?.value.toFixed(0)}
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9 }}>
                          ΔP: {result.components.deltaP?.value.toFixed(2)} {result.components.deltaP?.unit}
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            </Html>
          )}
          
          <mesh 
            position={[0, animatedScores.durability, 0]}
            onPointerOver={(e) => { e.stopPropagation(); setHoveredSphere('durability'); }}
            onPointerOut={(e) => { e.stopPropagation(); setHoveredSphere(null); }}
          >
            <sphereGeometry args={[3, 32, 32]} />
            <meshStandardMaterial color="#4caf50" emissive="#4caf50" emissiveIntensity={hoveredSphere === 'durability' ? 2.0 : 1.2} />
          </mesh>
          <Text position={[0, animatedScores.durability + 8, 0]} fontSize={4} color="#4caf50">
            {animatedScores.durability > 0 ? '+' : ''}{animatedScores.durability.toFixed(1)}
          </Text>
          {hoveredSphere === 'durability' && currentScores && (
            <Html position={[0, animatedScores.durability + 15, 0]}>
              <div style={{ 
                background: 'rgba(76, 175, 80, 0.95)', 
                color: 'white', 
                padding: '8px 12px', 
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
              }}>
                {baselineScores ? (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '12px' }}>ΔDurability (EV)</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Current: {currentScores.durability.toFixed(1)}</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Baseline: {baselineScores.durability.toFixed(1)}</div>
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.3)', marginTop: '4px', paddingTop: '4px', fontSize: '10px' }}>
                      {currentScores.durability.toFixed(1)} - {baselineScores.durability.toFixed(1)} = <span style={{ fontWeight: 'bold', fontSize: '12px' }}>{(currentScores.durability - baselineScores.durability).toFixed(1)}</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Durability Score</div>
                    <div style={{ fontSize: '16px', marginBottom: '6px', color: '#fff', fontWeight: 'bold' }}>{currentScores.durability.toFixed(1)}/100</div>
                    <div style={{ fontSize: '9px', opacity: 0.7, marginBottom: '6px', fontStyle: 'italic' }}>
                      Position = {currentScores.durability.toFixed(1)} - 50 = {animatedScores.durability.toFixed(1)}
                    </div>
                    {result?.components?.deltaP && (
                      <>
                        <div style={{ fontSize: '9px', opacity: 0.8, marginTop: '6px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                          Based on: material properties, environment, stress
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9, marginTop: '4px' }}>
                          Pressure Drop: {result.components.deltaP.value.toFixed(2)} {result.components.deltaP.unit}
                        </div>
                        <div style={{ fontSize: '9px', opacity: 0.8, marginTop: '2px' }}>
                          (Lower ΔP = less material stress)
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            </Html>
          )}
          
          <mesh 
            position={[0, 0, animatedScores.economic]}
            onPointerOver={(e) => { e.stopPropagation(); setHoveredSphere('economic'); }}
            onPointerOut={(e) => { e.stopPropagation(); setHoveredSphere(null); }}
          >
            <sphereGeometry args={[3, 32, 32]} />
            <meshStandardMaterial color="#ff9800" emissive="#ff9800" emissiveIntensity={hoveredSphere === 'economic' ? 2.0 : 1.2} />
          </mesh>
          <Text position={[0, 8, animatedScores.economic]} fontSize={4} color="#ff9800">
            {animatedScores.economic > 0 ? '+' : ''}{animatedScores.economic.toFixed(1)}
          </Text>
          {hoveredSphere === 'economic' && currentScores && (
            <Html position={[0, 15, animatedScores.economic]}>
              <div style={{ 
                background: 'rgba(255, 152, 0, 0.95)', 
                color: 'white', 
                padding: '8px 12px', 
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
              }}>
                {baselineScores ? (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '12px' }}>ΔEconomic (EV)</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Current: {currentScores.economic.toFixed(1)}</div>
                    <div style={{ fontSize: '10px', opacity: 0.9 }}>Baseline: {baselineScores.economic.toFixed(1)}</div>
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.3)', marginTop: '4px', paddingTop: '4px', fontSize: '10px' }}>
                      {currentScores.economic.toFixed(1)} - {baselineScores.economic.toFixed(1)} = <span style={{ fontWeight: 'bold', fontSize: '12px' }}>{(currentScores.economic - baselineScores.economic).toFixed(1)}</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Economic Score</div>
                    <div style={{ fontSize: '16px', marginBottom: '6px', color: '#fff', fontWeight: 'bold' }}>{currentScores.economic.toFixed(1)}/100</div>
                    <div style={{ fontSize: '9px', opacity: 0.7, marginBottom: '6px', fontStyle: 'italic' }}>
                      Position = {currentScores.economic.toFixed(1)} - 50 = {animatedScores.economic.toFixed(1)}
                    </div>
                    {result?.components && (
                      <>
                        <div style={{ fontSize: '9px', opacity: 0.8, marginTop: '6px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                          Score = (1 - total/£20k) × 100
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9, marginTop: '4px' }}>
                          Material: £{result.components.material_cost?.value.toFixed(2)}
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.9 }}>
                          10yr Energy: £{(result.components.total_cost?.value - result.components.material_cost?.value).toFixed(2)}
                        </div>
                        <div style={{ fontSize: '11px', opacity: 1, marginTop: '2px', paddingTop: '2px', borderTop: '1px solid rgba(255,255,255,0.2)', fontWeight: 'bold' }}>
                          Total: £{result.components.total_cost?.value.toFixed(2)}
                        </div>
                        <div style={{ fontSize: '9px', opacity: 0.7, marginTop: '2px' }}>
                          (Lower is better)
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            </Html>
          )}
        </>
      )}
      
      {/* Axis Labels - Delta Cube Style */}
      <Text position={[55, -55, -55]} fontSize={3} color="#00bcd4">
        ΔPerformance →
      </Text>
      <Text position={[-55, 55, -55]} fontSize={3} color="#4caf50" rotation={[0, 0, Math.PI / 2]}>
        ↑ ΔDurability
      </Text>
      <Text position={[-55, -55, 55]} fontSize={3} color="#ff9800">
        ΔEconomic →
      </Text>
      
      {/* Origin marker (baseline = 0,0,0) */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[2, 16, 16]} />
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.8} />
      </mesh>
      <Text position={[0, -8, 0]} fontSize={2} color="#888">
        Baseline (0,0,0)
      </Text>
      
      {/* Grid */}
      <gridHelper args={[100, 20, '#333', '#222']} position={[0, -50, 0]} />
      
      {/* Axes */}
      <axesHelper args={[60]} />
      
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <pointLight position={[50, 50, 50]} intensity={1} />
      <pointLight position={[-50, -50, -50]} intensity={0.5} />
    </>
  )
}

interface ExplorationSnapshot {
  timestamp: number
  inputs: Record<string, any>
  result: CalculationResult
  label?: string
}

function App() {
  const [activeTab, setActiveTab] = useState(0)
  const [selectedEngineId, setSelectedEngineId] = useState('hose_optimization')
  const [inputSchema, setInputSchema] = useState<Record<string, ParameterSchema>>({})
  const [inputs, setInputs] = useState<Record<string, any>>({})
  const [result, setResult] = useState<CalculationResult | null>(null)
  const [baseline, setBaseline] = useState<{ inputs: Record<string, any>, result: CalculationResult } | null>(null)
  const [baselineModalOpen, setBaselineModalOpen] = useState(false)
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false)
  const [explorationHistory, setExplorationHistory] = useState<ExplorationSnapshot[]>([])
  const [visualizationMode, setVisualizationMode] = useState<string>('basic')
  const [targetProfile, setTargetProfile] = useState<string>('Balanced')
  const [surfaceBrightness, setSurfaceBrightness] = useState<number>(0.6)
  const [controlPanelWidth, setControlPanelWidth] = useState(350)
  const [calcDetailsOpen, setCalcDetailsOpen] = useState(true)
  const [calcDetailsPos, setCalcDetailsPos] = useState({ x: 20, y: 20 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [appVersion, setAppVersion] = useState<string>('loading...')

  // Fetch input schema
  useEffect(() => {
    console.log('Fetching input schema...')
    axios.get(`${API_BASE_URL}/api/engines/hose_optimization/input-schema`)
      .then(res => {
        console.log('Schema response:', res.data)
        if (res.data.success) {
          setInputSchema(res.data.data)
          const defaultInputs: Record<string, any> = {}  // Changed from number to any
          Object.entries(res.data.data).forEach(([key, param]: [string, any]) => {
            defaultInputs[key] = param.default
          })
          console.log('Default inputs:', defaultInputs)
          setInputs(defaultInputs)
        }
      })
      .catch(err => console.error('Failed to fetch schema:', err))
  }, [])

  // Fetch version information
  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/version`)
      .then(res => {
        if (res.data.success) {
          setAppVersion(`v${res.data.data.version}`)
        }
      })
      .catch(err => {
        console.error('Failed to fetch version:', err)
        // Fallback to package.json version
        setAppVersion('v1.1.0')
      })
  }, [])

  // Auto-calculate on input change - INSTANT, no debounce
  useEffect(() => {
    if (Object.keys(inputs).length === 0) return
    
    console.log('Inputs changed, calculating...', inputs)
    axios.post(`${API_BASE_URL}/api/engines/hose_optimization/calculate`, inputs)
      .then(res => {
        console.log('Calculation result:', res.data)
        if (res.data.success) {
          const data = res.data.data
          setResult(data)
          
          // Auto-log to exploration history
          setExplorationHistory(prev => {
            const newSnapshot: ExplorationSnapshot = {
              timestamp: Date.now(),
              inputs: { ...inputs },
              result: data
            }
            return [...prev, newSnapshot].slice(-100) // Keep last 100
          })
        }
      })
      .catch(err => console.error('Calculation failed:', err))
  }, [inputs])

  // Load target profile
  const handleProfileChange = (profile: string) => {
    setTargetProfile(profile)
    axios.get(`${API_BASE_URL}/api/engines/hose_optimization/target-profiles`)
      .then(res => {
        if (res.data.success) {
          setInputs(res.data.data[profile])
        }
      })
      .catch(err => console.error('Failed to load profile:', err))
  }

  // Set current config as baseline
  const handleSetBaseline = () => {
    if (result) {
      setBaseline({ inputs: { ...inputs }, result })
      setBaselineModalOpen(false)
    }
  }

  // Restore a snapshot from history
  const handleRestoreSnapshot = (snapshot: ExplorationSnapshot) => {
    setInputs(snapshot.inputs)
    setResult(snapshot.result)
    setHistoryDrawerOpen(false)
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* Baseline Configuration Dialog */}
      <Dialog 
        open={baselineModalOpen} 
        onClose={() => setBaselineModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Define Baseline Configuration
          <IconButton
            onClick={() => setBaselineModalOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter your current real-world system parameters. These will be used as the baseline to calculate ΔEV for all future configurations.
          </Typography>
          
          {baseline && (
            <Paper sx={{ p: 2, bgcolor: 'success.dark', mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>✓ Baseline Currently Set</Typography>
              <Typography variant="caption">
                P={baseline.result.composites.performance_score.toFixed(1)}, 
                E={baseline.result.composites.economic_score.toFixed(1)}, 
                D={baseline.result.composites.durability_score.toFixed(1)}
              </Typography>
            </Paper>
          )}
          
          {/* PERFORMANCE DOMAIN */}
          <Paper sx={{ p: 2, mb: 2, bgcolor: '#1a1a2e' }}>
            <Typography variant="h6" color="primary" gutterBottom>
              Performance Domain
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Hydraulic & flow parameters
            </Typography>
            <Paper sx={{ p: 1, mb: 2, bgcolor: '#0a0a1a' }}>
              <Typography variant="caption" color="primary" sx={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>
                Performance Score = f(velocity, Reynolds, ΔP, safety_margin)
                <br />• Lower pressure drop = better
                <br />• Moderate velocity (target ~3 m/s)
                <br />• Safety margin vs rated pressure
              </Typography>
            </Paper>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="caption">Inner Diameter (Di) - mm</Typography>
                <Slider
                  value={typeof inputs.Di === 'number' ? inputs.Di * 1000 : 25}
                  min={inputSchema.Di?.min_value ? inputSchema.Di.min_value * 1000 : 6}
                  max={inputSchema.Di?.max_value ? inputSchema.Di.max_value * 1000 : 50}
                  onChange={(_, val) => setInputs({ ...inputs, Di: (val as number) / 1000 })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Outer Diameter (Do) - mm</Typography>
                <Slider
                  value={typeof inputs.Do === 'number' ? inputs.Do * 1000 : 31}
                  min={inputSchema.Do?.min_value ? inputSchema.Do.min_value * 1000 : 10}
                  max={inputSchema.Do?.max_value ? inputSchema.Do.max_value * 1000 : 60}
                  onChange={(_, val) => setInputs({ ...inputs, Do: (val as number) / 1000 })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Length (L) - meters</Typography>
                <Slider
                  value={typeof inputs.L === 'number' ? inputs.L : 100}
                  min={inputSchema.L?.min_value || 10}
                  max={inputSchema.L?.max_value || 500}
                  onChange={(_, val) => setInputs({ ...inputs, L: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Flow Rate - L/s</Typography>
                <Slider
                  value={typeof inputs.flow_rate === 'number' ? inputs.flow_rate : 2.5}
                  min={inputSchema.flow_rate?.min_value || 0.5}
                  max={inputSchema.flow_rate?.max_value || 10}
                  step={0.1}
                  onChange={(_, val) => setInputs({ ...inputs, flow_rate: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Operating Pressure - bar</Typography>
                <Slider
                  value={typeof inputs.operating_pressure === 'number' ? inputs.operating_pressure : 10}
                  min={inputSchema.operating_pressure?.min_value || 1}
                  max={inputSchema.operating_pressure?.max_value || 30}
                  onChange={(_, val) => setInputs({ ...inputs, operating_pressure: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Surface Roughness - mm</Typography>
                <Slider
                  value={typeof inputs.roughness === 'number' ? inputs.roughness : 0.007}
                  min={inputSchema.roughness?.min_value || 0.0015}
                  max={inputSchema.roughness?.max_value || 0.15}
                  step={0.001}
                  onChange={(_, val) => setInputs({ ...inputs, roughness: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
            </Grid>
          </Paper>

          {/* DURABILITY DOMAIN */}
          <Paper sx={{ p: 2, mb: 2, bgcolor: '#1a2e1a' }}>
            <Typography variant="h6" color="success.main" gutterBottom>
              Durability Domain
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Material & environmental factors
            </Typography>
            <Paper sx={{ p: 1, mb: 2, bgcolor: '#0a1a0a' }}>
              <Typography variant="caption" color="success.main" sx={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>
                Durability Score = material_factor × reinforcement_factor / climate_degradation
                <br />• Reduced by: temp_degradation, uv_degradation
                <br />• Material max_temp, UV resistance
                <br />• Climate zone degradation multipliers
              </Typography>
            </Paper>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="caption">Material Type</Typography>
                <Select
                  value={inputs.material_type || 'PVC'}
                  onChange={(e) => setInputs({ ...inputs, material_type: e.target.value })}
                  fullWidth
                  size="small"
                >
                  {inputSchema.material_type?.options?.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Reinforcement Type</Typography>
                <Select
                  value={inputs.reinforcement_type || 'Textile'}
                  onChange={(e) => setInputs({ ...inputs, reinforcement_type: e.target.value })}
                  fullWidth
                  size="small"
                >
                  {inputSchema.reinforcement_type?.options?.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Climate Zone</Typography>
                <Select
                  value={inputs.climate_zone || 'Temperate'}
                  onChange={(e) => setInputs({ ...inputs, climate_zone: e.target.value })}
                  fullWidth
                  size="small"
                >
                  {inputSchema.climate_zone?.options?.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Ambient Temp - °C</Typography>
                <Slider
                  value={typeof inputs.ambient_temp === 'number' ? inputs.ambient_temp : 20}
                  min={inputSchema.ambient_temp?.min_value || -20}
                  max={inputSchema.ambient_temp?.max_value || 50}
                  onChange={(_, val) => setInputs({ ...inputs, ambient_temp: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">UV Exposure (0-10)</Typography>
                <Slider
                  value={typeof inputs.uv_exposure === 'number' ? inputs.uv_exposure : 5}
                  min={inputSchema.uv_exposure?.min_value || 0}
                  max={inputSchema.uv_exposure?.max_value || 10}
                  onChange={(_, val) => setInputs({ ...inputs, uv_exposure: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
            </Grid>
          </Paper>

          {/* ECONOMIC DOMAIN */}
          <Paper sx={{ p: 2, mb: 2, bgcolor: '#2e1a1a' }}>
            <Typography variant="h6" color="warning.main" gutterBottom>
              Economic Domain
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Cost & operational parameters
            </Typography>
            <Paper sx={{ p: 1, mb: 2, bgcolor: '#1a0a0a' }}>
              <Typography variant="caption" color="warning.main" sx={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>
                Economic Score = 1 - (total_10yr_cost / max_cost) × 100
                <br />• Material cost = mass × cost_per_kg × reinforcement_multiplier
                <br />• Annual energy = pumping_power × hours × electricity_rate
                <br />• Total = material_cost + (10 × annual_energy)
              </Typography>
            </Paper>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="caption">Material Cost - £/kg</Typography>
                <Slider
                  value={typeof inputs.material_cost_per_kg === 'number' ? inputs.material_cost_per_kg : 2.5}
                  min={0.5}
                  max={20}
                  step={0.5}
                  onChange={(_, val) => setInputs({ ...inputs, material_cost_per_kg: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                  marks={[
                    { value: 2.5, label: 'PVC' },
                    { value: 5, label: 'EPDM' },
                    { value: 15, label: 'PTFE' }
                  ]}
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Reinforcement Cost Multiplier</Typography>
                <Slider
                  value={typeof inputs.reinforcement_cost_mult === 'number' ? inputs.reinforcement_cost_mult : 1.3}
                  min={1.0}
                  max={3.0}
                  step={0.1}
                  onChange={(_, val) => setInputs({ ...inputs, reinforcement_cost_mult: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                  marks={[
                    { value: 1.0, label: 'None' },
                    { value: 1.3, label: 'Textile' },
                    { value: 3.0, label: 'Steel' }
                  ]}
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Electricity Rate - £/kWh</Typography>
                <Slider
                  value={typeof inputs.electricity_rate === 'number' ? inputs.electricity_rate : 0.12}
                  min={inputSchema.electricity_rate?.min_value || 0.05}
                  max={inputSchema.electricity_rate?.max_value || 0.30}
                  step={0.01}
                  onChange={(_, val) => setInputs({ ...inputs, electricity_rate: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption">Operating Hours/Year</Typography>
                <Slider
                  value={typeof inputs.operating_hours_per_year === 'number' ? inputs.operating_hours_per_year : 4000}
                  min={inputSchema.operating_hours_per_year?.min_value || 1000}
                  max={inputSchema.operating_hours_per_year?.max_value || 8760}
                  step={100}
                  onChange={(_, val) => setInputs({ ...inputs, operating_hours_per_year: val as number })}
                  valueLabelDisplay="on"
                  size="small"
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  💡 Material costs can be overridden here. Future: Auto-fetch from commodity price APIs
                </Typography>
              </Grid>
            </Grid>
          </Paper>
          
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBaselineModalOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSetBaseline} 
            variant="contained" 
            disabled={!result}
          >
            Save as Baseline
          </Button>
        </DialogActions>
      </Dialog>

      {/* Exploration History Drawer */}
      <Drawer
        anchor="right"
        open={historyDrawerOpen}
        onClose={() => setHistoryDrawerOpen(false)}
        sx={{ '& .MuiDrawer-paper': { width: 400, bgcolor: '#1a1a1a', color: '#fff' } }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Exploration History
            <IconButton onClick={() => setHistoryDrawerOpen(false)} sx={{ float: 'right' }}>
              <Close />
            </IconButton>
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {explorationHistory.length} configurations explored
          </Typography>
        </Box>
        <Divider />
        <List sx={{ overflow: 'auto' }}>
          {explorationHistory.slice().reverse().map((snapshot, idx) => {
            const actualIdx = explorationHistory.length - 1 - idx
            const timeStr = new Date(snapshot.timestamp).toLocaleTimeString()
            const deltaP = baseline ? snapshot.result.composites.performance_score - baseline.result.composites.performance_score : 0
            const deltaE = baseline ? snapshot.result.composites.economic_score - baseline.result.composites.economic_score : 0
            const deltaD = baseline ? snapshot.result.composites.durability_score - baseline.result.composites.durability_score : 0
            
            return (
              <ListItem 
                key={actualIdx}
                button
                onClick={() => handleRestoreSnapshot(snapshot)}
                sx={{ 
                  borderLeft: baseline ? `3px solid ${deltaP > 0 && deltaE > 0 && deltaD > 0 ? '#4caf50' : '#666'}` : 'none',
                  '&:hover': { bgcolor: '#2a2a2a' }
                }}
              >
                <ListItemText
                  primary={
                    <Box>
                      <Typography variant="body2">
                        Config #{actualIdx + 1} · {timeStr}
                      </Typography>
                      {baseline && (
                        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                          <Chip label={`ΔP: ${deltaP > 0 ? '+' : ''}${deltaP.toFixed(1)}`} size="small" color={deltaP > 0 ? 'success' : 'default'} />
                          <Chip label={`ΔE: ${deltaE > 0 ? '+' : ''}${deltaE.toFixed(1)}`} size="small" color={deltaE > 0 ? 'success' : 'default'} />
                          <Chip label={`ΔD: ${deltaD > 0 ? '+' : ''}${deltaD.toFixed(1)}`} size="small" color={deltaD > 0 ? 'success' : 'default'} />
                        </Box>
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      Overall: {snapshot.result.overall_score.toFixed(1)}
                    </Typography>
                  }
                />
              </ListItem>
            )
          })}
        </List>
      </Drawer>

      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a' }}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: '1px solid #333' }}>
          <Typography variant="h4" align="center" sx={{ fontWeight: 300 }}>
            Feasibility Platform
          </Typography>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            centered
            sx={{ mt: 1 }}
          >
            <Tab label="Visualizations" />
            <Tab label="Engine Selection" />
          </Tabs>
        </Box>

        {/* Tab 0: Visualizations (all visualization modes) */}
        {activeTab === 0 && (
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Control Panel */}
          <Box sx={{ 
            borderRight: '1px solid #333', 
            overflowY: 'auto', 
            p: 2,
            display: { xs: 'none', md: 'block' },
            width: `${controlPanelWidth}px`,
            minWidth: '250px',
            maxWidth: '600px',
            position: 'relative',
            flexShrink: 0
          }}>
            {/* Resize Handle */}
            <Box
              onMouseDown={(e) => {
                e.preventDefault()
                const startX = e.clientX
                const startWidth = controlPanelWidth
                const handleMouseMove = (e: MouseEvent) => {
                  const delta = e.clientX - startX
                  setControlPanelWidth(Math.min(600, Math.max(250, startWidth + delta)))
                }
                const handleMouseUp = () => {
                  document.removeEventListener('mousemove', handleMouseMove)
                  document.removeEventListener('mouseup', handleMouseUp)
                }
                document.addEventListener('mousemove', handleMouseMove)
                document.addEventListener('mouseup', handleMouseUp)
              }}
              sx={{
                position: 'absolute',
                right: 0,
                top: 0,
                bottom: 0,
                width: '4px',
                cursor: 'col-resize',
                bgcolor: 'transparent',
                '&:hover': { bgcolor: '#00bcd4' },
                zIndex: 10
              }}
            />
            {/* Baseline & History Controls */}
            <Paper sx={{ p: 1.25, mb: 1.25, bgcolor: '#1a1a1a' }}>
              <Typography variant="caption" fontWeight="bold" gutterBottom display="block" sx={{ fontSize: '0.75rem', mb: 0.75 }}>
                Baseline & History
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, mb: 0.5 }}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  startIcon={<Bookmark sx={{ fontSize: '0.9rem' }} />}
                  onClick={() => setBaselineModalOpen(true)}
                  sx={{ py: 0.4, fontSize: '0.65rem' }}
                >
                  {baseline ? 'Edit' : 'Set'}
                </Button>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  startIcon={<History sx={{ fontSize: '0.9rem' }} />}
                  onClick={() => setHistoryDrawerOpen(true)}
                  sx={{ py: 0.4, fontSize: '0.65rem' }}
                >
                  History ({explorationHistory.length})
                </Button>
              </Box>
              {baseline && (
                <Typography variant="caption" color="success.main" sx={{ fontSize: '0.65rem' }}>
                  ✓ Baseline set · Showing ΔEV
                </Typography>
              )}
            </Paper>

            {/* Visualization Controls - All in One */}
            <Paper sx={{ p: 1, mb: 1.25, bgcolor: '#1a1a1a' }}>
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#999', display: 'block', mb: 0.5 }}>
                  Visualization Mode
                </Typography>
                <Select
                  value={visualizationMode}
                  onChange={(e) => setVisualizationMode(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ 
                    bgcolor: '#222', 
                    borderColor: '#00bcd4',
                    '& .MuiSelect-select': { py: 0.4, fontSize: '0.7rem' },
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: '#00bcd4' }
                  }}
                >
                  <MenuItem value="basic">Basic 3D Profile</MenuItem>
                  <MenuItem value="ternary">Ternary Plot</MenuItem>
                  <MenuItem value="feasibility">Feasibility Volume</MenuItem>
                  <MenuItem value="parallel">Parallel Coordinates</MenuItem>
                  <MenuItem value="response">Response Surface</MenuItem>
                  <MenuItem value="sensitivity">Sensitivity Analysis</MenuItem>
                  <MenuItem value="correlation">Correlation Matrix</MenuItem>
                  <MenuItem value="pareto">Pareto Frontier</MenuItem>
                  <MenuItem value="radar">Radar Chart</MenuItem>
                </Select>
              </Box>

              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#999', display: 'block', mb: 0.5 }}>
                  Target Profile
                </Typography>
                <FormControl fullWidth>
                  <Select
                    value={targetProfile}
                    onChange={(e) => handleProfileChange(e.target.value)}
                    size="small"
                    sx={{ 
                      bgcolor: '#222',
                      borderColor: '#00bcd4',
                      '& .MuiSelect-select': { py: 0.4, fontSize: '0.7rem' },
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#00bcd4' }
                    }}
                  >
                    <MenuItem value="Maximum Performance">Maximum Performance</MenuItem>
                    <MenuItem value="Best ROI">Best ROI</MenuItem>
                    <MenuItem value="Balanced">Balanced</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#999', display: 'block', mb: 0.5 }}>
                  Brightness
                </Typography>
                <Slider
                  value={surfaceBrightness}
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  onChange={(_: Event, val: number | number[]) => setSurfaceBrightness(val as number)}
                  size="small"
                  sx={{ 
                    color: '#00bcd4',
                    '& .MuiSlider-markLabel': { fontSize: '0.55rem' }
                  }}
                  marks={[
                    { value: 0.3, label: 'Dim' },
                    { value: 0.6, label: 'Normal' },
                    { value: 0.9, label: 'Bright' }
                  ]}
                />
              </Box>
            </Paper>

            {/* Parameter Sliders */}
            <Paper sx={{ p: 1, bgcolor: '#1a1a1a', height: 'calc(100vh - 350px)', overflow: 'auto' }}>
              <Typography variant="caption" fontWeight="bold" gutterBottom display="block" sx={{ mb: 1, fontSize: '0.7rem' }}>
                Input Parameters ({Object.keys(inputSchema).length})
              </Typography>
              
              {Object.keys(inputSchema).length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  Loading parameters...
                </Typography>
              )}
              
              {console.log('Rendering parameters, count:', Object.keys(inputSchema).length)}
              {Object.entries(inputSchema).map(([key, param]) => {
                console.log('Rendering parameter:', key, param)
                return (
                <Box key={key} sx={{ mb: 0.75 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.3 }}>
                    <Typography variant="caption" sx={{ color: '#999', fontSize: '0.65rem' }}>
                      {param.name} {param.unit && `(${param.unit})`}
                    </Typography>
                    <Tooltip title={param.description} arrow>
                      <IconButton size="small" sx={{ p: 0.15 }}>
                        <Info fontSize="small" sx={{ fontSize: '0.85rem' }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  {param.type === 'select' ? (
                    <FormControl fullWidth size="small">
                      <Select
                        value={inputs[key] || param.default}
                        onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                        sx={{ 
                          bgcolor: '#222',
                          '& .MuiSelect-select': { py: 0.35, fontSize: '0.7rem' },
                          '& .MuiOutlinedInput-notchedOutline': { borderColor: '#00bcd4' },
                          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#00bcd4' },
                          '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#00bcd4' }
                        }}
                      >
                        {param.options?.map(option => (
                          <MenuItem key={option} value={option} sx={{ fontSize: '0.7rem' }}>{option}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ) : (
                    <Box>
                      <Slider
                        value={typeof inputs[key] === 'number' ? inputs[key] : param.default}
                        min={param.min_value}
                        max={param.max_value}
                        step={(param.max_value! - param.min_value!) / 100}
                        onChange={(_: Event, val: number | number[]) => setInputs({ ...inputs, [key]: val as number })}
                        size="small"
                        sx={{ 
                          color: '#00bcd4',
                          '& .MuiSlider-valueLabel': { fontSize: '0.65rem' }
                        }}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(value) => value.toFixed(3)}
                      />
                    </Box>
                  )}
                </Box>
              )})}
            </Paper>

            {/* Overall Score - D/P/E shown on 3D visual */}
            {result && (
              <Paper sx={{ p: 1.5, mt: 1.25, bgcolor: '#00bcd4', borderRadius: 1, textAlign: 'center' }}>
                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#000', fontWeight: 'bold' }}>
                  OVERALL SCORE
                </Typography>
                <Typography variant="h3" sx={{ color: '#000', fontWeight: 'bold', lineHeight: 1.2 }}>
                  {result.overall_score.toFixed(1)}
                </Typography>
              </Paper>
            )}
          </Box>

          {/* Visualization Area */}
          <Box sx={{ position: 'relative', height: '100%', flex: 1 }}>
            {/* Draggable Calculation Details Panel */}
            {calcDetailsOpen && result && (
              <Paper
                onMouseDown={(e) => {
                  if ((e.target as HTMLElement).closest('.drag-handle')) {
                    setIsDragging(true)
                    setDragOffset({
                      x: e.clientX - calcDetailsPos.x,
                      y: e.clientY - calcDetailsPos.y
                    })
                  }
                }}
                onMouseMove={(e) => {
                  if (isDragging) {
                    setCalcDetailsPos({
                      x: e.clientX - dragOffset.x,
                      y: e.clientY - dragOffset.y
                    })
                  }
                }}
                onMouseUp={() => setIsDragging(false)}
                sx={{
                  position: 'absolute',
                  top: `${calcDetailsPos.y}px`,
                  left: `${calcDetailsPos.x}px`,
                  width: 320,
                  bgcolor: 'rgba(10, 10, 10, 0.95)',
                  border: '1px solid #333',
                  borderRadius: 1,
                  zIndex: 100,
                  cursor: isDragging ? 'grabbing' : 'default',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                }}
              >
                <Box className="drag-handle" sx={{ 
                  p: 1.5, 
                  bgcolor: '#1a1a1a', 
                  cursor: 'grab',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid #333'
                }}>
                  <Typography variant="subtitle2">💡 Actionable Insights</Typography>
                  <IconButton size="small" onClick={() => setCalcDetailsOpen(false)}>
                    <Close fontSize="small" />
                  </IconButton>
                </Box>
                <Box sx={{ p: 2, maxHeight: 400, overflowY: 'auto' }}>
                  {/* Economic Insights */}
                  {baseline && result.composites.economic_score < baseline.result.composites.economic_score && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#2e1a1a', borderLeft: '3px solid #ff9800', borderRadius: 1 }}>
                      <Typography variant="caption" color="warning.main" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        ⚠️ Higher Cost Detected
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        Current config costs £{result.components.total_cost.value.toFixed(2)} vs baseline £{baseline.result.components.total_cost.value.toFixed(2)}
                        <br />• Material: £{result.components.material_cost.value.toFixed(2)}
                        <br />→ Consider: Lower-cost materials (PVC, EPDM) if durability allows
                      </Typography>
                    </Box>
                  )}
                  {baseline && result.composites.economic_score > baseline.result.composites.economic_score && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#1a2e1a', borderLeft: '3px solid #4caf50', borderRadius: 1 }}>
                      <Typography variant="caption" color="success.main" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        ✓ Cost Savings Achieved
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        Saving £{(baseline.result.components.total_cost.value - result.components.total_cost.value).toFixed(2)} over 10 years
                      </Typography>
                    </Box>
                  )}

                  {/* Performance Insights */}
                  {result.components.deltaP.value > 2 && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#2e1a1a', borderLeft: '3px solid #f44336', borderRadius: 1 }}>
                      <Typography variant="caption" color="error.main" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        ⚠️ High Pressure Drop
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        ΔP = {result.components.deltaP.value.toFixed(2)} bar (high)
                        <br />→ Increase inner diameter or reduce length
                        <br />→ Check for blockages or high roughness
                      </Typography>
                    </Box>
                  )}
                  {result.components.velocity.value > 5 && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#2e1a1a', borderLeft: '3px solid #ff9800', borderRadius: 1 }}>
                      <Typography variant="caption" color="warning.main" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        ⚠️ High Flow Velocity
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        v = {result.components.velocity.value.toFixed(2)} m/s (erosion risk)
                        <br />→ Increase diameter to reduce velocity
                      </Typography>
                    </Box>
                  )}

                  {/* Durability Insights */}
                  {baseline && result.composites.durability_score < baseline.result.composites.durability_score && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#2e1a1a', borderLeft: '3px solid #ff9800', borderRadius: 1 }}>
                      <Typography variant="caption" color="warning.main" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        ⚠️ Reduced Durability
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        Check: UV exposure, ambient temperature vs material limits
                        <br />→ Consider: EPDM or Silicone for UV resistance
                      </Typography>
                    </Box>
                  )}

                  {/* No raw calculations - use tooltips on 3D visual instead */}
                </Box>
              </Paper>
            )}
            {!calcDetailsOpen && (
              <IconButton
                onClick={() => setCalcDetailsOpen(true)}
                sx={{
                  position: 'absolute',
                  top: 20,
                  left: 20,
                  bgcolor: 'rgba(10, 10, 10, 0.8)',
                  '&:hover': { bgcolor: 'rgba(10, 10, 10, 0.95)' },
                  zIndex: 100
                }}
              >
                <Info />
              </IconButton>
            )}
            {visualizationMode === 'basic' ? (
              <Canvas>
                <PerspectiveCamera makeDefault position={[80, 80, 80]} />
                <ProfileShapeVisualization 
                  currentScores={result ? {
                    performance: result.composites.performance_score,
                    durability: result.composites.durability_score,
                    economic: result.composites.economic_score
                  } : null}
                  baselineScores={baseline ? {
                    performance: baseline.result.composites.performance_score,
                    durability: baseline.result.composites.durability_score,
                    economic: baseline.result.composites.economic_score
                  } : null}
                  brightness={surfaceBrightness}
                  result={result}
                  baseline={baseline}
                />
                <OrbitControls 
                  enableDamping 
                  dampingFactor={0.05}
                  minDistance={50}
                  maxDistance={200}
                />
              </Canvas>
            ) : (
              <VisualizationModeSelector
                calculationResult={result}
                inputs={inputs}
                parameterSchema={Object.entries(inputSchema).map(([key, param]) => ({
                  ...param,
                  display_name: param.name,
                  name: key
                }))}
                explorationHistory={explorationHistory.map(s => s.result)}
                initialMode={visualizationMode}
                hideSelector={true}
              />
            )}
          </Box>
        </Box>
        )}

        {/* Tab 1: Engine Selection */}
        {activeTab === 1 && (
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            <EngineSelector
              selectedEngineId={selectedEngineId}
              onEngineSelect={(engineId) => {
                setSelectedEngineId(engineId)
                setActiveTab(0) // Switch back to basic view after selection
              }}
            />
          </Box>
        )}

        {/* Footer with version */}
        <Box sx={{ 
          borderTop: '1px solid #333', 
          p: 1, 
          textAlign: 'center',
          bgcolor: '#0a0a0a',
          position: 'sticky',
          bottom: 0,
          zIndex: 1000
        }}>
          <Typography variant="caption" color="text.secondary">
            Feasibility Platform {appVersion} · {new Date().getFullYear()} · Powered by AI
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
