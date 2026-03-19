# Interactive Correlation Heatmap Template

## Overview
Template for building interactive correlation matrix visualizations with real-time updates, zoom capabilities, and drill-down functionality.

## Features
- D3.js powered correlation heatmap
- Real-time data updates
- Interactive zoom and pan
- Hover tooltips with details
- Color-coded correlation strength
- Click-to-drill-down functionality

## Dependencies
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "d3": "^7.8.5",
  "@types/d3": "^7.4.0",
  "tailwindcss": "^3.3.0",
  "react-query": "^3.39.3"
}
```

## Template Variables
- `{{component_name}}`: React component name
- `{{api_endpoint}}`: Backend correlation API endpoint
- `{{update_interval}}`: Real-time update interval (ms)
- `{{color_scheme}}`: D3 color scale (e.g., 'RdBu', 'viridis')

## Generated Structure
```
correlation_heatmap/
├── components/
│   ├── CorrelationHeatmap.tsx
│   ├── HeatmapTooltip.tsx
│   └── ColorLegend.tsx
├── hooks/
│   ├── useCorrelationData.ts
│   └── useHeatmapInteractions.ts
├── utils/
│   ├── d3Helpers.ts
│   └── correlationUtils.ts
├── types/
│   └── correlation.types.ts
└── tests/
    ├── CorrelationHeatmap.test.tsx
    └── correlationUtils.test.ts
```

## Key Features
- Responsive design for mobile and desktop
- WebSocket integration for live updates
- Efficient rendering for large correlation matrices
- Accessibility support (ARIA labels, keyboard navigation)
- Export functionality (PNG, SVG, PDF)

## Performance Targets
- Render 100x100 matrix: < 2 seconds
- Real-time update latency: < 500ms
- Smooth zoom/pan interactions: 60fps
- Memory usage: < 500MB for large datasets