/**
 * Audio Synchronization - Beat detection and audio-reactive lighting
 */

class AudioSync {
    constructor(waveformCanvasId) {
        this.audioContext = null;
        this.analyser = null;
        this.audioElement = null;
        this.dataArray = null;
        this.bufferLength = 0;
        this.isPlaying = false;
        this.beatSyncEnabled = true;
        
        // Waveform visualization
        this.waveformCanvas = document.getElementById(waveformCanvasId);
        this.waveformCtx = this.waveformCanvas ? this.waveformCanvas.getContext('2d') : null;
        
        // Beat detection
        this.beatThreshold = 1.3;
        this.beatDecay = 0.98;
        this.beatCutoff = 0;
        this.beatMin = Infinity;
        this.beatMax = -Infinity;
        
        // Audio reactive state
        this.bassLevel = 0;
        this.midLevel = 0;
        this.trebleLevel = 0;
        this.volume = 0.7;
    }
    
    async init(audioSource) {
        try {
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.analyser.smoothingTimeConstant = 0.8;
            
            this.bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);
            
            // Create audio element if source is URL
            if (typeof audioSource === 'string') {
                this.audioElement = new Audio(audioSource);
                this.audioElement.crossOrigin = 'anonymous';
                this.audioElement.loop = true;
                this.audioElement.volume = this.volume;
                
                const source = this.audioContext.createMediaElementSource(this.audioElement);
                source.connect(this.analyser);
                this.analyser.connect(this.audioContext.destination);
            }
            
            console.log('Audio system initialized');
            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            return false;
        }
    }
    
    play() {
        if (!this.audioElement) {
            console.warn('No audio source loaded');
            return;
        }
        
        this.audioElement.play();
        this.isPlaying = true;
        
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
    }
    
    pause() {
        if (!this.audioElement) return;
        
        this.audioElement.pause();
        this.isPlaying = false;
    }
    
    stop() {
        if (!this.audioElement) return;
        
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
        this.isPlaying = false;
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audioElement) {
            this.audioElement.volume = this.volume;
        }
    }
    
    setBeatSyncEnabled(enabled) {
        this.beatSyncEnabled = enabled;
    }
    
    update() {
        if (!this.analyser || !this.dataArray) return;
        
        // Get frequency data
        this.analyser.getByteFrequencyData(this.dataArray);
        
        // Calculate frequency bands
        const bass = this.getAverageFrequency(0, 100);
        const mid = this.getAverageFrequency(100, 500);
        const treble = this.getAverageFrequency(500, 2000);
        
        this.bassLevel = bass / 255;
        this.midLevel = mid / 255;
        this.trebleLevel = treble / 255;
        
        // Beat detection
        if (this.beatSyncEnabled) {
            this.detectBeat();
        }
        
        // Update waveform visualization
        this.drawWaveform();
    }
    
    getAverageFrequency(startHz, endHz) {
        const nyquist = this.audioContext.sampleRate / 2;
        const startIndex = Math.floor((startHz / nyquist) * this.bufferLength);
        const endIndex = Math.floor((endHz / nyquist) * this.bufferLength);
        
        let sum = 0;
        let count = 0;
        
        for (let i = startIndex; i < endIndex && i < this.bufferLength; i++) {
            sum += this.dataArray[i];
            count++;
        }
        
        return count > 0 ? sum / count : 0;
    }
    
    detectBeat() {
        const average = this.bassLevel;
        
        // Update min/max for normalization
        if (average < this.beatMin) this.beatMin = average;
        if (average > this.beatMax) this.beatMax = average;
        
        // Detect beat
        if (average > this.beatCutoff && average > this.beatThreshold * 0.5) {
            this.onBeat();
        }
        
        // Decay cutoff
        this.beatCutoff *= this.beatDecay;
        this.beatCutoff = Math.max(this.beatCutoff, average);
    }
    
    onBeat() {
        // Trigger beat event
        const event = new CustomEvent('beat', {
            detail: {
                bass: this.bassLevel,
                mid: this.midLevel,
                treble: this.trebleLevel
            }
        });
        window.dispatchEvent(event);
    }
    
    drawWaveform() {
        if (!this.waveformCtx || !this.analyser) return;
        
        // Get time domain data for waveform
        const timeData = new Uint8Array(this.analyser.fftSize);
        this.analyser.getByteTimeDomainData(timeData);
        
        const { width, height } = this.waveformCanvas;
        
        // Clear canvas
        this.waveformCtx.fillStyle = '#151b2b';
        this.waveformCtx.fillRect(0, 0, width, height);
        
        // Draw waveform
        this.waveformCtx.lineWidth = 2;
        this.waveformCtx.strokeStyle = '#6366f1';
        this.waveformCtx.beginPath();
        
        const sliceWidth = width / timeData.length;
        let x = 0;
        
        for (let i = 0; i < timeData.length; i++) {
            const v = timeData[i] / 128.0;
            const y = v * height / 2;
            
            if (i === 0) {
                this.waveformCtx.moveTo(x, y);
            } else {
                this.waveformCtx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        this.waveformCtx.stroke();
        
        // Draw frequency bars
        this.analyser.getByteFrequencyData(this.dataArray);
        
        const barWidth = width / this.bufferLength * 2.5;
        let barX = 0;
        
        for (let i = 0; i < this.bufferLength; i += 2) {
            const barHeight = (this.dataArray[i] / 255) * height * 0.8;
            
            const hue = (i / this.bufferLength) * 240;
            this.waveformCtx.fillStyle = `hsla(${hue}, 70%, 60%, 0.6)`;
            this.waveformCtx.fillRect(barX, height - barHeight, barWidth, barHeight);
            
            barX += barWidth + 1;
            
            if (barX > width) break;
        }
    }
    
    getAudioReactiveIntensity() {
        // Return normalized intensity for LED effects
        return {
            bass: this.bassLevel,
            mid: this.midLevel,
            treble: this.trebleLevel,
            overall: (this.bassLevel + this.midLevel + this.trebleLevel) / 3
        };
    }
    
    applyBeatReactiveEffect(renderer, layer, baseIntensity = 1.0) {
        if (!this.beatSyncEnabled) return baseIntensity;
        
        // Increase brightness on bass hits
        const reactivity = this.bassLevel * 0.5;
        return Math.min(1.0, baseIntensity * (1 + reactivity));
    }
}

window.AudioSync = AudioSync;
