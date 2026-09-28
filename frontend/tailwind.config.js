/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          base: '#0B1220',
          panel: '#121C2E',
          elevated: '#1A2740',
          inset: '#0E1626'
        },
        border: {
          subtle: '#233049',
          strong: '#33507A'
        },
        text: {
          primary: '#E6EDF7',
          secondary: '#9FB0C9',
          muted: '#5F7291'
        },
        accent: {
          primary: '#2F81F7',
          focus: '#58A6FF'
        },
        status: {
          ok: '#2EA043',
          warn: '#D29922',
          crit: '#F85149',
          info: '#388BFD'
        }
      },
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace']
      },
      boxShadow: {
        panel: '0 4px 20px rgba(0,0,0,0.6)',
        pop: '0 12px 32px rgba(0,0,0,0.8)'
      },
      borderRadius: {
        md: '2px',
        lg: '4px',
        xl: '6px'
      }
    },
  },
  plugins: [],
}
