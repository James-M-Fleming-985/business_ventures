# UI Layout Documentation

## Overview
This document outlines the user interface layouts, tab structures, and feature specifications for the Opti Royale Clash Royale analysis application.

**Last Updated:** July 27, 2025  
**Version:** 2.0  
**Framework:** Next.js 14 with TypeScript and Tailwind CSS

---

## Dashboard Structure

### Main Navigation Tabs
The dashboard contains the following main tabs:
- **Overview** - Main dashboard with feature overview
- **Leaderboard** - Player rankings and statistics  
- **Achievements** - User achievements and progress tracking
- **Profile** - User profile management
- **Battle Analysis** - Video analysis and AI recommendations ⭐
- **File Management** - Personal video library and storage management 📂 *(Future Tab 4)*

---

## Tab 4: File Management (Future Feature)

### Overview
**Purpose:** Centralized video library management for user's uploaded gameplay videos  
**Target Implementation:** Phase 3 (Post-MVP)  
**Integration:** Connected to Window 1 upload system in Battle Analysis tab

### Core Features

#### 📂 **Personal Video Library**
- **Video Grid View**
  - Thumbnail previews with duration overlay
  - Battle type badges (1v1, 2v2, Tournament)
  - Date uploaded and file size information
  - Quick filter by arena, deck type, or outcome

- **Folder Organization**
  - Custom folder creation for categorization
  - Auto-categorization by arena level
  - Season-based organization
  - Deck archetype grouping

- **Video Metadata Management**
  - Battle results (Win/Loss/Draw)
  - Trophy range at time of recording
  - Deck composition tagging
  - Strategic notes and annotations

#### 🔍 **Advanced Search & Filter**
- **Search Capabilities**
  - Full-text search in video notes
  - Card-based search ("Find videos with Hog Rider")
  - Date range filtering
  - Trophy range filtering

- **Smart Collections**
  - Auto-generated collections (e.g., "Close Losses", "Perfect Games")
  - Deck-based grouping
  - Performance analysis clusters
  - Learning objective collections

#### ☁️ **Cloud Storage Integration**
- **Storage Management**
  - Usage quota visualization
  - Automatic compression for old videos
  - Tiered storage (active vs archive)
  - Backup and sync status

- **Cross-Device Sync**
  - Mobile app synchronization
  - Web browser access
  - Download for offline analysis
  - Selective sync preferences

#### 📊 **Library Analytics**
- **Storage Statistics**
  - Total videos uploaded
  - Storage usage breakdown
  - Upload frequency tracking
  - Analysis completion rates

- **Performance Insights**
  - Win rate by video category
  - Most analyzed battle types
  - Improvement tracking over time
  - Strategic pattern identification

### Technical Architecture

#### Database Schema Extensions:
```sql
-- User File Directory Table
CREATE TABLE user_video_libraries (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR REFERENCES users(id),
  folder_path VARCHAR NOT NULL,
  folder_name VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced Video Metadata
ALTER TABLE videos ADD COLUMN (
  folder_id INTEGER REFERENCES user_video_libraries(id),
  thumbnail_url VARCHAR,
  battle_type VARCHAR, -- '1v1', '2v2', 'tournament'
  arena_level INTEGER,
  trophy_range VARCHAR,
  user_notes TEXT,
  tags VARCHAR[], -- Array of custom tags
  analysis_status VARCHAR DEFAULT 'pending',
  storage_tier VARCHAR DEFAULT 'active'
);
```

#### File System Integration:
```typescript
interface FileManagementSystem {
  // Folder Operations
  createFolder: (name: string, parentId?: string) => Promise<Folder>;
  deleteFolder: (folderId: string) => Promise<void>;
  moveVideo: (videoId: string, folderId: string) => Promise<void>;
  
  // Video Operations
  uploadVideo: (file: File, folderId?: string) => Promise<Video>;
  deleteVideo: (videoId: string) => Promise<void>;
  generateThumbnail: (videoId: string) => Promise<string>;
  
  // Search & Filter
  searchVideos: (query: SearchQuery) => Promise<Video[]>;
  getVideosByFolder: (folderId: string) => Promise<Video[]>;
  getVideosByTags: (tags: string[]) => Promise<Video[]>;
  
  // Storage Management
  getStorageUsage: () => Promise<StorageInfo>;
  archiveOldVideos: (olderThan: Date) => Promise<void>;
  optimizeStorage: () => Promise<void>;
}
```

---

## Battle Analysis Tab - 3-Window Layout

### Layout Overview
The Battle Analysis tab features a revolutionary **3-window layout** designed for comprehensive Clash Royale gameplay analysis.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Battle Analysis Header                       │
├───────────────┬─────────────────────────┬───────────────────────────┤
│   WINDOW 1    │        WINDOW 2         │         WINDOW 3          │
│  (Blue Border)│     (Yellow Border)     │      (Green Border)       │
│               │                         │                           │
│ Video         │    Video Player &       │    Game Data &            │
│ Selection     │    Controls             │    Analysis Results       │
│ & Upload      │                         │                           │
│               │                         │                           │
└───────────────┴─────────────────────────┴───────────────────────────┘
```

### Window 1: Video Selection & Upload (Left Panel)
**Theme:** Blue gradient with blue border  
**Purpose:** Comprehensive video management, file system integration, and navigation controls

#### Core Features:

##### 📁 **File Upload & Management**
- **Single Video Upload**
  - Direct device file selection via file picker
  - Drag & drop functionality (in parent component)
  - Browser-based file validation and conversion
  - Support: MP4, MOV, AVI, WebM formats

- **Multiple Video Upload** ⭐
  - Batch file selection from device
  - Queue management for processing multiple videos
  - Individual video preview thumbnails
  - Bulk analysis capabilities

- **User File Directory Integration** 📂
  - Personal video library management
  - Integration with **Tab 4: File Management** (future feature)
  - Video categorization and tagging
  - Storage quota tracking and management

##### 🔗 **Clash Royale API Integration**
- **Battle Log Import** ⭐
  - Direct connection to Clash Royale API
  - Automatic battle history retrieval
  - Match metadata association with videos
  - Player statistics integration

- **Match Data Correlation**
  - Automatic deck detection from API
  - Trophy range and arena matching
  - Opponent analysis data import
  - Battle result validation

##### 📱 **Cross-Platform File Transfer** (Future Feature)
- **iOS/iPad Integration**
  - AirDrop compatibility
  - iCloud Drive integration
  - Photos app video import
  - Safari upload optimization

- **Mobile App File Sync**
  - Native mobile app video capture
  - Automatic cloud synchronization
  - Background upload capabilities
  - Mobile-optimized compression

##### 🔄 **File Conversion & Processing**
- **Browser-Based Conversion**
  - WebAssembly video processing
  - Format standardization (MP4 H.264)
  - Resolution optimization for analysis
  - Compression for storage efficiency

- **Mobile App Conversion**
  - Native iOS/Android video processing
  - Hardware-accelerated encoding
  - Quality presets for different devices
  - Bandwidth-aware upload optimization

#### Current Implementation Status:
- ✅ **Current Video Info Display**
- ✅ **Basic Upload Controls**
- ✅ **Quick Navigation Buttons**
- ✅ **Analysis History Panel**
- ⚠️ **Single Video Upload** (UI ready, backend pending)
- 🔄 **Multiple Video Upload** (planned for Phase 2)
- 🔄 **Battle Log API Integration** (Phase 2)
- 🔄 **File Directory System** (Phase 3)
- 🔄 **Cross-Platform Transfer** (Phase 4)

#### Technical Architecture:

##### File Upload Flow:
```typescript
interface VideoUploadFlow {
  // Step 1: File Selection
  selectFiles: (multiple: boolean) => FileList;
  
  // Step 2: Client-side Processing
  validateFormat: (file: File) => boolean;
  generateThumbnail: (file: File) => Promise<Blob>;
  extractMetadata: (file: File) => VideoMetadata;
  
  // Step 3: Conversion (if needed)
  convertToStandard: (file: File) => Promise<File>;
  compressForUpload: (file: File) => Promise<File>;
  
  // Step 4: Upload & Storage
  uploadToCloud: (file: File) => Promise<string>;
  saveToUserDirectory: (metadata: VideoMetadata) => Promise<void>;
  
  // Step 5: Integration
  loadIntoAnalyzer: (videoUrl: string) => void;
}
```

##### API Integration Architecture:
```typescript
interface ClashRoyaleAPIIntegration {
  // Battle Log Retrieval
  getBattleLog: (playerTag: string) => Promise<Battle[]>;
  getMatchDetails: (battleId: string) => Promise<MatchData>;
  
  // Video Correlation
  correlateVideoWithBattle: (
    video: VideoFile, 
    battles: Battle[]
  ) => Promise<MatchData | null>;
  
  // Automatic Processing
  processMatchVideo: (
    video: VideoFile, 
    matchData: MatchData
  ) => Promise<AnalysisResult>;
}
```

#### Visual Design:
```css
Background: bg-gray-800
Border: border-2 border-blue-400
Header: bg-gradient-to-r from-blue-600 to-purple-600
Icon: Upload (Lucide React)
```

### Window 2: Video Player & Controls (Center Panel)
**Theme:** Yellow/orange gradient with yellow border  
**Purpose:** Primary video viewing and analysis trigger

#### Features:
- **Video Display**
  - Full-width video player (h-80)
  - Object-cover scaling
  - Analysis overlay markers

- **Video Controls**
  - Play/Pause toggle
  - Restart button (RotateCcw)
  - Progress slider with seek functionality
  - Time display (current/total)

- **Analysis Interface**
  - "Analyze This Moment" button
  - Loading state with spinner
  - Gradient styling (green-to-blue)
  - Hover effects and scaling

- **Analysis Overlay**
  - Positioned recommendation markers
  - Animated pulse effects
  - Target icon indicators
  - Non-interactive overlay layer

#### Visual Design:
```css
Background: bg-gray-900
Border: border-2 border-yellow-400
Header: bg-gradient-to-r from-yellow-500 to-orange-500
Header Text: text-black (high contrast)
Analysis Button: bg-gradient-to-r from-green-500 to-blue-500
```

### Window 3: Game Data & Analysis (Right Panel)
**Theme:** Green gradient with green border  
**Purpose:** Analysis results and game data display

#### Features:
- **Current Analysis Results** (Dynamic)
  - Recommended card display with rarity colors
  - Confidence percentage with progress bar
  - Strategic reasoning text
  - Elixir state comparison (player vs opponent)
  - Save/Share action buttons

- **Battle Decks** (When match data available)
  - Player deck grid (4 columns)
  - Opponent deck grid (4 columns)
  - Card level and elixir indicators
  - Rarity-based gradient colors

- **Development Log**
  - Real-time implementation status
  - Feature completion indicators
  - Backend integration status
  - Color-coded progress markers

- **Session Statistics**
  - Analyses run counter
  - Video duration tracking
  - Current playback position
  - Progress percentage

#### Visual Design:
```css
Background: bg-gray-800
Border: border-2 border-green-400
Header: bg-gradient-to-r from-green-600 to-teal-600
Max Height: max-h-[500px] with overflow-y-auto
Scrollable Content: Custom scrollbar styling
```

### Responsive Behavior
- **Large screens (lg+):** Full 3-window layout
- **Medium screens:** Stacked layout maintains window structure
- **Small screens:** Single column with preserved functionality

### Card Rarity Color System
```css
Legendary: from-orange-400 to-yellow-500
Epic: from-purple-400 to-pink-500
Rare: from-orange-300 to-orange-500
Common: from-gray-300 to-gray-400
```

---

---

## Engine Integration Requirements

### Computer Vision Engine (CV-Analyzer Service)
**Location:** `/services/cv-analyzer/`  
**Technology Stack:** Python + OpenCV + TensorFlow/PyTorch  
**Purpose:** Real-time video analysis and card detection

#### Core CV Capabilities Required:
1. **Frame-by-Frame Analysis** (30fps processing)
   - Real-time card detection with 99%+ accuracy
   - Game board state extraction
   - Unit position tracking
   - Elixir count recognition

2. **Card Recognition System**
   - 120+ card types including all evolutions
   - Rarity detection (Common, Rare, Epic, Legendary, Champion)
   - Level identification (1-15)
   - Evolution state detection (34 evolvable cards)

3. **Game State Detection**
   - Tower health monitoring (King + Princess towers)
   - Current elixir tracking (both players)
   - Unit positioning on 18x32 tile grid
   - Time remaining calculation

4. **Strategic Analysis**
   - Building pull range calculations
   - Sight range modeling for engagement prediction
   - Targeting type classification (building-only, troop-only, both)
   - Indirect damage area calculations

#### Integration Points with VideoAnalyzer:
- **Window 2**: Real-time overlay markers showing analysis results
- **Window 3**: Confidence scores, card recommendations, game state display
- **Analysis Button**: Triggers CV analysis of current video frame

### Machine Learning Pipeline (ML-Pipeline Service)
**Location:** `/services/ml-pipeline/`  
**Technology Stack:** MLflow + Feast + Azure ML  
**Purpose:** Continuous model training and optimization recommendations

#### Core ML Features:
1. **Strategic Recommendation Engine**
   - Optimal card placement calculation
   - Counter-strategy suggestions
   - Elixir efficiency optimization
   - Win probability prediction

2. **User Personalization**
   - Individual skill level assessment
   - Preferred playstyle analysis
   - Improvement area identification
   - Custom recommendation tuning

3. **Meta Analysis**
   - Current meta deck strength calculation
   - Balance change impact assessment
   - Card synergy scoring
   - Tournament-level strategy adaptation

#### Feature Store Integration:
```python
# Key features tracked for ML model
features = {
    "game_context": ["player_trophies", "elixir_advantage", "tower_health"],
    "user_performance": ["avg_placement_score", "win_rate", "skill_level"],
    "card_effectiveness": ["synergy_score", "counter_presence", "meta_strength"],
    "realtime_state": ["board_state", "immediate_threats", "optimal_responses"]
}
```

### Game Mechanics Engine
**Location:** Integrated across all services  
**Source:** `/CLASH_ROYALE_MECHANICS_SPEC.md`  
**Purpose:** Accurate game rule modeling

#### Critical Mechanics Implemented:
1. **Evolution System** (34 cards)
   - Enhanced stats and special abilities
   - 2-3 cycle evolution requirements
   - Evolution-specific targeting changes

2. **Building Interaction System**
   - Pull ranges for defensive buildings
   - Building-only targeting cards
   - Kiting mechanics and pathfinding

3. **Targeting Classifications**
   - Air/Ground targeting restrictions
   - Building vs Troop targeting priorities
   - Sight range engagement rules

4. **Indirect Damage Systems**
   - Splash damage calculations
   - Aura effect modeling
   - Chain reaction mechanics

### Clash Royale API Integration
**Location:** `/services/clash-royale-api/`  
**Purpose:** Real-time game data synchronization

#### API Capabilities:
1. **Player Data Sync**
   - Live trophy counts
   - Deck compositions
   - Battle history
   - Clan information

2. **Meta Tracking**
   - Balance change detection
   - Card usage statistics
   - Arena-specific meta shifts
   - Tournament results analysis

3. **Match Data Enhancement**
   - Official battle results
   - Opponent deck information
   - Arena context
   - Seasonal variations

### Performance Requirements by Engine

#### CV-Analyzer Performance Targets:
- **Analysis Speed**: <2 seconds per frame analysis
- **Accuracy**: 99%+ card detection rate
- **Concurrent Processing**: 1000+ simultaneous analyses
- **GPU Utilization**: CUDA-accelerated with CuPy

#### ML-Pipeline Performance Targets:
- **Recommendation Generation**: <100ms response time
- **Model Training**: Continuous retraining with new data
- **Feature Store**: Real-time feature serving via Redis
- **Prediction Accuracy**: 85%+ strategic recommendation success rate

#### Integration Architecture:
```
VideoAnalyzer Component
├── CV Analysis Request → CV-Analyzer Service
│   ├── Frame Processing (OpenCV + TensorFlow)
│   ├── Card Detection (YOLO/ResNet models)
│   └── Game State Extraction
│
├── Strategic Analysis → ML-Pipeline Service  
│   ├── Feature Engineering (Feast)
│   ├── Model Inference (MLflow)
│   └── Recommendation Generation
│
└── Real-time Data → Clash Royale API Service
    ├── Player Statistics
    ├── Meta Information
    └── Match Context
```

---

## Implementation Status

### ✅ Completed Features
- [x] 3-window responsive grid layout
- [x] Video player with full controls
- [x] Analysis overlay system
- [x] Mock data integration
- [x] Upload functionality integration
- [x] Session statistics tracking
- [x] Analysis history storage
- [x] Card rarity visualization
- [x] Development status logging

### 🔄 In Progress
- [ ] Real video file handling
- [ ] Backend API integration
- [ ] Analysis algorithm connection
- [ ] Match data population

### ⚠️ Known Issues
- Demo video URL (placeholder)
- Backend services disconnected
- Mock analysis data only
- Upload requires parent component integration

---

## Technical Implementation

### Component Structure
```
dashboard.tsx
├── BattleAnalysisTab
    ├── Upload Interface (drag & drop)
    ├── Demo Mode Banner
    └── VideoAnalyzer Component
        ├── Match Header (conditional)
        ├── Debug Banner (temporary)
        └── 3-Window Grid
            ├── Window 1: Upload/Selection
            ├── Window 2: Video Player
            └── Window 3: Analysis Data
```

### Key Props & State
```typescript
interface VideoAnalyzerProps {
  videoUrl: string;
  matchData?: MatchData;
  onAnalysisComplete?: (result: AnalysisResult) => void;
}

// Key state variables:
- isPlaying: boolean
- currentTime: number
- duration: number
- isAnalyzing: boolean
- analysisResult: AnalysisResult | null
- savedAnalyses: AnalysisResult[]
```

### Styling Framework
- **CSS Framework:** Tailwind CSS
- **Icons:** Lucide React
- **Layout:** CSS Grid with responsive breakpoints
- **Animations:** Tailwind transitions and transforms
- **Color Scheme:** Clash Royale inspired (blues, purples, golds)

---

## Future Enhancements

### Planned Features
1. **Real-time Analysis Engine**
   - Computer vision integration
   - Card detection algorithms
   - Position tracking
   - Elixir calculation

2. **Enhanced Video Controls**
   - Frame-by-frame stepping
   - Speed adjustment controls
   - Multiple analysis markers
   - Timeline annotations

3. **Advanced Analytics**
   - Win rate predictions
   - Deck synergy analysis
   - Counter-strategy suggestions
   - Performance metrics

4. **Social Features**
   - Analysis sharing
   - Community discussions
   - Replay competitions
   - Expert reviews

### UI/UX Improvements
- [ ] Keyboard shortcuts
- [ ] Dark/light theme toggle
- [ ] Window resize handles
- [ ] Minimap navigation
- [ ] Analysis timeline
- [ ] Export functionality

---

## Notes for Developers

### Design Principles
1. **Information Density:** Each window serves a specific purpose without overlap
2. **Visual Hierarchy:** Color coding helps users understand different data types
3. **Progressive Disclosure:** Complex information revealed as needed
4. **Responsive Design:** Layout adapts to different screen sizes gracefully

### Maintenance Guidelines
- Update this document when adding new features
- Maintain consistent color schemes across windows
- Test responsive behavior on all breakpoints
- Keep development status section current
- Document any breaking changes to the layout

### Debug Features
- Green banner indicates new layout version loaded
- Development log shows real-time status
- Session stats help track user engagement
- Console logging for analysis events

---

**Document Version:** 2.1  
**Component Version:** VideoAnalyzer v2.0  
**Layout Status:** ✅ Implemented and Active

---

## 📋 Analysis Summary & Recommendations

### 🔍 Key Findings from Document Review

#### ✅ Strengths Identified:
1. **Comprehensive Engine Architecture**: Well-planned separation of CV, ML, and API services
2. **Detailed Game Mechanics**: Thorough documentation of Clash Royale mechanics including evolutions
3. **Performance Targets**: Clear metrics for each engine component
4. **Feature Store Integration**: Proper ML feature engineering with Feast framework
5. **Enterprise-Scale Planning**: 100K+ concurrent user capacity with Azure infrastructure

#### ⚠️ Critical Gaps & Challenges:

##### 1. **Computer Vision Complexity**
- **Challenge**: 99%+ accuracy requirement for 120+ cards including 34 evolutions
- **Impact**: Extremely difficult to achieve with varying video qualities, angles, and lighting
- **Recommendation**: Start with 90% accuracy target and improve iteratively

##### 2. **Real-Time Processing Bottleneck**
- **Challenge**: <2 second analysis time for 30fps video processing
- **Impact**: Requires significant GPU infrastructure ($$$)
- **Recommendation**: Implement analysis on pause/frame selection rather than continuous

##### 3. **Game State Extraction Difficulty**
- **Challenge**: Extracting elixir counts, tower health, exact unit positions from video
- **Impact**: Core to strategic recommendations but technically very challenging
- **Recommendation**: Focus on card placement analysis first, add state detection later

##### 4. **Evolution System Complexity**
- **Challenge**: 34 evolvable cards with special abilities and enhanced stats
- **Impact**: Significantly increases ML model complexity
- **Recommendation**: Implement base cards first, add evolutions as phase 2

#### 🎯 Recommended Implementation Phases:

##### Phase 1: Basic Card Detection (Weeks 1-4)
```
Priority 1: Detect 20 most common cards with 85% accuracy
Priority 2: Basic placement recommendations (good/bad positions)
Priority 3: Simple confidence scoring system
```

##### Phase 2: Enhanced Analysis (Weeks 5-8)
```
Priority 1: Full card library (120+ cards)
Priority 2: Game state extraction (elixir, towers)
Priority 3: Strategic reasoning display
```

##### Phase 3: Advanced Features (Weeks 9-12)
```
Priority 1: Evolution card detection
Priority 2: Meta-specific recommendations
Priority 3: User personalization
```

### 🔧 Technical Architecture Recommendations

#### VideoAnalyzer UI Adaptations Needed:
1. **Window 2 Enhancements**:
   - Add "Processing..." states for CV analysis
   - Implement error handling for failed analysis
   - Add confidence indicators for detection quality

2. **Window 3 Data Flow**:
   - Design fallback displays when engines are unavailable
   - Add progressive disclosure for complex analysis results
   - Implement real-time status indicators for each engine

3. **Performance Optimization**:
   - Implement analysis caching to avoid re-processing
   - Add video quality assessment before analysis
   - Include user feedback loops for ML model improvement

#### Engine Integration Strategy:
```typescript
// Recommended service integration pattern
interface AnalysisEngine {
  cv_analyzer: {
    status: 'online' | 'offline' | 'degraded';
    confidence: number;
    processing_time: number;
  };
  ml_pipeline: {
    status: 'online' | 'offline' | 'degraded';
    model_version: string;
    feature_completeness: number;
  };
  clash_api: {
    status: 'online' | 'offline' | 'degraded';
    data_freshness: number;
    rate_limit_remaining: number;
  };
}
```

### 💡 Strategic Recommendations

#### 1. Start with MVP Approach
- Focus on basic card detection before advanced game state analysis
- Implement manual game state input as fallback
- Build user feedback system to improve ML models

#### 2. Progressive Enhancement
- Begin with popular cards (80/20 rule)
- Add complexity gradually based on user feedback
- Implement A/B testing for recommendation accuracy

#### 3. User Experience Priority
- Ensure UI remains responsive even with slow analysis
- Provide clear feedback about analysis quality/confidence
- Allow users to override AI recommendations

#### 4. Infrastructure Scaling
- Start with single GPU instance for MVP
- Implement horizontal scaling based on user growth
- Use Azure Container Instances for cost-effective scaling

### 🚨 Risk Mitigation

#### High-Risk Areas:
1. **CV Accuracy**: May not achieve 99% target initially
2. **Processing Speed**: Real-time analysis may require significant infrastructure
3. **Game Updates**: Clash Royale updates may break detection models
4. **User Adoption**: Complex analysis may overwhelm casual users

#### Mitigation Strategies:
- Implement graceful degradation when engines fail
- Build manual override capabilities
- Create user education/onboarding flow
- Plan for regular model retraining cycles

---
