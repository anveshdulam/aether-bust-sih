/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        bg: { canvas: '#0e131a', panel: '#151b23', raised: '#1b222c' },
        border: { DEFAULT: '#262f3b' },
        text: { primary: '#e8ecf1', muted: '#9aa5b4' },
        accent: { DEFAULT: '#4c9be8' },
        status: { red: '#ef4444', amber: '#f59e0b', sky: '#38bdf8', green: '#34d399' },
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '4px',
        md: '4px',
        lg: '4px',
        xl: '4px',
        '2xl': '4px',
        '3xl': '4px'
      },
      boxShadow: {
        none: 'none',
        popover: '0 8px 24px rgba(0,0,0,0.55)',
      },
    },
  },
  plugins: [],
};
