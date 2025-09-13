// Clash Royale inspired color palette and design system
// Using colors that are similar but not identical to avoid copyright issues

export const clashRoyaleTheme = {
  colors: {
    // Primary palette - inspired by CR but original
    primary: {
      blue: {
        50: '#e6f3ff',
        100: '#bae2ff',
        200: '#8dd0ff',
        300: '#60beff',
        400: '#33acff',
        500: '#069aff', // Main blue
        600: '#0588e6',
        700: '#0476cc',
        800: '#0364b3',
        900: '#025299'
      },
      purple: {
        50: '#f3e6ff',
        100: '#e2baff',
        200: '#d08dff',
        300: '#be60ff',
        400: '#ac33ff',
        500: '#9a06ff', // Main purple
        600: '#8805e6',
        700: '#7604cc',
        800: '#6403b3',
        900: '#520299'
      },
      orange: {
        50: '#fff3e6',
        100: '#ffe2ba',
        200: '#ffd08d',
        300: '#ffbe60',
        400: '#ffac33',
        500: '#ff9a06', // Main orange
        600: '#e68805',
        700: '#cc7604',
        800: '#b36403',
        900: '#995202'
      },
      yellow: {
        50: '#fffee6',
        100: '#fffcba',
        200: '#fff98d',
        300: '#fff660',
        400: '#fff333',
        500: '#fff006', // Main yellow
        600: '#e6d805',
        700: '#ccbf04',
        800: '#b3a603',
        900: '#998d02'
      }
    },
    
    // Rarity colors (Accurate Clash Royale colors)
    rarity: {
      common: {
        from: '#87ceeb',  // Sky blue
        to: '#4682b4',    // Steel blue
        border: '#2c5aa0',
        text: '#ffffff'
      },
      rare: {
        from: '#ffa500',  // Orange
        to: '#ff8c00',    // Dark orange
        border: '#ff6347',
        text: '#ffffff'
      },
      epic: {
        from: '#9370db',  // Medium purple
        to: '#8a2be2',    // Blue violet
        border: '#4b0082',
        text: '#ffffff'
      },
      legendary: {
        from: '#e6e6fa',  // Lavender (silver with purple hue)
        to: '#d8bfd8',    // Thistle
        border: '#9370db',
        text: '#4b0082'
      },
      champion: {
        from: '#ffd700',  // Gold
        to: '#ffb347',    // Light orange/yellow
        border: '#daa520',
        text: '#000000'
      }
    },

    // UI States
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
    
    // Backgrounds
    dark: {
      100: '#1e293b',
      200: '#334155',
      300: '#475569',
      400: '#64748b',
      500: '#94a3b8'
    }
  },

  // Clash Royale inspired typography
  typography: {
    fontFamily: {
      heading: ['Supercell-Magic', 'Arial Black', 'Helvetica', 'sans-serif'],
      body: ['Supercell-Text', 'Arial', 'Helvetica', 'sans-serif'],
      mono: ['Consolas', 'Monaco', 'monospace']
    },
    
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem'
    }
  },

  // Component specific styles
  components: {
    card: {
      shadow: '0 8px 25px -8px rgba(0, 0, 0, 0.3)',
      hoverShadow: '0 12px 35px -8px rgba(0, 0, 0, 0.4)',
      borderRadius: '12px'
    },
    
    button: {
      primary: 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700',
      secondary: 'bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700',
      success: 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700',
      warning: 'bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700',
      danger: 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700'
    }
  },

  // Animation constants
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms'
    },
    easing: {
      default: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    }
  }
};

// Utility functions for theme usage
export const getCardRarityStyles = (rarity: 'common' | 'rare' | 'epic' | 'legendary' | 'champion') => {
  const rarityStyle = clashRoyaleTheme.colors.rarity[rarity];
  return {
    background: `linear-gradient(135deg, ${rarityStyle.from}, ${rarityStyle.to})`,
    borderColor: rarityStyle.border,
    color: rarityStyle.text
  };
};

export const getElixirColor = (cost: number) => {
  if (cost <= 2) return clashRoyaleTheme.colors.primary.blue[500];
  if (cost <= 4) return clashRoyaleTheme.colors.primary.purple[500];
  if (cost <= 6) return clashRoyaleTheme.colors.primary.orange[500];
  return clashRoyaleTheme.colors.error;
};

export const getTrophyColor = (trophies: number) => {
  if (trophies >= 5000) return clashRoyaleTheme.colors.rarity.legendary.from;
  if (trophies >= 4000) return clashRoyaleTheme.colors.rarity.epic.from;
  if (trophies >= 3000) return clashRoyaleTheme.colors.rarity.rare.from;
  return clashRoyaleTheme.colors.rarity.common.from;
};

// CSS-in-JS helper for styled components
export const styled = {
  clashButton: `
    font-family: ${clashRoyaleTheme.typography.fontFamily.heading.join(', ')};
    font-weight: bold;
    padding: 12px 24px;
    border-radius: ${clashRoyaleTheme.components.card.borderRadius};
    border: 3px solid;
    box-shadow: ${clashRoyaleTheme.components.card.shadow};
    transition: all ${clashRoyaleTheme.animation.duration.normal} ${clashRoyaleTheme.animation.easing.default};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
    
    &:hover {
      box-shadow: ${clashRoyaleTheme.components.card.hoverShadow};
      transform: translateY(-2px);
    }
    
    &:active {
      transform: translateY(0);
    }
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      transition: left ${clashRoyaleTheme.animation.duration.slow} ${clashRoyaleTheme.animation.easing.default};
    }
    
    &:hover::before {
      left: 100%;
    }
  `,
  
  clashCard: `
    background: ${clashRoyaleTheme.colors.dark[100]};
    border-radius: ${clashRoyaleTheme.components.card.borderRadius};
    box-shadow: ${clashRoyaleTheme.components.card.shadow};
    border: 2px solid rgba(255, 255, 255, 0.1);
    transition: all ${clashRoyaleTheme.animation.duration.normal} ${clashRoyaleTheme.animation.easing.default};
    
    &:hover {
      box-shadow: ${clashRoyaleTheme.components.card.hoverShadow};
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-4px);
    }
  `,
  
  clashGradientText: `
    background: linear-gradient(135deg, ${clashRoyaleTheme.colors.primary.yellow[400]}, ${clashRoyaleTheme.colors.primary.orange[500]});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: ${clashRoyaleTheme.typography.fontFamily.heading.join(', ')};
    font-weight: bold;
  `
};

export default clashRoyaleTheme;
