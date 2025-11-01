# Immersive Displays MVP

Minimum Viable Product for testing the seasonal LED curtain display concept with web-based preview and hardware integration pathway.

## Project Vision

Create a seasonal installation system (Halloween, Christmas, Easter) with:
- **High-density LED curtains** (60-144 LEDs/meter vs competitor's 10-20 LEDs/meter)
- **Multi-layer depth rendering** (background, midground, foreground)
- **AI-generated scenes** from natural language descriptions
- **Audio synchronization** with soundscapes and beat-reactive lighting
- **Mobile & web control** for scene selection and customization

## MVP Structure

### Phase 1: Web Preview System (Current Focus)
Build a web application that simulates the complete experience:
- Canvas-based LED curtain visualization
- Real-time scene rendering with multi-layer effects
- Audio playback with beat detection
- Scene templates (Halloween, Christmas, Easter)
- AI scene description interface (simulated for MVP)

**Goal**: Validate the product concept and user experience before hardware investment

### Phase 2: Hardware Integration (Future)
Connect the web system to physical LED controllers:
- ESP32 WebSocket/HTTP communication
- Real-time LED control (WS2812B/SK6812)
- Physical speaker integration
- Hardware configuration tools

## Directory Structure

```
mvp/
├── web-preview/              # Phase 1: Web-based visualization
│   ├── index.html           # Main application page
│   ├── styles.css           # UI styling
│   ├── src/
│   │   ├── led-renderer.js  # Canvas LED curtain simulator
│   │   ├── scene-engine.js  # Multi-layer scene management
│   │   ├── audio-sync.js    # Beat detection & synchronization
│   │   ├── ai-interface.js  # Scene generation UI (simulated)
│   │   ├── scenes/          # Scene templates
│   │   │   ├── halloween.js
│   │   │   ├── christmas.js
│   │   │   └── easter.js
│   │   └── audio/           # Audio processing utilities
│   └── assets/
│       └── sounds/          # Audio files for scenes
│
├── hardware-integration/     # Phase 2: Physical LED control
│   ├── esp32-firmware/      # ESP32 controller code
│   ├── api-bridge/          # Web-to-hardware API
│   └── README.md            # Hardware setup guide
│
└── README.md                # This file
```

## Development Roadmap

### Week 1: Web Preview Foundation
- [x] Set up MVP structure
- [ ] Create LED canvas renderer
- [ ] Implement basic scene engine
- [ ] Build UI layout

### Week 2: Scene & Audio
- [ ] Create 3 seasonal scene templates
- [ ] Implement audio synchronization
- [ ] Add beat detection visualization
- [ ] Build AI scene description UI

### Week 3: Polish & Testing
- [ ] User testing and feedback
- [ ] Performance optimization
- [ ] Mobile responsive design
- [ ] Documentation

### Week 4+: Hardware Pathway
- [ ] Design WebSocket API for ESP32
- [ ] Create hardware integration plan
- [ ] Source LED curtain components
- [ ] Build first physical prototype

## Technical Stack

**Web Preview:**
- Vanilla JavaScript (no framework dependencies for simplicity)
- HTML5 Canvas API for LED visualization
- Web Audio API for beat detection
- CSS Grid/Flexbox for responsive layout

**Future Hardware:**
- ESP32 DevKit (WiFi/Bluetooth)
- WS2812B/SK6812 addressable LEDs
- FastLED library for LED control
- WebSocket for real-time communication

## Getting Started

1. Open `web-preview/index.html` in a modern browser
2. Select a seasonal theme (Halloween, Christmas, Easter)
3. Preview the LED curtain visualization with audio
4. Test AI scene generation interface
5. Experiment with scene customization

No build process or dependencies required for Phase 1!

## Success Criteria

**MVP is successful if:**
- ✅ Visual experience clearly demonstrates multi-layer depth effects
- ✅ Audio synchronization is engaging and reactive
- ✅ Scene templates showcase competitive advantage (6x LED density, AI generation)
- ✅ User feedback validates $1500-2000 price point
- ✅ Technical approach proves viable for hardware implementation

**Next Phase Decision:**
- If validated → Invest in hardware prototype and ESP32 integration
- If issues found → Iterate on web preview until concept is compelling
