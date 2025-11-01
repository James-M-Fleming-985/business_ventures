/**
 * Christmas Scene - Snowy landscape with falling snow and twinkling lights
 */

const ChristmasScene = {
    name: 'Christmas',
    description: 'Snowy winter landscape with falling snow, twinkling stars, and aurora borealis',
    
    params: {
        snowSpeed: 0.5,
        twinkleSpeed: 0.002,
        auroraSpeed: 0.0003,
        numSnowflakes: 100,
        numStars: 30
    },
    
    snowflakes: [],
    stars: [],
    
    init(renderer) {
        // Initialize snowflakes
        this.snowflakes = [];
        for (let i = 0; i < this.params.numSnowflakes; i++) {
            this.snowflakes.push({
                x: Math.random() * renderer.cols,
                y: Math.random() * renderer.rows,
                speed: 0.3 + Math.random() * 0.7,
                drift: (Math.random() - 0.5) * 0.2
            });
        }
        
        // Initialize twinkling stars
        this.stars = [];
        for (let i = 0; i < this.params.numStars; i++) {
            this.stars.push({
                x: Math.floor(Math.random() * renderer.cols),
                y: Math.floor(Math.random() * renderer.rows * 0.4),
                phase: Math.random() * Math.PI * 2,
                speed: 0.001 + Math.random() * 0.002
            });
        }
    },
    
    updateBackground(renderer, time, deltaTime, opacity) {
        // Aurora borealis effect - green and blue waves
        const { cols, rows } = renderer;
        
        renderer.clearLayer('background');
        
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                // Dark blue night sky gradient
                const skyT = y / rows;
                const baseR = Math.round(SceneUtils.lerp(5, 0, skyT));
                const baseG = Math.round(SceneUtils.lerp(10, 5, skyT));
                const baseB = Math.round(SceneUtils.lerp(30, 15, skyT));
                
                // Aurora waves (only in upper half)
                let auroraR = 0, auroraG = 0, auroraB = 0;
                if (y < rows * 0.5) {
                    const wave1 = SceneUtils.wave(
                        x * 0.1 + time * this.params.auroraSpeed,
                        1,
                        1,
                        y * 0.1
                    );
                    const wave2 = SceneUtils.wave(
                        x * 0.15 + time * this.params.auroraSpeed * 1.3,
                        1,
                        1,
                        y * 0.15 + Math.PI
                    );
                    
                    const auroraIntensity = Math.max(0, (wave1 + wave2) * 0.3);
                    auroraG = Math.round(100 * auroraIntensity);
                    auroraB = Math.round(50 * auroraIntensity);
                }
                
                renderer.setLED('background', x, y, {
                    r: baseR + auroraR,
                    g: baseG + auroraG,
                    b: baseB + auroraB,
                    a: opacity
                });
            }
        }
        
        // Add twinkling stars
        for (let star of this.stars) {
            const twinkle = SceneUtils.pulse(
                time * star.speed + star.phase,
                1,
                0.3,
                1.0
            );
            
            renderer.setLED('background', star.x, star.y, {
                r: Math.round(255 * twinkle),
                g: Math.round(255 * twinkle),
                b: Math.round(255 * twinkle),
                a: opacity
            });
        }
    },
    
    updateMidground(renderer, time, deltaTime, opacity) {
        // Falling snow
        const { cols, rows } = renderer;
        
        renderer.clearLayer('midground');
        
        for (let snowflake of this.snowflakes) {
            // Update position
            snowflake.y += snowflake.speed;
            snowflake.x += snowflake.drift;
            
            // Wrap around
            if (snowflake.y > rows) {
                snowflake.y = 0;
                snowflake.x = Math.random() * cols;
            }
            if (snowflake.x < 0) snowflake.x += cols;
            if (snowflake.x >= cols) snowflake.x -= cols;
            
            // Draw snowflake
            const x = Math.floor(snowflake.x);
            const y = Math.floor(snowflake.y);
            
            renderer.setLED('midground', x, y, {
                r: 255,
                g: 255,
                b: 255,
                a: opacity
            });
        }
    },
    
    updateForeground(renderer, time, deltaTime, opacity) {
        // Christmas lights string effect at bottom
        const { cols, rows } = renderer;
        
        renderer.clearLayer('foreground');
        
        // Alternating colored lights
        const colors = [
            { r: 255, g: 0, b: 0 },     // Red
            { r: 0, g: 255, b: 0 },     // Green
            { r: 255, g: 255, b: 0 },   // Yellow
            { r: 0, g: 100, b: 255 },   // Blue
            { r: 255, g: 255, b: 255 }  // White
        ];
        
        // Draw light string
        const lightY = Math.floor(rows * 0.85);
        const spacing = 3;
        
        for (let x = 0; x < cols; x += spacing) {
            const colorIndex = Math.floor(x / spacing) % colors.length;
            const baseColor = colors[colorIndex];
            
            // Twinkling effect
            const twinkle = SceneUtils.pulse(
                time * this.params.twinkleSpeed + x * 0.1,
                1,
                0.5,
                1.0
            );
            
            // Draw light with glow
            for (let dy = -1; dy <= 1; dy++) {
                const y = lightY + dy;
                const intensity = 1 - Math.abs(dy) * 0.3;
                
                renderer.setLED('foreground', x, y, {
                    r: Math.round(baseColor.r * twinkle * intensity),
                    g: Math.round(baseColor.g * twinkle * intensity),
                    b: Math.round(baseColor.b * twinkle * intensity),
                    a: opacity
                });
            }
        }
    }
};

window.ChristmasScene = ChristmasScene;
