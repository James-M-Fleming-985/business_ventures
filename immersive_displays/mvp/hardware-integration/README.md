# Hardware Integration Guide

This directory will contain the code and documentation needed to connect the web preview system to physical LED hardware.

## 🚧 Coming Soon

Phase 2 of the MVP will include:

### ESP32 Firmware
- WebSocket client for real-time LED control
- FastLED library integration
- WiFi configuration system
- OTA (Over-The-Air) updates

### API Bridge
- WebSocket server for LED communication
- Scene-to-hardware translation layer
- Device discovery and management
- Performance optimization for real-time control

### Setup Documentation
- Hardware assembly guide
- LED wiring diagrams
- Power supply calculations
- Troubleshooting guide

## Current Status

**Phase 1 (Current):** Web preview system complete ✅
**Phase 2 (Next):** Hardware integration - Coming after validation

## Quick Hardware Overview

### Required Components
1. **ESP32 DevKit** - Main controller ($10-15)
2. **WS2812B/SK6812 LED Strips** - Addressable RGB LEDs
3. **5V Power Supply** - 60W per 100 LEDs recommended
4. **Level Shifter** - 3.3V to 5V signal conversion
5. **Capacitors** - 1000µF per power line recommended
6. **Resistor** - 470Ω for data line protection

### LED Strip Specifications
- **Type:** WS2812B (most common) or SK6812 (RGBW option)
- **Voltage:** 5V DC
- **Current:** ~60mA per LED at full white
- **Density:** 60, 100, or 144 LEDs/meter
- **Protocol:** Single-wire with timing-based data

### Communication Architecture
```
Web Browser (Canvas Preview)
    ↓ WebSocket
API Bridge Server (Node.js/Python)
    ↓ WebSocket
ESP32 Controller (WiFi)
    ↓ FastLED Library
WS2812B LED Strip (Physical Display)
```

### Power Calculation Example
For a 3m × 2m curtain at 100 LEDs/meter:
- Total LEDs: ~600
- Max current: 600 × 0.06A = 36A (at full white)
- Typical usage: ~12-18A (colored scenes)
- Recommended PSU: 5V 20A (100W) for safety margin

## Development Roadmap

### Week 5-6: Hardware Prototype
- [ ] Source and order components
- [ ] Build first small-scale test (1m × 0.5m)
- [ ] Develop ESP32 firmware skeleton
- [ ] Test basic LED control

### Week 7-8: Communication Layer
- [ ] Implement WebSocket protocol
- [ ] Create scene translation layer
- [ ] Optimize for real-time performance
- [ ] Test latency and synchronization

### Week 9-10: Integration & Testing
- [ ] Connect web interface to hardware
- [ ] Validate all scenes work on physical LEDs
- [ ] Audio sync with hardware
- [ ] Performance tuning

### Week 11-12: Polish & Documentation
- [ ] Create installation guides
- [ ] Record demo videos
- [ ] Write troubleshooting docs
- [ ] Prepare for user testing

## Testing the Web Preview First

Before investing in hardware:
1. Open `web-preview/index.html` in a browser
2. Test all 3 seasonal scenes
3. Try AI scene generation
4. Verify audio synchronization
5. Gather feedback from potential users

**Only proceed to hardware if:**
- Visual effects are compelling
- Performance is smooth (60 FPS)
- User feedback is positive
- Business case is validated

## Resources

### LED Strip Suppliers
- AliExpress: Bulk LED strips at $8-15/meter
- Amazon: Faster shipping, $15-25/meter
- Adafruit: Premium quality, $25-30/meter

### Tutorials
- [ESP32 + WS2812B Guide](https://randomnerdtutorials.com/esp32-ws2812b-addressable-rgb-led-strip-arduino/)
- [FastLED Library Documentation](https://github.com/FastLED/FastLED)
- [WebSocket ESP32 Tutorial](https://randomnerdtutorials.com/esp32-websocket-server-arduino/)

### Tools Needed
- Soldering iron
- Wire strippers
- Multimeter
- Heat shrink tubing
- Cable management supplies

## Questions?

Before building hardware, validate the concept with the web preview first!

See `../README.md` for overall MVP strategy.
