/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    // Set at theme level (not extend) so these utilities do not exist.
    boxShadow: {},
    backdropBlur: {},
    dropShadow: {},
    borderRadius: { none: '0', DEFAULT: '2px', sm: '2px', md: '3px', full: '9999px' },
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        base: '#0B1220',
        panel: '#121C2E',
        inset: '#0E1626',
        line: '#1F2A3D',
        'line-strong': '#2C3A52',
        ink: { DEFAULT: '#D9E0EA', dim: '#9AA6B8', faint: '#7A879C' },
        accent: '#2F81F7',
        status: { ok: '#2EA043', warn: '#D29922', crit: '#F85149' },
      },
      keyframes: { fade: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.45' } } },
      animation: { fade: 'fade 1.4s ease-in-out infinite' },
    },
  },
  plugins: [],
};
