/**
 * Shared TypeScript interfaces for Feasibility Platform
 * These match the backend Python schemas for type safety
 */

export interface ParameterSchema {
  name: string; // Parameter key (e.g., "Di", "Do", "material_type")
  display_name?: string; // Human-readable name (e.g., "Inner Diameter")
  type: string; // "float", "integer", "select"
  min_value?: number;
  max_value?: number;
  default: any;
  unit: string;
  description: string;
  options?: string[]; // For dropdown/select inputs
}

export interface ComponentResult {
  value: number;
  unit: string;
  formula: string;
  calculation_steps: string[];
  normalized: number;
}

export interface CalculationResult {
  components: Record<string, ComponentResult>;
  composites: Record<string, number>; // performance_score, economic_score, durability_score
  visualization_point: Record<string, number>; // All parameter values for this calculation
  overall_score: number;
  metadata?: {
    calculation_time_ms?: number;
    timestamp?: string;
    [key: string]: any;
  };
}

export interface EngineMetadata {
  engine_id: string;
  name: string;
  description: string;
  version: string;
  domain: string;
}

export interface VisualizationProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
}

export type VisualizationMode =
  | 'ternary'
  | 'feasibility'
  | 'parallel'
  | 'response'
  | 'sensitivity'
  | 'correlation'
  | 'pareto'
  | 'radar';

export interface VisualizationConfig {
  mode: VisualizationMode;
  targetFPS: number;
  maxHistoryEntries: number;
  performanceMonitoring: boolean;
}

export interface PerformanceMetrics {
  fps: number;
  updateLatencyMs: number;
  frameDrops: number;
  lastMeasurement: number;
}
