# CA-006 Feedback Dashboard

Modern React dashboard for monitoring MVP portfolio performance.

## Quick Start

### Development
```bash
npm run dev
```

Open http://localhost:5173 to view the dashboard.

### Build for Production
```bash
npm run build
```

### Run Tests
```bash
npm test
```

## Features

- **Portfolio Overview**: View all MVPs with key metrics and trends
- **MVP Detail View**: Deep dive into individual MVP analytics
- **Real-time Updates**: WebSocket connections for live data
- **Responsive Design**: Desktop, tablet, and mobile support
- **Interactive Charts**: Recharts-powered visualizations

## Architecture

- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3
- **State**: Zustand
- **Charts**: Recharts
- **Tables**: TanStack Table
- **Testing**: Vitest + React Testing Library

## Backend Integration

Configure backend API URL in `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

Backend should provide:
- GET /api/v1/portfolio/overview
- GET /api/v1/mvps
- GET /api/v1/mvps/{id}/metrics
- WebSocket /ws/live-feed

See `FEATURE-CA-006-06_dashboard_ui.yaml` for complete API specification.

## Deployment

### Railway
```bash
railway link
railway up
```

### Docker
```bash
docker build -t dashboard-ui .
docker run -p 5173:5173 dashboard-ui
```

## License

Proprietary - Causal Affect System CA-006
