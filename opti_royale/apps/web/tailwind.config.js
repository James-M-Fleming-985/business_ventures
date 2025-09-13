/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Clash Royale inspired colors
        'cr-blue': {
          DEFAULT: '#4A90E2',
          50: '#E8F4FD',
          100: '#D1E9FB',
          200: '#A3D3F7',
          300: '#75BDF3',
          400: '#47A7EF',
          500: '#4A90E2',
          600: '#2B7BC8',
          700: '#1F5B95',
          800: '#143C62',
          900: '#0A1E31'
        },
        'cr-purple': {
          DEFAULT: '#9B59B6',
          50: '#F4E6F7',
          100: '#E8CCEF',
          200: '#D199DF',
          300: '#BA66CF',
          400: '#A333BF',
          500: '#9B59B6',
          600: '#7D4694',
          700: '#5F3371',
          800: '#40204F',
          900: '#220D2C'
        },
        'cr-orange': {
          DEFAULT: '#E67E22',
          50: '#FDF2E9',
          100: '#FCE4D3',
          200: '#F8C9A7',
          300: '#F4AE7B',
          400: '#F0934F',
          500: '#E67E22',
          600: '#C0651C',
          700: '#944C15',
          800: '#68330F',
          900: '#3C1A08'
        },
        'cr-gold': {
          DEFAULT: '#F1C40F',
          50: '#FEFCE8',
          100: '#FEF9C3',
          200: '#FEF08A',
          300: '#FDE047',
          400: '#FACC15',
          500: '#F1C40F',
          600: '#CA8A04',
          700: '#A16207',
          800: '#854D0E',
          900: '#713F12'
        }
      },
      animation: {
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      fontFamily: {
        'clash': ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'cr-card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        'cr-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      },
      backgroundImage: {
        'cr-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'cr-card-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
      }
    },
  },
  plugins: [],
};
