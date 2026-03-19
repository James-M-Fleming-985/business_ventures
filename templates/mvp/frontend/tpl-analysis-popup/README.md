# Analysis Pop-out Template

## Overview
Template for intelligent analysis modal components that provide detailed correlation explanations, causality testing results, and AI-generated insights.

## Features
- Interactive modal with tabbed sections
- Causality analysis visualization
- Drift timeline charts
- AI-powered explanations
- Export and sharing functionality

## Dependencies
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "recharts": "^2.8.0",
  "tailwindcss": "^3.3.0",
  "@headlessui/react": "^1.7.17",
  "react-query": "^3.39.3"
}
```

## Template Variables
- `{{modal_name}}`: Modal component name
- `{{causality_api}}`: Causality testing API endpoint
- `{{explanation_api}}`: AI explanation generation endpoint
- `{{export_formats}}`: Supported export formats

## Generated Structure
```
analysis_popup/
├── components/
│   ├── AnalysisModal.tsx
│   ├── CausalityTab.tsx
│   ├── DriftTimelineTab.tsx
│   ├── ExplanationTab.tsx
│   └── ExportButton.tsx
├── hooks/
│   ├── useCausalityData.ts
│   ├── useDriftData.ts
│   └── useExplanation.ts
├── utils/
│   ├── causalityHelpers.ts
│   └── exportHelpers.ts
└── tests/
    └── AnalysisModal.test.tsx
```

## Key Components
- Overview section with correlation summary
- Causality testing with Granger tests and DAG visualization
- Drift timeline showing relationship evolution
- AI-generated explanations with confidence scores
- Actionable recommendations for MVP opportunities