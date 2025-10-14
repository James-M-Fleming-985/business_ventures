# CA-006 Feedback Dashboard - UI Visualization & Design Specification
# =====================================================================

## Overview
The CA-006 Feedback Dashboard is a real-time analytics and prioritization interface for monitoring all deployed MVPs across the Causal Affect platform.

---

## Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Causal Affect - Feedback Dashboard                    👤 User    🔔 Alerts    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  📊 Portfolio Overview                                    🔄 Last updated: 30s │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │  Total MVPs  │  Active MVPs │ High Priority│ Archive Queue│   Total Rev   │ │
│  │     47       │      42      │      12      │      3       │   $127,450   │ │
│  │   +3 (7d)    │   +2 (7d)    │   +1 (7d)    │   -1 (7d)    │  +$12.3K (7d)│ │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                                 │
│  🎯 Top Performers (Priority Score > 75)                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Rank │ MVP Name           │ Score │ DAU    │ Revenue  │ Growth │ Trend  │  │
│  ├──────┼────────────────────┼───────┼────────┼──────────┼────────┼────────┤  │
│  │  🥇  │ TaskFlow Pro       │  92   │ 1,247  │ $4,231/d │ +127%  │ ↗️↗️↗️  │  │
│  │  🥈  │ MealPlan AI        │  88   │   892  │ $3,102/d │ +89%   │ ↗️↗️    │  │
│  │  🥉  │ FitTracker Plus    │  84   │ 1,891  │ $2,847/d │ +67%   │ ↗️↗️    │  │
│  │   4  │ BudgetBuddy        │  81   │   634  │ $1,923/d │ +52%   │ ↗️     │  │
│  │   5  │ LearnPath          │  78   │   421  │ $1,654/d │ +48%   │ ↗️     │  │
│  └──────┴────────────────────┴───────┴────────┴──────────┴────────┴────────┘  │
│                                                          [View All Top 25 →]   │
│                                                                                 │
│  ⚠️ Archive Candidates (Priority Score < 10, No Growth 30d)                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ MVP Name        │ Score │ DAU   │ Revenue  │ Last Activity │ Action      │  │
│  ├─────────────────┼───────┼───────┼──────────┼───────────────┼─────────────┤  │
│  │ QuickNote App   │   7   │   12  │  $0/d    │ 45 days ago   │ [Archive]   │  │
│  │ EventFinder     │   5   │    8  │  $0/d    │ 61 days ago   │ [Archive]   │  │
│  │ ColorSchemer    │   3   │    3  │  $0/d    │ 89 days ago   │ [Archive]   │  │
│  └─────────────────┴───────┴───────┴──────────┴───────────────┴─────────────┘  │
│                                                                                 │
│  📈 Portfolio Metrics (Last 30 Days)                                           │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                          │ │
│  │  Total DAU Trend                        Revenue Trend                   │ │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░            ░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │ │
│  │  │                          ╱             │                        ╱     │ │
│  │  │                     ╱╲  ╱              │                   ╱╲  ╱      │ │
│  │  │                ╱╲  ╱  ╲╱               │              ╱╲  ╱  ╲╱       │ │
│  │  │           ╱╲  ╱  ╲╱                    │         ╱╲  ╱  ╲╱            │ │
│  │  │      ╱╲  ╱  ╲╱                         │    ╱╲  ╱  ╲╱                 │ │
│  │  └──────────────────────────────────      └──────────────────────────── │ │
│  │   1d   7d   14d  21d  30d                  1d   7d   14d  21d  30d      │ │
│  │                                                                          │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Individual MVP Detail View

When you click on an MVP (e.g., "TaskFlow Pro"), you see:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                    TaskFlow Pro                   ⭐ Score: 92│
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  📌 Quick Stats                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────────┐│
│  │  Priority Score: 92/100  ████████████████████░░  [Excellent Performance]   ││
│  │                                                                             ││
│  │  Score Breakdown:                                                           ││
│  │  • Engagement Score (30%): 95  ████████████████████                         ││
│  │  • Revenue Score (35%):    91  ██████████████████                           ││
│  │  • Growth Score (25%):     88  █████████████████                            ││
│  │  • Potential Score (10%):  90  ██████████████████                           ││
│  └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  📊 Key Metrics (Real-time, <1 min refresh)                                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   DAU (24h)  │   Sessions   │ Avg Session  │ Bounce Rate  │ Retention 7d │ │
│  │    1,247     │    3,421     │   12m 34s    │    23.4%     │    67.8%     │ │
│  │   +8.2% ↗️   │  +12.3% ↗️   │  +5.1% ↗️    │  -2.1% ↘️    │  +4.3% ↗️    │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                                 │
│  💰 Revenue Metrics                                                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │  Revenue/Day │  Conv Rate   │     AOV      │   LTV:CAC    │     MRR      │ │
│  │   $4,231     │    4.2%      │   $29.99     │    3.2:1     │   $89,234    │ │
│  │  +23.4% ↗️   │  +0.8% ↗️    │  +2.1% ↗️    │  +0.3 ↗️     │  +18.2% ↗️   │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                                 │
│  📈 Engagement Over Time (30 Days)                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                             ││
│  │  1500 ┤                                                          ●          ││
│  │       │                                                      ●  ╱           ││
│  │  1200 ┤                                                  ●  ╱               ││
│  │       │                                              ●  ╱                   ││
│  │  900  ┤                                          ●  ╱                       ││
│  │       │                                      ●  ╱                           ││
│  │  600  ┤                                  ●  ╱                               ││
│  │       │                              ●  ╱                                   ││
│  │  300  ┤                          ●  ╱                                       ││
│  │       └──────────────────────────────────────────────────────────────────  ││
│  │        1d    5d    10d   15d   20d   25d   30d                             ││
│  │                                                                             ││
│  │  Legend: ● DAU    ▲ Sessions    ◆ Revenue                                  ││
│  └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  🎯 Conversion Funnel                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐│
│  │  Impression → Click → Visit → Signup → Trial → Purchase → Repeat           ││
│  │                                                                             ││
│  │  ████████████  95%  ██████████  23%  ████  4.2%  ███  89%  ██  45%         ││
│  │  10,000 impr → 9,500 clicks → 2,185 visits → 92 signups → 82 trials → 37  ││
│  │                                                                             ││
│  │  Drop-off Analysis:                                                         ││
│  │  • Click to Visit: 77% drop (expected 50-70%, ⚠️ needs improvement)        ││
│  │  • Visit to Signup: 95.8% drop (expected 85-95%, ✅ good)                  ││
│  └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  📍 Traffic Sources                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐│
│  │  Source      │ Users │ Conv Rate │ Revenue  │ CAC    │ ROI                 ││
│  ├──────────────┼───────┼───────────┼──────────┼────────┼─────────────────────┤│
│  │  Google Ads  │  547  │   5.2%    │ $1,847/d │ $12.34 │ 4.8x  ████████░░    ││
│  │  Facebook    │  412  │   3.8%    │ $1,234/d │ $15.67 │ 2.1x  ████░░░░░░    ││
│  │  Organic     │  188  │   6.1%    │   $892/d │  $0.00 │  ∞    ██████████    ││
│  │  Reddit      │   78  │   2.9%    │   $189/d │  $8.23 │ 3.1x  █████░░░░░    ││
│  │  Direct      │   22  │   4.5%    │    $69/d │  $0.00 │  ∞    ██████████    ││
│  └──────────────┴───────┴───────────┴──────────┴────────┴─────────────────────┘│
│                                                                                 │
│  🎬 Recent Events (Live Feed)                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐│
│  │  • 15s ago: New signup from Google Ads (San Francisco, CA)                 ││
│  │  • 42s ago: Purchase completed - $29.99 (Returning customer)               ││
│  │  • 1m ago:  Session started (Mobile, iOS 17, Chrome)                       ││
│  │  • 2m ago:  Trial started (Email: user***@gmail.com)                       ││
│  │  • 3m ago:  Page view: /pricing (Desktop, Chrome, USA)                     ││
│  └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  🔧 Actions                                                                     │
│  [🚀 Prioritize for Iteration]  [📊 View Analytics Dashboard]  [⚙️ Settings]  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Analytics Integration Panel

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🔌 Analytics Providers                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  Provider         │ Status    │ Last Sync    │ Metrics Collected │ Errors │ │
│  ├───────────────────┼───────────┼──────────────┼───────────────────┼────────┤ │
│  │  Google Analytics │ ✅ Active │ 23 sec ago   │ 127,453           │   0    │ │
│  │  Mixpanel         │ ✅ Active │ 31 sec ago   │  89,234           │   0    │ │
│  │  Amplitude        │ ✅ Active │ 18 sec ago   │  67,891           │   0    │ │
│  │  Segment          │ ⚠️ Slow   │ 4 min ago    │  12,456           │   3    │ │
│  └───────────────────┴───────────┴──────────────┴───────────────────┴────────┘  │
│                                                                                 │
│  Provider Health Metrics                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  Google Analytics:  ████████████████████████ 98.7% uptime (30d)         │  │
│  │  Mixpanel:          ███████████████████████░  96.3% uptime (30d)        │  │
│  │  Amplitude:         ████████████████████████  99.1% uptime (30d)        │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  [🔄 Sync All Now]  [⚙️ Configure Providers]  [📊 View Error Logs]            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key React Components to Build

### Core Layout
1. **DashboardLayout.tsx** - Main layout with navigation and header
2. **Navbar.tsx** - Top navigation bar with user menu
3. **Sidebar.tsx** - Optional sidebar for navigation

### Dashboard Views
4. **PortfolioOverview.tsx** - Top-level portfolio metrics (5 stat cards)
5. **TopPerformersTable.tsx** - Sortable, filterable table of high-priority MVPs
6. **ArchiveCandidatesTable.tsx** - List of MVPs pending archive
7. **PortfolioMetricsCharts.tsx** - DAU and Revenue trend charts

### MVP Detail
8. **MVPDetailView.tsx** - Full detail page for individual MVP
9. **ScoreBreakdownCard.tsx** - Priority score with dimension breakdown
10. **KeyMetricsGrid.tsx** - Grid of engagement/revenue metric cards
11. **EngagementChart.tsx** - 30-day engagement trend chart
12. **ConversionFunnel.tsx** - Funnel visualization with drop-off analysis
13. **TrafficSourcesTable.tsx** - Traffic sources with ROI metrics
14. **LiveEventFeed.tsx** - Real-time event stream

### Shared Components
15. **MetricsCard.tsx** - Reusable metric display with trend indicator
16. **TrendIndicator.tsx** - Up/down arrow with percentage change
17. **ProgressBar.tsx** - Horizontal progress bar for scores
18. **StatCard.tsx** - Reusable stat card component
19. **Chart.tsx** - Recharts wrapper for line/bar charts

### Admin/Settings
20. **AnalyticsProvidersPanel.tsx** - Provider status and configuration
21. **PrioritizationSettings.tsx** - Algorithm weight configuration
22. **ArchiveManagementPanel.tsx** - Archive queue and workflow
23. **SettingsPage.tsx** - Global settings interface

---

## Technology Stack for UI

### Frontend (React + Vite)
- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3 (utility-first CSS)
- **State Management**: Zustand (lightweight, simple)
- **Charts/Graphs**: Recharts (React-native charts)
- **Real-time Updates**: WebSocket connection to backend
- **Data Tables**: TanStack Table (React Table v8)
- **Icons**: Heroicons / Lucide React
- **Animations**: Framer Motion (smooth transitions)
- **HTTP Client**: Axios / Fetch API
- **Forms**: React Hook Form + Zod validation

### Backend API (FastAPI)
- **Framework**: FastAPI (Python 3.11+)
- **Real-time**: WebSocket support for live metrics
- **API Format**: RESTful JSON
- **Documentation**: Auto-generated with Swagger/OpenAPI

### Data Flow
```
Analytics Providers (GA, Mixpanel, Amplitude)
           ↓
Backend (FastAPI) - Collects & Aggregates Data
           ↓
PostgreSQL (Storage) + Redis (Cache)
           ↓
WebSocket / REST API
           ↓
React Frontend - Real-time Dashboard (<1min refresh)
```

---

## Color Scheme & Design System

### Colors
- **Primary Blue**: #3B82F6 - Actions, links, primary buttons
- **Success Green**: #10B981 - Positive metrics, growth indicators
- **Warning Yellow**: #F59E0B - Attention needed, medium priority
- **Danger Red**: #EF4444 - Archive, critical issues, negative trends
- **Info Purple**: #8B5CF6 - Information, secondary actions
- **Neutral Gray**: #6B7280 - Text, borders, backgrounds

### Typography
- **Headings**: Inter Bold (font-family: 'Inter', sans-serif)
- **Body**: Inter Regular
- **Monospace**: JetBrains Mono (for metrics/numbers)
- **Sizes**: 12px (xs), 14px (sm), 16px (base), 18px (lg), 24px (xl)

### Spacing
- **Grid**: 8px base unit (0.5rem, 1rem, 1.5rem, 2rem, 3rem, 4rem)
- **Container**: Max-width 1400px with 2rem padding

### Layout Grid
- **Desktop (>1024px)**: 12-column grid, max-width 1400px
- **Tablet (768-1024px)**: 8-column grid
- **Mobile (<768px)**: 4-column grid, full-width

---

## API Endpoints (Backend)

### Portfolio
- `GET /api/v1/portfolio/overview` - Portfolio summary stats
- `GET /api/v1/portfolio/metrics` - Time-series metrics
- `GET /api/v1/mvps` - List all MVPs with pagination/filtering
- `GET /api/v1/mvps/top-performers` - Top performing MVPs
- `GET /api/v1/mvps/archive-candidates` - MVPs pending archive

### MVP Details
- `GET /api/v1/mvps/{mvp_id}` - Individual MVP details
- `GET /api/v1/mvps/{mvp_id}/metrics` - MVP metrics
- `GET /api/v1/mvps/{mvp_id}/events` - Recent events for MVP
- `GET /api/v1/mvps/{mvp_id}/score-breakdown` - Score components
- `GET /api/v1/mvps/{mvp_id}/conversion-funnel` - Funnel data
- `GET /api/v1/mvps/{mvp_id}/traffic-sources` - Traffic source breakdown

### Analytics
- `GET /api/v1/analytics/providers` - Provider status
- `POST /api/v1/analytics/sync` - Trigger manual sync
- `GET /api/v1/analytics/errors` - Error logs

### Prioritization
- `GET /api/v1/prioritization/settings` - Current algorithm config
- `PUT /api/v1/prioritization/settings` - Update weights/thresholds
- `POST /api/v1/prioritization/recalculate` - Force recalculation

### Archive
- `GET /api/v1/archive/queue` - Archive queue
- `POST /api/v1/archive/{mvp_id}/approve` - Approve archive
- `POST /api/v1/archive/{mvp_id}/reject` - Reject archive
- `GET /api/v1/archive/history` - Archived MVPs

### WebSocket
- `WS /ws/live-feed` - Real-time event stream
- `WS /ws/metrics/{mvp_id}` - Real-time MVP metrics

---

## Mobile Responsive View

The dashboard will be fully responsive with breakpoints:

- **Desktop (>1024px)**: Full dashboard with all panels
- **Tablet (768-1024px)**: Stacked panels, simplified charts
- **Mobile (<768px)**: Single column, collapsible sections, swipeable cards

---

## Summary

This dashboard provides:
- ✅ **Real-time visibility** into all MVPs (<1 min latency)
- ✅ **Clear prioritization** with explainable scoring
- ✅ **Automated archive** recommendations with workflow
- ✅ **Complete analytics** integration (GA, Mixpanel, Amplitude)
- ✅ **Beautiful UI** with modern React + TailwindCSS
- ✅ **Responsive design** for desktop, tablet, mobile
- ✅ **Live updates** via WebSocket
- ✅ **Production-ready** with Railway deployment

**Ready to generate the code for this dashboard!** 🎨🚀
