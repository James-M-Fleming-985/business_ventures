/**
 * AI Interface - Simulated AI scene generation
 */

class AIInterface {
    constructor() {
        this.isGenerating = false;
        this.generatedScenes = [];
    }
    
    async generateScene(prompt) {
        this.isGenerating = true;
        
        // Simulate API delay
        await this.delay(1500);
        
        // Parse prompt for keywords and generate scene config
        const sceneConfig = this.parsePrompt(prompt);
        
        this.isGenerating = false;
        return sceneConfig;
    }
    
    parsePrompt(prompt) {
        const lowerPrompt = prompt.toLowerCase();
        
        // Detect scene theme
        let theme = 'custom';
        if (lowerPrompt.includes('halloween') || lowerPrompt.includes('spooky') || 
            lowerPrompt.includes('scary') || lowerPrompt.includes('ghost')) {
            theme = 'halloween';
        } else if (lowerPrompt.includes('christmas') || lowerPrompt.includes('winter') || 
                   lowerPrompt.includes('snow') || lowerPrompt.includes('holiday')) {
            theme = 'christmas';
        } else if (lowerPrompt.includes('easter') || lowerPrompt.includes('spring') || 
                   lowerPrompt.includes('flower') || lowerPrompt.includes('butterfly')) {
            theme = 'easter';
        }
        
        // Extract colors
        const colors = this.extractColors(lowerPrompt);
        
        // Extract elements
        const elements = this.extractElements(lowerPrompt);
        
        // Generate scene configuration
        return {
            name: this.generateSceneName(prompt),
            description: prompt,
            theme: theme,
            colors: colors,
            elements: elements,
            layers: this.generateLayers(theme, colors, elements)
        };
    }
    
    extractColors(prompt) {
        const colorMap = {
            'red': { r: 255, g: 0, b: 0 },
            'orange': { r: 255, g: 165, b: 0 },
            'yellow': { r: 255, g: 255, b: 0 },
            'green': { r: 0, g: 255, b: 0 },
            'blue': { r: 0, g: 0, b: 255 },
            'purple': { r: 128, g: 0, b: 128 },
            'pink': { r: 255, g: 192, b: 203 },
            'white': { r: 255, g: 255, b: 255 },
            'black': { r: 0, g: 0, b: 0 }
        };
        
        const foundColors = [];
        for (let [colorName, rgb] of Object.entries(colorMap)) {
            if (prompt.includes(colorName)) {
                foundColors.push({ name: colorName, ...rgb });
            }
        }
        
        return foundColors.length > 0 ? foundColors : [{ name: 'default', r: 100, g: 100, b: 255 }];
    }
    
    extractElements(prompt) {
        const elementKeywords = {
            'stars': ['star', 'stars', 'starry'],
            'clouds': ['cloud', 'clouds', 'cloudy'],
            'rain': ['rain', 'rainy', 'drops'],
            'lightning': ['lightning', 'thunder', 'flash'],
            'fire': ['fire', 'flame', 'flames'],
            'water': ['water', 'ocean', 'waves'],
            'sparkles': ['sparkle', 'sparkles', 'glitter'],
            'particles': ['particle', 'particles', 'dust'],
            'gradient': ['gradient', 'fade', 'transition']
        };
        
        const foundElements = [];
        for (let [element, keywords] of Object.entries(elementKeywords)) {
            if (keywords.some(keyword => prompt.includes(keyword))) {
                foundElements.push(element);
            }
        }
        
        return foundElements;
    }
    
    generateSceneName(prompt) {
        // Generate a name from first few words
        const words = prompt.split(' ').slice(0, 3);
        return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
    
    generateLayers(theme, colors, elements) {
        // Generate procedural layer descriptions
        return {
            background: this.generateBackgroundLayer(theme, colors, elements),
            midground: this.generateMidgroundLayer(theme, colors, elements),
            foreground: this.generateForegroundLayer(theme, colors, elements)
        };
    }
    
    generateBackgroundLayer(theme, colors, elements) {
        const effects = [];
        
        if (elements.includes('gradient')) {
            effects.push({
                type: 'gradient',
                colors: colors.slice(0, 2),
                direction: 'vertical'
            });
        }
        
        if (elements.includes('stars')) {
            effects.push({
                type: 'stars',
                density: 0.02,
                twinkle: true
            });
        }
        
        return {
            effects: effects.length > 0 ? effects : [{
                type: 'solid',
                color: colors[0] || { r: 20, g: 20, b: 40 }
            }]
        };
    }
    
    generateMidgroundLayer(theme, colors, elements) {
        const effects = [];
        
        if (elements.includes('sparkles')) {
            effects.push({
                type: 'sparkles',
                density: 0.05,
                color: colors[0]
            });
        }
        
        if (elements.includes('particles')) {
            effects.push({
                type: 'particles',
                count: 50,
                speed: 0.5
            });
        }
        
        return { effects };
    }
    
    generateForegroundLayer(theme, colors, elements) {
        const effects = [];
        
        if (elements.includes('lightning')) {
            effects.push({
                type: 'lightning',
                frequency: 0.001
            });
        }
        
        if (elements.includes('fire')) {
            effects.push({
                type: 'fire',
                intensity: 0.7
            });
        }
        
        return { effects };
    }
    
    createSceneFromConfig(config) {
        // Create a procedural scene object from config
        const scene = {
            name: config.name,
            description: config.description,
            
            init(renderer) {
                console.log(`AI-generated scene initialized: ${config.name}`);
            },
            
            updateBackground(renderer, time, deltaTime, opacity) {
                renderer.clearLayer('background');
                
                // Apply background effects from config
                for (let effect of config.layers.background.effects) {
                    if (effect.type === 'gradient') {
                        SceneUtils.gradient(
                            renderer,
                            'background',
                            effect.colors[0] || { r: 0, g: 0, b: 50 },
                            effect.colors[1] || { r: 0, g: 50, b: 100 },
                            effect.direction
                        );
                    } else if (effect.type === 'solid') {
                        renderer.fillLayer('background', effect.color);
                    } else if (effect.type === 'stars') {
                        SceneUtils.sparkle(renderer, 'background', effect.density);
                    }
                }
            },
            
            updateMidground(renderer, time, deltaTime, opacity) {
                renderer.clearLayer('midground');
                
                // Apply midground effects
                for (let effect of config.layers.midground.effects) {
                    if (effect.type === 'sparkles') {
                        SceneUtils.sparkle(renderer, 'midground', effect.density, effect.color);
                    }
                }
            },
            
            updateForeground(renderer, time, deltaTime, opacity) {
                // Apply foreground effects
                for (let effect of config.layers.foreground.effects) {
                    if (effect.type === 'lightning' && Math.random() < effect.frequency) {
                        renderer.fillLayer('foreground', {
                            r: 200,
                            g: 200,
                            b: 255,
                            a: opacity * 0.3
                        });
                        setTimeout(() => renderer.clearLayer('foreground'), 100);
                    }
                }
            }
        };
        
        return scene;
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    getSamplePrompts() {
        return [
            "Purple and orange nebula with twinkling stars",
            "Ocean waves with blue and green gradient",
            "Fiery sunset with red and yellow flames",
            "Peaceful forest with green sparkles and fireflies",
            "Thunderstorm with lightning flashes and rain",
            "Rainbow gradient with sparkles",
            "Deep space with purple and blue stars"
        ];
    }
}

window.AIInterface = AIInterface;
