/**
 * Halloween Scene - Spooky graveyard with purple fog and flying bats
 */

const HalloweenScene = {
    name: 'Halloween',
    description: 'Spooky graveyard with purple fog, flying bats, and flickering jack-o-lanterns',
    
    // Scene parameters
    params: {
        fogSpeed: 0.0005,
        batSpeed: 0.001,
        pumpkinFlickerSpeed: 0.003,
        numBats: 5,
        numPumpkins: 8
    },
    
    // Scene state
    bats: [],
    pumpkins: [],
    
    init(renderer) {
        // Initialize bats
        this.bats = [];
        for (let i = 0; i < this.params.numBats; i++) {
            this.bats.push({
                x: Math.random() * renderer.cols,
                y: Math.random() * renderer.rows,
                speed: 0.5 + Math.random() * 1.5,
                amplitude: 2 + Math.random() * 3,
                phase: Math.random() * Math.PI * 2
            });
        }
        
        // Initialize pumpkins
        this.pumpkins = [];
        for (let i = 0; i < this.params.numPumpkins; i++) {
            this.pumpkins.push({
                x: Math.floor(Math.random() * renderer.cols),
                y: Math.floor(renderer.rows * 0.6 + Math.random() * renderer.rows * 0.4),
                flickerPhase: Math.random() * Math.PI * 2,
                flickerSpeed: 0.002 + Math.random() * 0.001
            });
        }
    },
    
    updateBackground(renderer, time, deltaTime, opacity) {
        // Dark purple/blue gradient fog
        const { cols, rows } = renderer;
        
        renderer.clearLayer('background');
        
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                // Create animated fog effect using noise
                const fogNoise = SceneUtils.perlinNoise(
                    x * 0.1,
                    y * 0.1 + time * this.params.fogSpeed,
                    12345
                );
                
                // Purple to dark blue gradient
                const gradientT = y / rows;
                const baseR = Math.round(SceneUtils.lerp(20, 5, gradientT));
                const baseG = Math.round(SceneUtils.lerp(0, 0, gradientT));
                const baseB = Math.round(SceneUtils.lerp(40, 20, gradientT));
                
                // Add fog variation
                const fogIntensity = fogNoise * 30;
                
                renderer.setLED('background', x, y, {
                    r: Math.min(255, baseR + fogIntensity),
                    g: Math.min(255, baseG),
                    b: Math.min(255, baseB + fogIntensity),
                    a: opacity
                });
            }
        }
    },
    
    updateMidground(renderer, time, deltaTime, opacity) {
        // Flying bats
        const { cols, rows } = renderer;
        
        renderer.clearLayer('midground');
        
        // Draw bats
        for (let bat of this.bats) {
            // Update bat position
            bat.x += bat.speed;
            if (bat.x > cols + 5) {
                bat.x = -5;
                bat.y = Math.random() * rows;
            }
            
            // Vertical wave motion
            const waveY = bat.y + Math.sin(time * 0.002 + bat.phase) * bat.amplitude;
            
            // Draw bat (simple 3x3 shape)
            const batX = Math.floor(bat.x);
            const batY = Math.floor(waveY);
            
            const batColor = { r: 0, g: 0, b: 0, a: opacity };
            
            // Bat body
            renderer.setLED('midground', batX, batY, batColor);
            // Wings
            renderer.setLED('midground', batX - 1, batY, batColor);
            renderer.setLED('midground', batX + 1, batY, batColor);
            renderer.setLED('midground', batX - 1, batY - 1, batColor);
            renderer.setLED('midground', batX + 1, batY - 1, batColor);
        }
    },
    
    updateForeground(renderer, time, deltaTime, opacity) {
        // Flickering jack-o-lanterns at bottom
        renderer.clearLayer('foreground');
        
        for (let pumpkin of this.pumpkins) {
            // Flickering orange glow
            const flicker = SceneUtils.pulse(
                time * pumpkin.flickerSpeed + pumpkin.flickerPhase,
                1,
                0.5,
                1.0
            );
            
            const orange = {
                r: Math.round(255 * flicker),
                g: Math.round(140 * flicker),
                b: 0,
                a: opacity
            };
            
            // Draw pumpkin glow (3x3 area)
            for (let dy = -1; dy <= 1; dy++) {
                for (let dx = -1; dx <= 1; dx++) {
                    const intensity = 1 - (Math.abs(dx) + Math.abs(dy)) * 0.2;
                    renderer.setLED('foreground', pumpkin.x + dx, pumpkin.y + dy, {
                        r: Math.round(orange.r * intensity),
                        g: Math.round(orange.g * intensity),
                        b: orange.b,
                        a: opacity
                    });
                }
            }
        }
        
        // Add occasional lightning flash
        if (Math.random() < 0.001) {
            const flashIntensity = 200;
            renderer.fillLayer('foreground', {
                r: flashIntensity,
                g: flashIntensity,
                b: flashIntensity,
                a: opacity * 0.3
            });
        }
    }
};

// Make available globally
window.HalloweenScene = HalloweenScene;
