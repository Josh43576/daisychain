/**
 * Neon Effects Configuration & Theme Manager
 * Easily customize colors, animations, and effects
 */

class NeonTheme {
    constructor(themeName = 'cyberpunk-blue') {
        this.themes = {
            'cyberpunk-blue': {
                name: 'Cyberpunk Blue',
                primary: '#00d4ff',
                secondary: '#00a8cc',
                accent: '#a0d8ff',
                background: '#0a0e27',
                backgroundDark: '#05070f',
                glow: 'rgba(0, 212, 255, 0.5)',
                description: 'Classic sky-blue neon with electric glow'
            },
            'synthwave-pink': {
                name: 'Synthwave Pink',
                primary: '#ff006e',
                secondary: '#d60048',
                accent: '#ff4d8f',
                background: '#1a0024',
                backgroundDark: '#0a0012',
                glow: 'rgba(255, 0, 110, 0.5)',
                description: 'Retro synthwave pink and purple'
            },
            'matrix-green': {
                name: 'Matrix Green',
                primary: '#39ff14',
                secondary: '#2ea00e',
                accent: '#70ff60',
                background: '#0a1a00',
                backgroundDark: '#050d00',
                glow: 'rgba(57, 255, 20, 0.5)',
                description: 'Classic Matrix digital rain effect'
            },
            'purple-haze': {
                name: 'Purple Haze',
                primary: '#c415ff',
                secondary: '#8b00cc',
                accent: '#e060ff',
                background: '#1a0033',
                backgroundDark: '#0d001a',
                glow: 'rgba(196, 21, 255, 0.5)',
                description: 'Mystical purple and violet neon'
            },
            'ice-cyan': {
                name: 'Ice Cyan',
                primary: '#00ffff',
                secondary: '#00b3cc',
                accent: '#80ffff',
                background: '#001a20',
                backgroundDark: '#000d10',
                glow: 'rgba(0, 255, 255, 0.5)',
                description: 'Cool cyan and ice-blue tones'
            },
            'hot-orange': {
                name: 'Hot Orange',
                primary: '#ff6b00',
                secondary: '#ff9f00',
                accent: '#ffb366',
                background: '#2a1400',
                backgroundDark: '#1a0a00',
                glow: 'rgba(255, 107, 0, 0.5)',
                description: 'Fiery orange and flame colors'
            },
            'mint-green': {
                name: 'Mint Green',
                primary: '#00ff9f',
                secondary: '#00cc80',
                accent: '#66ffcc',
                background: '#001a14',
                backgroundDark: '#000d0a',
                glow: 'rgba(0, 255, 159, 0.5)',
                description: 'Fresh mint and emerald green'
            },
            'coral-pink': {
                name: 'Coral Pink',
                primary: '#ff6b9d',
                secondary: '#ff5588',
                accent: '#ff99b9',
                background: '#2a1620',
                backgroundDark: '#1a0d14',
                glow: 'rgba(255, 107, 157, 0.5)',
                description: 'Warm coral and rosy pink'
            }
        };

        this.currentTheme = themeName;
        this.animationSettings = {
            flickerSpeed: '0.15s',
            pulseSpeed: '2s',
            glowSpeed: '2.5s',
            spinSpeed: '1.5s',
            particleSpeed: '4s',
            lightningInterval: '3s',
            gridSpeed: '20s'
        };
    }

    /**
     * Get a specific theme
     */
    getTheme(themeName) {
        return this.themes[themeName] || this.themes['cyberpunk-blue'];
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.getTheme(this.currentTheme);
    }

    /**
     * Get all themes
     */
    getAllThemes() {
        return Object.keys(this.themes);
    }

    /**
     * Apply theme to page
     */
    applyTheme(themeName) {
        const theme = this.getTheme(themeName);
        if (!theme) {
            console.error(`Theme "${themeName}" not found`);
            return;
        }

        this.currentTheme = themeName;
        
        // Update CSS variables
        const root = document.documentElement;
        root.style.setProperty('--neon-primary', theme.primary);
        root.style.setProperty('--neon-secondary', theme.secondary);
        root.style.setProperty('--neon-accent', theme.accent);
        root.style.setProperty('--bg-dark', theme.background);
        root.style.setProperty('--bg-darker', theme.backgroundDark);
        root.style.setProperty('--neon-glow', theme.glow);
        
        // Update gradient
        const gradient = `linear-gradient(135deg, ${theme.background} 0%, ${theme.backgroundDark} 100%)`;
        root.style.setProperty('--bg-gradient', gradient);

        // Update body background
        document.body.style.background = gradient;

        console.log(`✨ Theme "${theme.name}" applied`);
    }

    /**
     * Set animation speed
     */
    setAnimationSpeed(speedSetting = 'normal') {
        const speeds = {
            'slow': {
                flickerSpeed: '0.25s',
                pulseSpeed: '3s',
                glowSpeed: '4s',
                spinSpeed: '2.5s'
            },
            'normal': {
                flickerSpeed: '0.15s',
                pulseSpeed: '2s',
                glowSpeed: '2.5s',
                spinSpeed: '1.5s'
            },
            'fast': {
                flickerSpeed: '0.08s',
                pulseSpeed: '1.2s',
                glowSpeed: '1.5s',
                spinSpeed: '1s'
            }
        };

        this.animationSettings = speeds[speedSetting] || speeds['normal'];
        this._updateAnimationSpeeds();
    }

    /**
     * Get animation settings
     */
    getAnimationSettings() {
        return this.animationSettings;
    }

    /**
     * Create theme switcher UI
     */
    createThemeSwitcher() {
        const switcher = document.createElement('div');
        switcher.id = 'neon-theme-switcher';
        switcher.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 10000;
            background: rgba(10, 14, 39, 0.9);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            font-family: 'Courier New', monospace;
            max-width: 300px;
        `;

        // Title
        const title = document.createElement('div');
        title.style.cssText = `
            color: #00d4ff;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 12px;
            letter-spacing: 1px;
        `;
        title.textContent = '🎨 THEME SELECTOR';
        switcher.appendChild(title);

        // Theme buttons
        Object.keys(this.themes).forEach(themeName => {
            const btn = document.createElement('button');
            const theme = this.themes[themeName];
            
            btn.textContent = theme.name;
            btn.style.cssText = `
                display: block;
                width: 100%;
                margin: 5px 0;
                padding: 8px 12px;
                background: transparent;
                border: 1px solid ${theme.primary};
                color: ${theme.primary};
                cursor: pointer;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                transition: all 0.3s ease;
                text-align: left;
            `;

            btn.onmouseover = () => {
                btn.style.boxShadow = `0 0 10px ${theme.primary}`;
                btn.style.background = `rgba(${this._hexToRgb(theme.primary).join(',')}, 0.1)`;
            };

            btn.onmouseout = () => {
                btn.style.boxShadow = 'none';
                btn.style.background = 'transparent';
            };

            btn.onclick = () => this.applyTheme(themeName);
            
            switcher.appendChild(btn);
        });

        return switcher;
    }

    /**
     * Convert hex to RGB
     */
    _hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
        ] : [0, 212, 255];
    }

    /**
     * Update animation speeds in stylesheet
     */
    _updateAnimationSpeeds() {
        // This would require injecting CSS, so we'll log for now
        console.log('Animation speeds updated:', this.animationSettings);
    }

    /**
     * Export theme as CSS variables
     */
    exportAsCSS(themeName) {
        const theme = this.getTheme(themeName);
        const css = `
:root {
    --neon-primary: ${theme.primary};
    --neon-secondary: ${theme.secondary};
    --neon-accent: ${theme.accent};
    --bg-dark: ${theme.background};
    --bg-darker: ${theme.backgroundDark};
    --neon-glow: ${theme.glow};
}`;
        return css;
    }

    /**
     * Export all themes as JSON
     */
    exportAsJSON() {
        return JSON.stringify(this.themes, null, 2);
    }
}

// Global instance
const neonTheme = new NeonTheme('cyberpunk-blue');

// Auto-apply theme on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        neonTheme.applyTheme('cyberpunk-blue');
    });
} else {
    neonTheme.applyTheme('cyberpunk-blue');
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NeonTheme;
}
