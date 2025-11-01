/**
 * Main Application - Coordinates all components
 */

// Global state
let renderer = null;
let sceneEngine = null;
let audioSync = null;
let aiInterface = null;

// Scene registry
const scenes = {
    halloween: HalloweenScene,
    christmas: ChristmasScene,
    easter: EasterScene
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎃 Immersive Displays MVP Initializing...');
    
    initializeComponents();
    setupEventListeners();
    updateStats();
    
    console.log('✅ Application ready!');
});

function initializeComponents() {
    // Initialize LED renderer
    renderer = new LEDRenderer('led-canvas', {
        ledDensity: 100,
        curtainWidth: 3,
        curtainHeight: 2,
        brightness: 0.8,
        glowIntensity: 0.6
    });
    
    // Initialize scene engine
    sceneEngine = new SceneEngine(renderer);
    
    // Initialize audio sync
    audioSync = new AudioSync('waveform-canvas');
    
    // Initialize AI interface
    aiInterface = new AIInterface();
    
    // Start animation loop
    renderer.startAnimation((timestamp, deltaTime) => {
        // Update scene engine
        sceneEngine.update(timestamp, deltaTime);
        
        // Update audio visualization
        if (audioSync) {
            audioSync.update();
        }
        
        // Update stats
        if (Math.floor(timestamp) % 500 === 0) {
            updateStats();
        }
    });
}

function setupEventListeners() {
    // Scene selection
    document.querySelectorAll('.scene-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const sceneName = btn.dataset.scene;
            loadScene(sceneName);
            
            // Update active button
            document.querySelectorAll('.scene-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
    
    // AI scene generation
    const generateBtn = document.getElementById('generate-btn');
    const aiPrompt = document.getElementById('ai-prompt');
    
    generateBtn.addEventListener('click', async () => {
        const prompt = aiPrompt.value.trim();
        if (!prompt) {
            alert('Please enter a scene description');
            return;
        }
        
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        try {
            const sceneConfig = await aiInterface.generateScene(prompt);
            const customScene = aiInterface.createSceneFromConfig(sceneConfig);
            
            // Add to scenes registry
            scenes['custom'] = customScene;
            
            // Load the generated scene
            sceneEngine.loadScene(customScene);
            sceneEngine.play();
            
            // Update UI
            updateSceneInfo(customScene.name, customScene.description);
            
            // Deactivate preset buttons
            document.querySelectorAll('.scene-btn').forEach(b => b.classList.remove('active'));
            
            alert(`✨ Scene "${sceneConfig.name}" generated successfully!`);
        } catch (error) {
            console.error('Failed to generate scene:', error);
            alert('Failed to generate scene. Please try again.');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Scene';
        }
    });
    
    // Audio controls
    document.getElementById('play-audio-btn').addEventListener('click', () => {
        if (audioSync) {
            audioSync.play();
        }
    });
    
    document.getElementById('stop-audio-btn').addEventListener('click', () => {
        if (audioSync) {
            audioSync.stop();
        }
    });
    
    document.getElementById('beat-sync-toggle').addEventListener('change', (e) => {
        if (audioSync) {
            audioSync.setBeatSyncEnabled(e.target.checked);
        }
    });
    
    // Volume control
    const volumeSlider = document.getElementById('volume-slider');
    const volumeValue = document.getElementById('volume-value');
    
    volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value / 100;
        volumeValue.textContent = `${e.target.value}%`;
        if (audioSync) {
            audioSync.setVolume(volume);
        }
    });
    
    // Display settings
    document.getElementById('led-density').addEventListener('change', (e) => {
        renderer.updateConfig({ ledDensity: parseInt(e.target.value) });
        updateStats();
    });
    
    document.getElementById('curtain-size').addEventListener('change', (e) => {
        const [width, height] = e.target.value.split('x').map(Number);
        renderer.updateConfig({ curtainWidth: width, curtainHeight: height });
        updateStats();
    });
    
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessValue = document.getElementById('brightness-value');
    
    brightnessSlider.addEventListener('input', (e) => {
        const brightness = e.target.value / 100;
        brightnessValue.textContent = `${e.target.value}%`;
        renderer.updateConfig({ brightness });
    });
    
    // Layer controls
    document.querySelectorAll('.layer-item').forEach(item => {
        const layer = item.dataset.layer;
        const toggleBtn = item.querySelector('.toggle-btn');
        const opacitySlider = item.querySelector('.opacity-slider');
        const opacityValue = item.querySelector('.opacity-value');
        
        // Toggle visibility
        toggleBtn.addEventListener('click', () => {
            const visible = sceneEngine.getLayerVisibility(layer);
            sceneEngine.setLayerVisibility(layer, !visible);
            toggleBtn.textContent = visible ? '👁️‍🗨️' : '👁️';
            toggleBtn.style.opacity = visible ? '0.5' : '1';
        });
        
        // Opacity control
        opacitySlider.addEventListener('input', (e) => {
            const opacity = e.target.value / 100;
            opacityValue.textContent = `${e.target.value}%`;
            sceneEngine.setLayerOpacity(layer, opacity);
        });
    });
    
    // Hardware info button
    document.getElementById('hardware-info-btn').addEventListener('click', () => {
        showHardwareInfo();
    });
    
    // Export scene config
    document.getElementById('export-scene-btn').addEventListener('click', () => {
        exportSceneConfig();
    });
}

function loadScene(sceneName) {
    const scene = scenes[sceneName];
    if (!scene) {
        console.error(`Scene not found: ${sceneName}`);
        return;
    }
    
    // Stop current scene
    sceneEngine.stop();
    
    // Load new scene
    sceneEngine.loadScene(scene);
    sceneEngine.play();
    
    // Update scene info
    updateSceneInfo(scene.name, scene.description);
    
    console.log(`Loaded scene: ${scene.name}`);
}

function updateSceneInfo(name, description) {
    document.getElementById('scene-title').textContent = name;
    document.getElementById('scene-description').textContent = description;
}

function updateStats() {
    const stats = renderer.getStats();
    
    document.getElementById('total-leds').textContent = stats.totalLEDs;
    document.getElementById('fps').textContent = stats.fps;
    document.getElementById('layers').textContent = '3';
}

function showHardwareInfo() {
    const stats = renderer.getStats();
    
    const info = `
🔌 Hardware Requirements

LED Curtain Specifications:
- Total LEDs: ${stats.totalLEDs}
- Grid: ${stats.cols} × ${stats.rows}
- LED Type: WS2812B or SK6812
- Density: ${renderer.config.ledDensity} LEDs/meter
- Size: ${renderer.config.curtainWidth}m × ${renderer.config.curtainHeight}m

Controller:
- ESP32 DevKit (WiFi + Bluetooth)
- 5V Power Supply (60W per 100 LEDs)
- Level shifter for 5V LED signal

Estimated Cost:
- LED Strips: $${Math.round(stats.totalLEDs * 0.15)} - $${Math.round(stats.totalLEDs * 0.25)}
- Controller: $10 - $15
- Power Supply: $30 - $50
- Housing/Mounting: $20 - $40

Total: $${Math.round(stats.totalLEDs * 0.15 + 70)} - $${Math.round(stats.totalLEDs * 0.25 + 115)}

Next Steps:
1. Source WS2812B LED strips from AliExpress/Amazon
2. Purchase ESP32 DevKit
3. Follow hardware integration guide in mvp/hardware-integration/
4. Flash firmware and connect to web interface

Ready to build your display?
    `.trim();
    
    alert(info);
}

function exportSceneConfig() {
    const currentScene = sceneEngine.getCurrentScene();
    if (!currentScene) {
        alert('No scene loaded');
        return;
    }
    
    const config = {
        name: currentScene.name,
        description: currentScene.description,
        settings: {
            ledDensity: renderer.config.ledDensity,
            curtainWidth: renderer.config.curtainWidth,
            curtainHeight: renderer.config.curtainHeight,
            brightness: renderer.config.brightness
        },
        layers: {
            background: {
                visible: sceneEngine.getLayerVisibility('background'),
                opacity: sceneEngine.getLayerOpacity('background')
            },
            midground: {
                visible: sceneEngine.getLayerVisibility('midground'),
                opacity: sceneEngine.getLayerOpacity('midground')
            },
            foreground: {
                visible: sceneEngine.getLayerVisibility('foreground'),
                opacity: sceneEngine.getLayerOpacity('foreground')
            }
        }
    };
    
    // Download as JSON
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentScene.name.toLowerCase().replace(/\s+/g, '-')}-config.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    console.log('Scene config exported:', config);
}

// Beat reactive effects
window.addEventListener('beat', (event) => {
    const { bass, mid, treble } = event.detail;
    
    // Flash effect on strong beats
    if (bass > 0.7) {
        const canvas = document.getElementById('led-canvas');
        canvas.style.filter = `brightness(${1 + bass * 0.3})`;
        setTimeout(() => {
            canvas.style.filter = 'brightness(1)';
        }, 100);
    }
});

// Handle errors
window.addEventListener('error', (event) => {
    console.error('Application error:', event.error);
});

// Cleanup on unload
window.addEventListener('beforeunload', () => {
    if (renderer) {
        renderer.stopAnimation();
    }
    if (audioSync) {
        audioSync.stop();
    }
});
