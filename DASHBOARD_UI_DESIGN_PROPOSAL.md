# Causal Affect Platform - Dashboard UI Design Proposal

**Version:** 1.0  
**Date:** November 5, 2025  
**Status:** Pending Review

---

## 🎨 Design Philosophy

**Modern, Clean, Data-Focused**
- Professional dark theme with accent colors
- Emphasis on data visualization and insights
- Minimal distractions, maximum clarity
- Responsive design (desktop-first, mobile-friendly)

---

## 🎯 Layout Structure

### **Main Navigation (Left Sidebar)**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔮 Causal Affect Platform                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Dashboard          [Active]                             │
│  🔗 Correlation Analysis                                    │
│  📈 Forecasting                                             │
│  🎯 Opportunities                                           │
│  🔌 Data Sources                                            │
│  ⚙️  Settings                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### **Dashboard Page Layout**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  [Navigation Sidebar]  │  MAIN CONTENT AREA                                    │
│                        │                                                        │
│                        │  ┌──────────────────────────────────────────────┐    │
│                        │  │ 🎯 Quick Stats Bar                           │    │
│                        │  │ ╔═══════╗  ╔═══════╗  ╔═══════╗  ╔═══════╗ │    │
│                        │  │ ║  247  ║  ║  12   ║  ║  0.87 ║  ║  5.2% ║ │    │
│                        │  │ ║Correls║  ║Strong ║  ║Avg R  ║  ║Trend  ║ │    │
│                        │  │ ╚═══════╝  ╚═══════╝  ╚═══════╝  ╚═══════╝ │    │
│                        │  └──────────────────────────────────────────────┘    │
│                        │                                                        │
│                        │  ┌─────────────────────┐  ┌─────────────────────┐   │
│                        │  │ 🔥 CORRELATION      │  │ 📊 TIME SERIES      │   │
│                        │  │    HEATMAP          │  │    ANALYSIS         │   │
│                        │  │                     │  │                     │   │
│                        │  │  [Interactive       │  │  [Line charts with  │   │
│                        │  │   correlation       │  │   multiple series,  │   │
│                        │  │   matrix with       │  │   trend indicators, │   │
│                        │  │   color gradients]  │  │   zoom controls]    │   │
│                        │  │                     │  │                     │   │
│                        │  └─────────────────────┘  └─────────────────────┘   │
│                        │                                                        │
│                        │  ┌─────────────────────┐  ┌─────────────────────┐   │
│                        │  │ 🕸️  NETWORK         │  │ 🏆 LEADERBOARD      │   │
│                        │  │     GRAPH           │  │                     │   │
│                        │  │                     │  │  1. GDP ↔ Stocks    │   │
│                        │  │  [Force-directed    │  │     r=0.94 ⭐⭐⭐    │   │
│                        │  │   graph showing     │  │  2. Temp ↔ Energy   │   │
│                        │  │   relationships     │  │     r=0.89 ⭐⭐⭐    │   │
│                        │  │   between datasets] │  │  3. ...             │   │
│                        │  │                     │  │                     │   │
│                        │  └─────────────────────┘  └─────────────────────┘   │
│                        │                                                        │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme

### **Primary Colors**
- **Background Dark:** `#0F172A` (Slate 900)
- **Surface Dark:** `#1E293B` (Slate 800)
- **Surface Light:** `#334155` (Slate 700)

### **Accent Colors**
- **Primary (Cyan):** `#06B6D4` - For highlights, CTAs
- **Success (Green):** `#10B981` - Positive correlations
- **Warning (Amber):** `#F59E0B` - Moderate correlations
- **Danger (Red):** `#EF4444` - Negative correlations
- **Info (Blue):** `#3B82F6` - Information elements

### **Text Colors**
- **Primary Text:** `#F1F5F9` (Slate 100)
- **Secondary Text:** `#94A3B8` (Slate 400)
- **Muted Text:** `#64748B` (Slate 500)

---

## 📊 Component Specifications

### **1. Correlation Heatmap Panel**
```
┌─────────────────────────────────────────────────┐
│ 🔥 Correlation Heatmap                      [⚙️] │
├─────────────────────────────────────────────────┤
│                                                  │
│         GDP    Stocks  Temp   CO2   Energy      │
│  GDP    1.00   0.94    0.23   0.45   0.67       │
│  Stocks 0.94   1.00    0.19   0.41   0.63       │
│  Temp   0.23   0.19    1.00   0.89   0.72       │
│  CO2    0.45   0.41    0.89   1.00   0.81       │
│  Energy 0.67   0.63    0.72   0.81   1.00       │
│                                                  │
│  Color Scale: [-1.0] ━━━━━ [0] ━━━━━ [+1.0]    │
│               Red    Gray    Green              │
├─────────────────────────────────────────────────┤
│ 📌 Hover: GDP ↔ Stocks: r=0.94, p<0.001        │
└─────────────────────────────────────────────────┘
```

**Features:**
- Interactive hover tooltips showing correlation coefficient and p-value
- Click to drill down into detailed analysis
- Color gradient from red (negative) → gray (zero) → green (positive)
- Filter controls for threshold adjustment

---

### **2. Time Series Visualization**
```
┌─────────────────────────────────────────────────┐
│ 📈 Time Series Analysis                    [⚙️] │
├─────────────────────────────────────────────────┤
│  Select Variables: [GDP ▼] [Stocks ▼]          │
│  Time Range: [Last 30 days ▼]                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  │                           ╱╲                 │
│  │                        ╱╲╱  ╲                │
│  │                     ╱╲╱       ╲              │
│  │                  ╱╲╱           ╲╱╲           │
│  │               ╱╲╱                  ╲         │
│  │            ╱╲╱                       ╲       │
│  │         ╱╲╱                            ╲     │
│  │      ╱╲╱                                 ╲   │
│  └──────────────────────────────────────────────│
│   Jan    Feb    Mar    Apr    May    Jun       │
│                                                  │
│  ━━━ GDP (Normalized)   ━━━ Stocks (Normalized) │
├─────────────────────────────────────────────────┤
│ 💡 Insight: Strong positive correlation (r=0.94)│
│    detected. GDP leads stocks by ~3 days.       │
└─────────────────────────────────────────────────┘
```

**Features:**
- Multi-series line charts with legend
- Interactive zoom/pan controls
- Automatic normalization for comparison
- Trend indicators and annotations
- Real-time correlation coefficient display

---

### **3. Network Relationship Graph**
```
┌─────────────────────────────────────────────────┐
│ 🕸️  Correlation Network                    [⚙️] │
├─────────────────────────────────────────────────┤
│  Min Edge Weight: [0.5 ━━━●━━ 1.0]            │
├─────────────────────────────────────────────────┤
│                                                  │
│              ╭─────╮                            │
│              │ GDP │                            │
│              ╰──┬──╯                            │
│            ┌────┴────┐                          │
│      0.94 │          │ 0.67                     │
│       ╭───▼──╮   ╭──▼────╮                     │
│       │Stocks│   │Energy │                      │
│       ╰──────╯   ╰───┬───╯                     │
│                      │ 0.81                     │
│                  ╭───▼──╮                       │
│                  │ CO2  │                       │
│                  ╰───┬──╯                       │
│                      │ 0.89                     │
│                  ╭───▼──╮                       │
│                  │Temp  │                       │
│                  ╰──────╯                       │
│                                                  │
├─────────────────────────────────────────────────┤
│ Node size: # of connections                    │
│ Edge thickness: correlation strength           │
└─────────────────────────────────────────────────┘
```

**Features:**
- Force-directed graph layout
- Interactive drag-and-drop nodes
- Edge thickness represents correlation strength
- Node size represents number of connections
- Hover for detailed metrics
- Filter by minimum correlation threshold

---

### **4. Leaderboard Panel**
```
┌─────────────────────────────────────────────────┐
│ 🏆 Top Correlations                        [⚙️] │
├─────────────────────────────────────────────────┤
│                                                  │
│  #  Variables             r      p-value  Stars │
│ ─────────────────────────────────────────────── │
│  1  GDP ↔ Stocks        0.94   < 0.001   ⭐⭐⭐ │
│  2  Temp ↔ CO2          0.89   < 0.001   ⭐⭐⭐ │
│  3  CO2 ↔ Energy        0.81   < 0.001   ⭐⭐⭐ │
│  4  GDP ↔ Energy        0.67   < 0.01    ⭐⭐  │
│  5  Stocks ↔ Energy     0.63   < 0.01    ⭐⭐  │
│  6  Temp ↔ Energy       0.72   < 0.01    ⭐⭐  │
│  7  GDP ↔ CO2           0.45   < 0.05    ⭐    │
│  8  Stocks ↔ CO2        0.41   < 0.05    ⭐    │
│  9  GDP ↔ Temp          0.23   < 0.10    ─     │
│  10 Stocks ↔ Temp       0.19   < 0.10    ─     │
│                                                  │
├─────────────────────────────────────────────────┤
│ [View All 247 Correlations →]                   │
└─────────────────────────────────────────────────┘
```

**Features:**
- Sortable columns
- Star rating based on statistical significance
- Click to view detailed analysis
- Export to CSV functionality
- Pagination for large datasets

---

### **5. Quick Stats Bar**
```
┌──────────────────────────────────────────────────────────────┐
│  ╔═══════════╗  ╔═══════════╗  ╔═══════════╗  ╔═══════════╗│
│  ║    247    ║  ║     12    ║  ║   0.87    ║  ║   +5.2%   ║│
│  ║ Total     ║  ║ Strong    ║  ║ Avg       ║  ║ Trend     ║│
│  ║ Correlat. ║  ║ (r>0.7)   ║  ║ Correl.   ║  ║ Change    ║│
│  ╚═══════════╝  ╚═══════════╝  ╚═══════════╝  ╚═══════════╝│
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time statistics
- Animated counters on load
- Trend indicators (↑/↓)
- Click for detailed breakdown

---

### **6. 🔍 RELATIONSHIP CONTEXT PANEL (Pop-out Analysis)**

**⚡ KEY FEATURE - Triggered by clicking any correlation**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════════════════╗  │
│ ║  🔍 Relationship Deep Dive: GDP ↔ Stock Market             [✕]   ║  │
│ ╠═══════════════════════════════════════════════════════════════════╣  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 📊 STATISTICAL SUMMARY                                    │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  Correlation Coefficient (r):     0.94                    │  ║  │
│ ║  │  P-Value:                         < 0.001  ⭐⭐⭐          │  ║  │
│ ║  │  Confidence Interval:             [0.89, 0.97]           │  ║  │
│ ║  │  Sample Size:                     247 observations        │  ║  │
│ ║  │  Method:                          Pearson                 │  ║  │
│ ║  │  Significance:                    Highly Significant      │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 💡 NATURAL LANGUAGE EXPLANATION                           │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  "There is a very strong positive relationship between   │  ║  │
│ ║  │   GDP and Stock Market performance. When GDP increases    │  ║  │
│ ║  │   by 1%, the Stock Market tends to rise by 0.94%.        │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   This relationship is statistically significant (p<0.001)│  ║  │
│ ║  │   with 247 data points analyzed. The correlation suggests │  ║  │
│ ║  │   that economic growth (GDP) is a strong predictor of     │  ║  │
│ ║  │   stock market performance.                               │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   ⚠️  Note: Correlation does not imply causation. Other   │  ║  │
│ ║  │   factors may influence both variables."                  │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  Explanation Style: [○ Simple  ● Detailed  ○ Technical]  │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 📈 TIME SERIES OVERLAY                                    │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   GDP (Normalized)                                        │  ║  │
│ ║  │   │         ╱╲              ╱╲                            │  ║  │
│ ║  │   │      ╱╲╱  ╲          ╱╲╱  ╲                          │  ║  │
│ ║  │   │   ╱╲╱      ╲      ╱╲╱      ╲                         │  ║  │
│ ║  │   │╱╲╱          ╲  ╱╲╱          ╲                        │  ║  │
│ ║  │   └─────────────────────────────────────────             │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   Stocks (Normalized)                                     │  ║  │
│ ║  │   │         ╱╲              ╱╲                            │  ║  │
│ ║  │   │      ╱╲╱  ╲          ╱╲╱  ╲                          │  ║  │
│ ║  │   │   ╱╲╱      ╲      ╱╲╱      ╲   ← Follows GDP closely │  ║  │
│ ║  │   │╱╲╱          ╲  ╱╲╱          ╲                        │  ║  │
│ ║  │   └─────────────────────────────────────────             │  ║  │
│ ║  │    Jan   Feb   Mar   Apr   May   Jun                     │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   💡 Lag Analysis: GDP leads Stocks by ~3 days           │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 🧮 CAUSALITY ANALYSIS (Advanced)                          │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  📊 Statistical Causality Tests:                          │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  1. Granger Causality Test:                               │  ║  │
│ ║  │     GDP → Stocks:    ✅ Significant (p=0.003)  ⭐⭐⭐      │  ║  │
│ ║  │     Stocks → GDP:    ❌ Not Significant (p=0.234)         │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  2. Transfer Entropy:                                     │  ║  │
│ ║  │     Info Flow GDP→Stocks: 0.67 bits (High)  ✅           │  ║  │
│ ║  │     Info Flow Stocks→GDP: 0.12 bits (Low)   ❌           │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  3. Convergent Cross Mapping (CCM):                       │  ║  │
│ ║  │     GDP causes Stocks: ρ = 0.82 (Strong)  ⭐⭐⭐          │  ║  │
│ ║  │     Stocks causes GDP: ρ = 0.31 (Weak)    ⚠️             │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  ┌──────────────────────────────────────────┐            │  ║  │
│ ║  │  │ 🎯 CAUSAL DIRECTION CONFIDENCE            │            │  ║  │
│ ║  │  ├──────────────────────────────────────────┤            │  ║  │
│ ║  │  │                                           │            │  ║  │
│ ║  │  │       GDP ═══════════► Stocks            │            │  ║  │
│ ║  │  │                                           │            │  ║  │
│ ║  │  │       Confidence: 94% ⭐⭐⭐              │            │  ║  │
│ ║  │  │       Lag Time: 3 days                   │            │  ║  │
│ ║  │  │                                           │            │  ║  │
│ ║  │  └──────────────────────────────────────────┘            │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  💡 CAUSAL INTERPRETATION:                                │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  "Multiple statistical tests converge on the conclusion   │  ║  │
│ ║  │   that GDP growth CAUSES changes in Stock Market          │  ║  │
│ ║  │   performance, not the other way around.                  │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   - GDP changes predict future stock movements (3-day lag)│  ║  │
│ ║  │   - Information flows from GDP to Stocks (67%)            │  ║  │
│ ║  │   - This is likely a true causal relationship, not        │  ║  │
│ ║  │     spurious correlation                                  │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   ⚠️  CONFOUNDING CHECK:                                  │  ║  │
│ ║  │   Analyzed 15 potential confounding variables:            │  ║  │
│ ║  │   - Interest Rates (controlled)                           │  ║  │
│ ║  │   - Inflation (controlled)                                │  ║  │
│ ║  │   - Global Markets (controlled)                           │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │   ✅ Relationship holds after controlling for confounders"│  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  📚 Methods Explanation: [View Details ▼]                │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 🔗 RELATED CONNECTIONS                                    │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  Other variables correlated with both:                    │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  • Energy Consumption    (GDP: 0.67, Stocks: 0.63)       │  ║  │
│ ║  │  • Employment Rate       (GDP: 0.82, Stocks: 0.76)       │  ║  │
│ ║  │  • Consumer Confidence   (GDP: 0.71, Stocks: 0.88)       │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  [View Full Cluster →]                                    │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 📊 SCATTER PLOT                                           │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  Stocks                                                    │  ║  │
│ ║  │    │                                    •                 │  ║  │
│ ║  │    │                              •  •                    │  ║  │
│ ║  │    │                        •  •                          │  ║  │
│ ║  │    │                  •  •                                │  ║  │
│ ║  │    │            •  •                                      │  ║  │
│ ║  │    │      •  •                                            │  ║  │
│ ║  │    │  •                                                   │  ║  │
│ ║  │    └─────────────────────────────────────────── GDP      │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │    Regression Line: y = 0.94x + 2.3 (R² = 0.88)          │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 🎯 ACTIONABLE INSIGHTS                                    │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  1. 📈 GDP is a leading indicator for Stock Market        │  ║  │
│ ║  │     performance (3-day lead time)                         │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  2. 💰 Strong predictive relationship suggests GDP        │  ║  │
│ ║  │     forecasts can inform investment strategies            │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  3. ⚠️  Watch for GDP trend reversals as early signals    │  ║  │
│ ║  │     of market corrections                                 │  ║  │
│ ║  │                                                            │  ║  │
│ ║  │  4. 🔍 Consider energy consumption and employment as      │  ║  │
│ ║  │     secondary confirmation signals                        │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ║                                                                   ║  │
│ ║  ┌───────────────────────────────────────────────────────────┐  ║  │
│ ║  │ 🛠️  ACTIONS                                               │  ║  │
│ ║  ├───────────────────────────────────────────────────────────┤  ║  │
│ ║  │  [📊 Export Analysis]  [📈 Create Forecast]               │  ║  │
│ ║  │  [🔔 Set Alert]  [💾 Save to Dashboard]  [🔗 Share]      │  ║  │
│ ║  └───────────────────────────────────────────────────────────┘  ║  │
│ ╚═══════════════════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────────────────┘
                              [Overlay/Modal View]
```

---

#### **Relationship Context Panel - Interaction Flow**

**Trigger Points:**
1. Click any cell in the correlation heatmap
2. Click any item in the leaderboard
3. Click any edge in the network graph
4. Click "Analyze" button on any correlation

**Panel Behavior:**
- **Desktop:** Slides in from right as overlay (70% width)
- **Tablet:** Full-screen modal with close button
- **Mobile:** Full-screen takeover with back gesture

**Content Sections (Scrollable):**

1. **Statistical Summary** (Always visible at top)
   - Correlation coefficient
   - P-value with significance stars
   - Confidence interval
   - Sample size
   - Method used

2. **Natural Language Explanation** (Adaptive complexity)
   - Simple: For non-technical users
   - Detailed: Balanced explanation (default)
   - Technical: Full statistical details
   - Dynamically generated using correlation_analyzer

3. **Time Series Overlay**
   - Dual-axis normalized comparison
   - Lag/lead analysis
   - Trend indicators
   - Zoom/pan controls

4. **Causality Analysis** (Advanced Statistical Methods)
   - **Granger Causality Test**: Tests if one time series helps predict another
   - **Transfer Entropy**: Measures information flow between variables
   - **Convergent Cross Mapping (CCM)**: Detects nonlinear causal relationships
   - **Directed Acyclic Graphs (DAG)**: Visual causal network structure
   - **Instrumental Variables**: Identifies true causal effects
   - **Propensity Score Matching**: Controls for confounding variables
   - Directional relationship indicators (A → B, B → A, A ↔ B)
   - Causal strength estimates
   - Interpretation guidance with confidence levels

5. **Related Connections**
   - Other variables in the cluster
   - Potential confounding variables
   - Network context

6. **Scatter Plot with Regression**
   - Individual data points
   - Regression line
   - R² value
   - Outlier highlighting

7. **Actionable Insights**
   - Business implications
   - Predictive opportunities
   - Risk warnings
   - Strategic recommendations

8. **Action Buttons**
   - Export to PDF/CSV
   - Create forecast based on relationship
   - Set up alerts for changes
   - Save configuration
   - Share analysis link

---

#### **Key Features of Relationship Context Panel**

**🎯 Context Awareness:**
- Remembers which visualization triggered it
- Highlights related elements in other panels
- Maintains filter state

**📊 Dynamic Content:**
- Fetches fresh analysis from backend
- Caches recent analyses
- Updates in real-time if data changes

**🎨 Visual Hierarchy:**
- Most important info (stats) at top
- Scrollable detailed sections
- Progressive disclosure (expand/collapse)

**⚡ Performance:**
- Lazy-loads visualizations
- Preloads common correlations
- Smooth animations (< 300ms transition)

**♿ Accessibility:**
- Keyboard navigation (Tab, Esc to close)
- Screen reader friendly
- High contrast mode support

---

## 🔧 Interactive Features

### **Data Source Controls**
```
┌─────────────────────────────────────────────────┐
│ 🔌 Active Data Sources                     [+]  │
├─────────────────────────────────────────────────┤
│  ✅ Alpha Vantage (Stocks)      Updated: 2m ago │
│  ✅ World Bank (GDP)            Updated: 1h ago │
│  ✅ USGS (Earthquakes)          Updated: 5m ago │
│  ✅ NASA EONET (Climate)        Updated: 15m ago│
│  ⏸️  PubMed (Research)          Paused          │
│  ❌ OpenWeather                 API Key Missing │
└─────────────────────────────────────────────────┘
```

### **Analysis Controls**
```
┌─────────────────────────────────────────────────┐
│ ⚙️  Analysis Settings                           │
├─────────────────────────────────────────────────┤
│  Method:     [● Pearson  ○ Spearman ○ Kendall] │
│  Threshold:  [0.5 ━━━●━━━━ 1.0]                │
│  Time Range: [Last 30 days ▼]                  │
│  Min P-Value:[0.05 ▼]                          │
│                                                  │
│  [🔄 Refresh Analysis]  [💾 Save Configuration] │
└─────────────────────────────────────────────────┘
```

---

## 📱 Responsive Design

### **Desktop (1920x1080+)**
- Full 4-panel layout as shown above
- Sidebar always visible
- All visualizations displayed simultaneously

### **Tablet (768-1920px)**
- Collapsible sidebar (hamburger menu)
- 2-column grid for panels
- Slightly reduced chart sizes

### **Mobile (< 768px)**
- Fully collapsed sidebar (bottom navigation)
- Single column stacked panels
- Swipeable carousel for visualizations
- Simplified stat cards

---

## 🎭 Animation & Interactions

### **Page Load**
1. Fade in navigation (0.2s delay)
2. Stats bar counts up from zero (0.5s animation)
3. Panels fade in sequentially (0.3s stagger)
4. Charts draw from left to right (1s smooth animation)

### **Hover States**
- Panels lift with subtle shadow
- Buttons brighten on hover
- Chart elements highlight on mouseover

### **Data Updates**
- Smooth transitions when filters change
- Loading skeleton screens during data fetch
- Success/error toast notifications

---

## 🚀 Technical Stack Recommendation

### **Frontend Framework**
**Option 1: React + Recharts (Recommended)**
- Modern, component-based
- Excellent charting library (Recharts)
- Large ecosystem

**Option 2: Vue 3 + Chart.js**
- Simpler learning curve
- Flexible charting with Chart.js
- Good performance

**Option 3: Vanilla JS + D3.js (If you want full control)**
- No framework overhead
- Ultimate customization with D3
- Lighter bundle size

### **UI Component Library**
- **Tailwind CSS** - For styling
- **Headless UI** - For accessible components
- **Lucide Icons** - For modern icon set

### **Charting Libraries**
- **Recharts** - React-friendly, declarative
- **Chart.js** - Simple and performant
- **D3.js** - Maximum customization
- **Plotly.js** - Interactive scientific charts

---

## 📋 Implementation Phases

### **Phase 1: Core Structure (Week 1)**
- Navigation layout
- Page routing
- Stats bar
- Basic styling system

### **Phase 2: Visualizations (Week 2)**
- Heatmap component
- Time series chart
- Network graph
- Leaderboard table

### **Phase 3: Interactivity (Week 3)**
- Data source controls
- Filter/settings panel
- Real-time updates
- API integration

### **Phase 4: Polish (Week 4)**
- Animations
- Responsive design
- Performance optimization
- Cross-browser testing

---

## ✅ Review Checklist

**Before we proceed, please review:**

1. **Layout Structure** - Does the 4-panel dashboard work for you?
2. **Color Scheme** - Happy with dark theme and cyan accents?
3. **Component Priority** - Which visualization is most important?
4. **Interactivity Level** - Too much? Too little?
5. **Mobile Support** - Do you need full mobile functionality?
6. **Technical Stack** - React preferred or open to alternatives?

**Feedback Areas:**

- [ ] Overall layout and structure
- [ ] Color scheme and typography
- [ ] Visualization types and arrangement
- [ ] Interactive features
- [ ] Responsive design priorities
- [ ] Technical stack preference

---

## 🎯 Next Steps

Once you approve this design:

1. Set up frontend project structure
2. Implement core layout and navigation
3. Build visualization components
4. Integrate with FastAPI backend
5. Deploy to Railway alongside API

**Estimated Timeline:** 2-4 weeks for full implementation

---

**What are your thoughts? Any changes or preferences?**
