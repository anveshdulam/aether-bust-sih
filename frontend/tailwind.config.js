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
        bg: { base: '#0B1220', panel: '#121C2E', elevated: '#1A2740', inset: '#0E1626' },
        border: { subtle: '#233049', strong: '#33507A' },
        text: { primary: '#E6EDF7', secondary: '#9FB0C9', muted: '#5F7291' },
        accent: { primary: '#2F81F7', focus: '#58A6FF' },
        status: { ok: '#2EA043', warn: '#D29922', crit: '#F85149', info: '#388BFD' },
      },
      borderRadius: {
        md: '6px',
        lg: '10px',
        xl: '14px',
      },
      boxShadow: {
        panel: '0 2px 8px rgba(0,0,0,0.45)',
        pop: '0 8px 24px rgba(0,0,0,0.55)',
      },
    },
  },
  plugins: [],
};
