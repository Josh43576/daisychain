/**
 * Neon Lightning Effects System
 * Provides reusable functions for creating dynamic neon visual effects
 */

class NeonEffects {
    constructor(options = {}) {
        this.container = options.container || document.getElementById('lightningContainer');
        this.lightningColor = options.lightningColor || '#00d4ff';
        this.backgroundColor = options.backgroundColor || '#0a0e27';
        this.particleColor = options.particleColor || '#00d4ff';
        this.intensity = options.intensity || 1;
        this.enabled = true;
    }

    /**
     * Generate a random lightning bolt
     */
    generateLightning(startX = null, startY = null) {
        if (!this.enabled || !this.container) return;

        const bolt = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        
        startX = startX || Math.random() * window.innerWidth;
        startY = startY || -10;
        const endX = startX + (Math.random() - 0.5) * 400;
        const endY = window.innerHeight + 10;
        
        const points = [startX, startY];
        let currentX = startX;
        let currentY = startY;
        
        // Generate zigzag points for realistic lightning
        const segments = Math.ceil(window.innerHeight / 80);
        for (let i = 0; i < segments; i++) {
            currentX += (Math.random() - 0.5) * 200;
            currentY += (window.innerHeight / (segments - 1));
            points.push(currentX, currentY);
        }
        
        points.push(endX, endY);
        
        bolt.setAttribute('points', points.join(' '));
        bolt.setAttribute('stroke', this.lightningColor);
        bolt.setAttribute('stroke-width', 2 * this.intensity);
        bolt.setAttribute('fill', 'none');
        bolt.style.opacity = '0.8';
        bolt.style.filter = `drop-shadow(0 0 ${10 * this.intensity}px ${this.lightningColor})`;
        
        this.container.appendChild(bolt);
        
        // Animate the lightning
        let opacity = 0.8;
        const duration = 0.1 + Math.random() * 0.15;
        let elapsed = 0;
        const interval = setInterval(() => {
            elapsed += 0.03;
            if (elapsed < duration) {
                opacity = 0.8 - (elapsed / duration) * 0.8;
                bolt.style.opacity = opacity;
            } else {
                clearInterval(interval);
                bolt.remove();
            }
        }, 30);
    }

    /**
     * Create a burst of lightning from a point
     */
    createLightningBurst(x, y, boltCount = 5) {
        for (let i = 0; i < boltCount; i++) {
            const angle = (360 / boltCount) * i;
            const distance = 100;
            const endX = x + Math.cos((angle * Math.PI) / 180) * distance;
            const endY = y + Math.sin((angle * Math.PI) / 180) * distance;
            
            setTimeout(() => {
                this.generateLightning(x, y);
            }, i * 100);
        }
    }

    /**
     * Start continuous lightning effect
     */
    startLightningStorm(interval = 3000) {
        const strike = () => {
            this.generateLightning();
            const nextStrike = interval + (Math.random() - 0.5) * interval;
            setTimeout(strike, nextStrike);
        };
        strike();
    }

    /**
     * Create floating particles
     */
    createParticle() {
        if (!this.enabled) return;

        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background: ${this.particleColor};
            border-radius: 50%;
            pointer-events: none;
            z-index: 3;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            opacity: 0.6;
            box-shadow: 0 0 10px ${this.particleColor};
            animation: particleFloat ${3 + Math.random() * 2}s infinite;
        `;
        
        document.body.appendChild(particle);
        
        setTimeout(() => particle.remove(), 5000);
    }

    /**
     * Start particle effect
     */
    startParticleEffect(interval = 300) {
        const spawn = () => {
            this.createParticle();
            if (this.enabled) {
                setTimeout(spawn, interval);
            }
        };
        spawn();
    }

    /**
     * Create a neon text glow effect
     */
    addNeonGlow(element, color = '#00d4ff') {
        element.style.color = color;
        element.style.textShadow = `
            0 0 10px ${color},
            0 0 20px ${color},
            0 0 40px ${color},
            0 0 80px rgba(0, 212, 255, 0.5)
        `;
        element.style.fontWeight = 'bold';
        element.style.letterSpacing = '2px';
    }

    /**
     * Create a pulsing element
     */
    addPulseEffect(element, duration = 2) {
        element.style.animation = `statusPulse ${duration}s ease-in-out infinite`;
    }

    /**
     * Create a glitch effect
     */
    addGlitchEffect(element) {
        element.style.animation = 'glitchEffect 0.5s infinite';
    }

    /**
     * Disable all effects
     */
    disable() {
        this.enabled = false;
    }

    /**
     * Enable all effects
     */
    enable() {
        this.enabled = true;
    }

    /**
     * Clear all visual effects
     */
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        document.querySelectorAll('.particle').forEach(p => p.remove());
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NeonEffects;
}

/**
 * Utility: Create a loading indicator with neon effects
 */
function createNeonLoader(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.className = 'neon-loader';
    loader.innerHTML = `
        <div class="neon-loader-content">
            <div class="loading-spinner">
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
            </div>
            <p class="neon-text" style="margin-top: 20px; font-size: 14px;">${message}</p>
        </div>
    `;
    return loader;
}

/**
 * Utility: Create a neon notification
 */
function createNeonNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(10, 14, 39, 0.95);
        border: 2px solid #00d4ff;
        color: #00d4ff;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 9999;
        animation: slideInRight 0.5s ease-out;
        font-family: 'Courier New', monospace;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideInLeft 0.5s ease-out';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
    
    return notification;
}

/**
 * Initialize neon effects globally
 */
function initializeNeonEffects() {
    // Only initialize if SVG container exists
    if (document.getElementById('lightningContainer')) {
        const effects = new NeonEffects();
        effects.startLightningStorm(3000);
        effects.startParticleEffect(300);
        return effects;
    }
    return null;
}

// Auto-initialize on DOMContentLoaded if in error/loading page
if (document.currentScript && document.currentScript.src.includes('neon_effects')) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeNeonEffects);
    } else {
        initializeNeonEffects();
    }
}
