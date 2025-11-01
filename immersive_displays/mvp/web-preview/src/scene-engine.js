/**
 * Scene Engine - Multi-layer Scene Management
 * 
 * Manages scene playback with:
 * - Multi-layer animation system
 * - Effect composition
 * - Scene transitions
 * - Performance optimization
 */

class SceneEngine {
    constructor(ledRenderer) {
        this.renderer = ledRenderer;
        this.currentScene = null;
        this.isPlaying = false;
        this.startTime = 0;
        this.elapsedTime = 0;
        this.layerVisibility = {
            background: true,
            midground: true,
            foreground: true
        };
        this.layerOpacity = {
            background: 1.0,
            midground: 1.0,
            foreground: 1.0
        };
    }
    
    loadScene(scene) {
        this.currentScene = scene;
        this.startTime = performance.now();
        this.elapsedTime = 0;
        
        // Initialize scene if it has init method
        if (scene.init) {
            scene.init(this.renderer);
        }
        
        console.log(`Scene loaded: ${scene.name}`);
    }
    
    play() {
        if (!this.currentScene) {
            console.warn('No scene loaded');
            return;
        }
        
        this.isPlaying = true;
        this.startTime = performance.now() - this.elapsedTime;
    }
    
    pause() {
        this.isPlaying = false;
    }
    
    stop() {
        this.isPlaying = false;
        this.elapsedTime = 0;
        this.renderer.clearAllLayers();
    }
    
    update(timestamp, deltaTime) {
        if (!this.isPlaying || !this.currentScene) return;
        
        this.elapsedTime = timestamp - this.startTime;
        
        // Update each layer
        for (let layer of ['background', 'midground', 'foreground']) {
            if (!this.layerVisibility[layer]) {
                this.renderer.clearLayer(layer);
                continue;
            }
            
            // Call scene's layer update method
            const updateMethod = `update${this.capitalize(layer)}`;
            if (this.currentScene[updateMethod]) {
                this.currentScene[updateMethod](
                    this.renderer,
                    this.elapsedTime,
                    deltaTime,
                    this.layerOpacity[layer]
                );
            }
        }
    }
    
    setLayerVisibility(layer, visible) {
        this.layerVisibility[layer] = visible;
        if (!visible) {
            this.renderer.clearLayer(layer);
        }
    }
    
    setLayerOpacity(layer, opacity) {
        this.layerOpacity[layer] = Math.max(0, Math.min(1, opacity));
    }
    
    getLayerVisibility(layer) {
        return this.layerVisibility[layer];
    }
    
    getLayerOpacity(layer) {
        return this.layerOpacity[layer];
    }
    
    getCurrentScene() {
        return this.currentScene;
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Utility functions for scene creation

class SceneUtils {
    // Color utilities
    static hsvToRgb(h, s, v) {
        let r, g, b;
        const i = Math.floor(h * 6);
        const f = h * 6 - i;
        const p = v * (1 - s);
        const q = v * (1 - f * s);
        const t = v * (1 - (1 - f) * s);
        
        switch (i % 6) {
            case 0: r = v; g = t; b = p; break;
            case 1: r = q; g = v; b = p; break;
            case 2: r = p; g = v; b = t; break;
            case 3: r = p; g = q; b = v; break;
            case 4: r = t; g = p; b = v; break;
            case 5: r = v; g = p; b = q; break;
        }
        
        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255)
        };
    }
    
    static rgbToHsv(r, g, b) {
        r /= 255;
        g /= 255;
        b /= 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const delta = max - min;
        
        let h = 0;
        if (delta !== 0) {
            if (max === r) {
                h = ((g - b) / delta) % 6;
            } else if (max === g) {
                h = (b - r) / delta + 2;
            } else {
                h = (r - g) / delta + 4;
            }
            h /= 6;
            if (h < 0) h += 1;
        }
        
        const s = max === 0 ? 0 : delta / max;
        const v = max;
        
        return { h, s, v };
    }
    
    // Animation utilities
    static lerp(start, end, t) {
        return start + (end - start) * t;
    }
    
    static easeInOut(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }
    
    static easeIn(t) {
        return t * t;
    }
    
    static easeOut(t) {
        return t * (2 - t);
    }
    
    static wave(time, frequency = 1, amplitude = 1, phase = 0) {
        return Math.sin(time * frequency + phase) * amplitude;
    }
    
    static pulse(time, frequency = 1, min = 0, max = 1) {
        const wave = (Math.sin(time * frequency) + 1) / 2;
        return this.lerp(min, max, wave);
    }
    
    // Pattern generators
    static perlinNoise(x, y, seed = 0) {
        // Simplified Perlin noise (for demo purposes)
        const noise = (x, y) => {
            const n = Math.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453;
            return n - Math.floor(n);
        };
        
        const x0 = Math.floor(x);
        const x1 = x0 + 1;
        const y0 = Math.floor(y);
        const y1 = y0 + 1;
        
        const fx = x - x0;
        const fy = y - y0;
        
        const n00 = noise(x0, y0);
        const n10 = noise(x1, y0);
        const n01 = noise(x0, y1);
        const n11 = noise(x1, y1);
        
        const nx0 = this.lerp(n00, n10, fx);
        const nx1 = this.lerp(n01, n11, fx);
        
        return this.lerp(nx0, nx1, fy);
    }
    
    static sparkle(renderer, layer, density = 0.05, color = null) {
        const { cols, rows } = renderer;
        const numSparkles = Math.floor(cols * rows * density);
        
        for (let i = 0; i < numSparkles; i++) {
            const x = Math.floor(Math.random() * cols);
            const y = Math.floor(Math.random() * rows);
            const brightness = Math.random();
            
            const sparkleColor = color || {
                r: 255,
                g: 255,
                b: 255
            };
            
            renderer.setLED(layer, x, y, {
                r: Math.round(sparkleColor.r * brightness),
                g: Math.round(sparkleColor.g * brightness),
                b: Math.round(sparkleColor.b * brightness)
            });
        }
    }
    
    static gradient(renderer, layer, startColor, endColor, direction = 'vertical') {
        const { cols, rows } = renderer;
        
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const t = direction === 'vertical' ? y / rows : x / cols;
                
                const color = {
                    r: Math.round(this.lerp(startColor.r, endColor.r, t)),
                    g: Math.round(this.lerp(startColor.g, endColor.g, t)),
                    b: Math.round(this.lerp(startColor.b, endColor.b, t))
                };
                
                renderer.setLED(layer, x, y, color);
            }
        }
    }
    
    static drawCircle(renderer, layer, centerX, centerY, radius, color, filled = true) {
        const { cols, rows } = renderer;
        
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const dx = x - centerX;
                const dy = y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (filled ? distance <= radius : Math.abs(distance - radius) < 1) {
                    renderer.setLED(layer, x, y, color);
                }
            }
        }
    }
    
    static drawLine(renderer, layer, x0, y0, x1, y1, color) {
        // Bresenham's line algorithm
        const dx = Math.abs(x1 - x0);
        const dy = Math.abs(y1 - y0);
        const sx = x0 < x1 ? 1 : -1;
        const sy = y0 < y1 ? 1 : -1;
        let err = dx - dy;
        
        while (true) {
            renderer.setLED(layer, x0, y0, color);
            
            if (x0 === x1 && y0 === y1) break;
            
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x0 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y0 += sy;
            }
        }
    }
}

// Export for use in other scripts
window.SceneEngine = SceneEngine;
window.SceneUtils = SceneUtils;
