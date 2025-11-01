/**
 * LED Renderer - Canvas-based LED Curtain Visualization
 * 
 * Simulates a physical LED curtain display with:
 * - Configurable LED density (60-144 LEDs/meter)
 * - Multi-layer rendering (background, midground, foreground)
 * - Realistic LED glow effects
 * - Performance-optimized rendering
 */

class LEDRenderer {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Configuration
        this.config = {
            ledDensity: options.ledDensity || 100, // LEDs per meter
            curtainWidth: options.curtainWidth || 3, // meters
            curtainHeight: options.curtainHeight || 2, // meters
            brightness: options.brightness || 0.8,
            ledSpacing: options.ledSpacing || 1.2, // spacing multiplier
            glowIntensity: options.glowIntensity || 0.6,
            ...options
        };
        
        // Calculate LED grid
        this.calculateLEDGrid();
        
        // Layer buffers
        this.layers = {
            background: [],
            midground: [],
            foreground: []
        };
        
        // Animation state
        this.animationFrame = null;
        this.lastFrameTime = 0;
        this.fps = 0;
        
        // Initialize
        this.resizeCanvas();
        this.initializeLEDs();
        
        // Handle window resize
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    calculateLEDGrid() {
        const { ledDensity, curtainWidth, curtainHeight, ledSpacing } = this.config;
        
        // Calculate number of LEDs
        this.cols = Math.floor(curtainWidth * ledDensity / ledSpacing);
        this.rows = Math.floor(curtainHeight * ledDensity / ledSpacing);
        this.totalLEDs = this.cols * this.rows;
        
        console.log(`LED Grid: ${this.cols} × ${this.rows} = ${this.totalLEDs} LEDs`);
    }
    
    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        
        // Calculate LED size based on canvas dimensions
        this.ledWidth = this.canvas.width / this.cols;
        this.ledHeight = this.canvas.height / this.rows;
        this.ledSize = Math.min(this.ledWidth, this.ledHeight) * 0.7; // 70% of cell size
    }
    
    initializeLEDs() {
        // Initialize each layer with black LEDs
        const blackLED = { r: 0, g: 0, b: 0, a: 1 };
        
        for (let layer of ['background', 'midground', 'foreground']) {
            this.layers[layer] = Array(this.totalLEDs).fill(null).map(() => ({...blackLED}));
        }
    }
    
    setLayerOpacity(layer, opacity) {
        if (!this.layers[layer]) return;
        
        for (let led of this.layers[layer]) {
            led.a = opacity;
        }
    }
    
    setLED(layer, x, y, color) {
        if (!this.layers[layer]) return;
        if (x < 0 || x >= this.cols || y < 0 || y >= this.rows) return;
        
        const index = y * this.cols + x;
        if (index >= 0 && index < this.totalLEDs) {
            this.layers[layer][index] = { ...color, a: color.a !== undefined ? color.a : 1 };
        }
    }
    
    getLED(layer, x, y) {
        if (!this.layers[layer]) return null;
        if (x < 0 || x >= this.cols || y < 0 || y >= this.rows) return null;
        
        const index = y * this.cols + x;
        return this.layers[layer][index] || null;
    }
    
    fillLayer(layer, color) {
        if (!this.layers[layer]) return;
        
        for (let i = 0; i < this.totalLEDs; i++) {
            this.layers[layer][i] = { ...color, a: color.a !== undefined ? color.a : 1 };
        }
    }
    
    clearLayer(layer) {
        this.fillLayer(layer, { r: 0, g: 0, b: 0, a: 1 });
    }
    
    clearAllLayers() {
        this.clearLayer('background');
        this.clearLayer('midground');
        this.clearLayer('foreground');
    }
    
    blendColors(bottom, top) {
        // Alpha blend two colors
        const alpha = top.a;
        return {
            r: Math.round(top.r * alpha + bottom.r * (1 - alpha)),
            g: Math.round(top.g * alpha + bottom.g * (1 - alpha)),
            b: Math.round(top.b * alpha + bottom.b * (1 - alpha)),
            a: 1
        };
    }
    
    render() {
        // Clear canvas
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render each LED
        for (let y = 0; y < this.rows; y++) {
            for (let x = 0; x < this.cols; x++) {
                const index = y * this.cols + x;
                
                // Blend layers
                let color = this.layers.background[index];
                color = this.blendColors(color, this.layers.midground[index]);
                color = this.blendColors(color, this.layers.foreground[index]);
                
                // Apply brightness
                const r = Math.round(color.r * this.config.brightness);
                const g = Math.round(color.g * this.config.brightness);
                const b = Math.round(color.b * this.config.brightness);
                
                // Calculate LED position
                const ledX = x * this.ledWidth + this.ledWidth / 2;
                const ledY = y * this.ledHeight + this.ledHeight / 2;
                
                // Skip if LED is off
                if (r === 0 && g === 0 && b === 0) continue;
                
                // Draw LED glow
                if (this.config.glowIntensity > 0) {
                    const gradient = this.ctx.createRadialGradient(
                        ledX, ledY, 0,
                        ledX, ledY, this.ledSize * 1.5
                    );
                    gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${this.config.glowIntensity})`);
                    gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
                    
                    this.ctx.fillStyle = gradient;
                    this.ctx.fillRect(
                        ledX - this.ledSize * 1.5,
                        ledY - this.ledSize * 1.5,
                        this.ledSize * 3,
                        this.ledSize * 3
                    );
                }
                
                // Draw LED core
                this.ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
                this.ctx.beginPath();
                this.ctx.arc(ledX, ledY, this.ledSize / 2, 0, Math.PI * 2);
                this.ctx.fill();
            }
        }
    }
    
    startAnimation(callback) {
        let frameCount = 0;
        let lastFPSUpdate = performance.now();
        
        const animate = (timestamp) => {
            // Calculate FPS
            frameCount++;
            if (timestamp - lastFPSUpdate >= 1000) {
                this.fps = frameCount;
                frameCount = 0;
                lastFPSUpdate = timestamp;
            }
            
            // Call animation callback
            if (callback) {
                const deltaTime = timestamp - this.lastFrameTime;
                callback(timestamp, deltaTime);
            }
            
            this.lastFrameTime = timestamp;
            
            // Render
            this.render();
            
            // Continue animation
            this.animationFrame = requestAnimationFrame(animate);
        };
        
        this.animationFrame = requestAnimationFrame(animate);
    }
    
    stopAnimation() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }
    
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        
        // Recalculate grid if density or size changed
        if (newConfig.ledDensity || newConfig.curtainWidth || newConfig.curtainHeight) {
            this.calculateLEDGrid();
            this.resizeCanvas();
            this.initializeLEDs();
        }
    }
    
    getStats() {
        return {
            totalLEDs: this.totalLEDs,
            cols: this.cols,
            rows: this.rows,
            fps: this.fps,
            brightness: this.config.brightness
        };
    }
}

// Export for use in other scripts
window.LEDRenderer = LEDRenderer;
