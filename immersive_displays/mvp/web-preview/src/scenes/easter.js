/**
 * Easter Scene - Springtime meadow with blooming flowers and butterflies
 */

const EasterScene = {
    name: 'Easter',
    description: 'Springtime meadow with blooming flowers, flying butterflies, and rainbow',
    
    params: {
        butterflySpeed: 0.8,
        flowerGrowSpeed: 0.001,
        rainbowSpeed: 0.0002,
        numButterflies: 6,
        numFlowers: 15
    },
    
    butterflies: [],
    flowers: [],
    
    init(renderer) {
        // Initialize butterflies
        this.butterflies = [];
        for (let i = 0; i < this.params.numButterflies; i++) {
            this.butterflies.push({
                x: Math.random() * renderer.cols,
                y: Math.random() * renderer.rows * 0.7,
                speed: 0.3 + Math.random() * 0.5,
                amplitude: 3 + Math.random() * 4,
                phase: Math.random() * Math.PI * 2,
                color: this.getRandomPastelColor()
            });
        }
        
        // Initialize flowers
        this.flowers = [];
        for (let i = 0; i < this.params.numFlowers; i++) {
            this.flowers.push({
                x: Math.floor(Math.random() * renderer.cols),
                y: Math.floor(renderer.rows * 0.6 + Math.random() * renderer.rows * 0.4),
                color: this.getRandomPastelColor(),
                bloomPhase: Math.random() * Math.PI * 2,
                bloomSpeed: 0.0015 + Math.random() * 0.001
            });
        }
    },
    
    getRandomPastelColor() {
        const colors = [
            { r: 255, g: 182, b: 193 }, // Light Pink
            { r: 255, g: 218, b: 185 }, // Peach
            { r: 221, g: 160, b: 221 }, // Plum
            { r: 173, g: 216, b: 230 }, // Light Blue
            { r: 255, g: 255, b: 153 }, // Light Yellow
            { r: 152, g: 251, b: 152 }  // Pale Green
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    },
    
    updateBackground(renderer, time, deltaTime, opacity) {
        // Sky with rainbow arc
        const { cols, rows } = renderer;
        
        renderer.clearLayer('background');
        
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                // Light blue sky gradient
                const skyT = y / rows;
                let r = Math.round(SceneUtils.lerp(135, 200, skyT));
                let g = Math.round(SceneUtils.lerp(206, 230, skyT));
                let b = Math.round(SceneUtils.lerp(235, 255, skyT));
                
                // Rainbow arc (upper third)
                if (y < rows * 0.4) {
                    const centerX = cols / 2;
                    const centerY = rows * -0.2;
                    const dx = x - centerX;
                    const dy = y - centerY;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    const rainbowStart = rows * 0.5;
                    const rainbowWidth = rows * 0.15;
                    
                    if (distance > rainbowStart && distance < rainbowStart + rainbowWidth) {
                        // Calculate rainbow color
                        const t = (distance - rainbowStart) / rainbowWidth;
                        const hue = (t + time * this.params.rainbowSpeed) % 1;
                        const rainbowColor = SceneUtils.hsvToRgb(hue, 0.5, 0.8);
                        
                        // Blend with sky
                        const blendFactor = 0.4;
                        r = Math.round(r * (1 - blendFactor) + rainbowColor.r * blendFactor);
                        g = Math.round(g * (1 - blendFactor) + rainbowColor.g * blendFactor);
                        b = Math.round(b * (1 - blendFactor) + rainbowColor.b * blendFactor);
                    }
                }
                
                renderer.setLED('background', x, y, { r, g, b, a: opacity });
            }
        }
        
        // Add grass at bottom
        const grassStart = Math.floor(rows * 0.6);
        for (let y = grassStart; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const grassVariation = SceneUtils.perlinNoise(x * 0.2, y * 0.2, 54321) * 40;
                renderer.setLED('background', x, y, {
                    r: Math.round(50 + grassVariation),
                    g: Math.round(180 + grassVariation),
                    b: Math.round(50 + grassVariation),
                    a: opacity
                });
            }
        }
    },
    
    updateMidground(renderer, time, deltaTime, opacity) {
        // Flying butterflies
        const { cols, rows } = renderer;
        
        renderer.clearLayer('midground');
        
        for (let butterfly of this.butterflies) {
            // Update position
            butterfly.x += butterfly.speed;
            if (butterfly.x > cols + 3) {
                butterfly.x = -3;
                butterfly.y = Math.random() * rows * 0.7;
            }
            
            // Vertical flutter
            const flutterY = butterfly.y + 
                Math.sin(time * 0.003 + butterfly.phase) * butterfly.amplitude;
            
            const bx = Math.floor(butterfly.x);
            const by = Math.floor(flutterY);
            
            // Draw butterfly (simple shape)
            // Wing flap animation
            const wingFlap = Math.abs(Math.sin(time * 0.005 + butterfly.phase));
            const wingSpread = Math.floor(1 + wingFlap * 2);
            
            // Body
            renderer.setLED('midground', bx, by, {
                r: 50,
                g: 50,
                b: 50,
                a: opacity
            });
            
            // Wings
            for (let w = 1; w <= wingSpread; w++) {
                renderer.setLED('midground', bx - w, by - 1, {
                    ...butterfly.color,
                    a: opacity
                });
                renderer.setLED('midground', bx + w, by - 1, {
                    ...butterfly.color,
                    a: opacity
                });
                renderer.setLED('midground', bx - w, by + 1, {
                    ...butterfly.color,
                    a: opacity
                });
                renderer.setLED('midground', bx + w, by + 1, {
                    ...butterfly.color,
                    a: opacity
                });
            }
        }
    },
    
    updateForeground(renderer, time, deltaTime, opacity) {
        // Blooming flowers
        renderer.clearLayer('foreground');
        
        for (let flower of this.flowers) {
            // Bloom animation
            const bloom = SceneUtils.pulse(
                time * flower.bloomSpeed + flower.bloomPhase,
                1,
                0.6,
                1.0
            );
            
            // Draw flower center
            renderer.setLED('foreground', flower.x, flower.y, {
                r: Math.round(255 * bloom),
                g: Math.round(255 * bloom),
                b: 0,
                a: opacity
            });
            
            // Draw petals
            const petalPositions = [
                [-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [1, -1], [-1, 1], [1, 1]
            ];
            
            for (let [dx, dy] of petalPositions) {
                renderer.setLED('foreground', flower.x + dx, flower.y + dy, {
                    r: Math.round(flower.color.r * bloom),
                    g: Math.round(flower.color.g * bloom),
                    b: Math.round(flower.color.b * bloom),
                    a: opacity
                });
            }
            
            // Stem
            for (let dy = 1; dy < 3; dy++) {
                renderer.setLED('foreground', flower.x, flower.y + dy, {
                    r: 34,
                    g: 139,
                    b: 34,
                    a: opacity
                });
            }
        }
    }
};

window.EasterScene = EasterScene;
