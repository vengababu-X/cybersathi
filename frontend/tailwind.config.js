/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Calm, trust-building palette. Risk colours are always paired with an icon and a
        // text label in the UI — never colour alone, for colour-blind users.
        brand: {
          50: '#eef4ff', 100: '#dae6ff', 200: '#bcd2ff', 300: '#8eb3ff',
          400: '#5a8bff', 500: '#3563eb', 600: '#2347c7', 700: '#1e3a8a',
          800: '#1e3a5f', 900: '#172554',
        },
        accent: {
          50: '#f0fdfa', 100: '#ccfbf1', 200: '#99f6e4', 300: '#5eead4',
          400: '#2dd4bf', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e',
          800: '#115e59', 900: '#134e4a',
        },
        risk: {
          safe: '#15803d',
          suspicious: '#b45309',
          high: '#b91c1c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        tamil: ['Noto Sans Tamil', 'Nirmala UI', 'Latha', 'sans-serif'],
      },
      keyframes: {
        'fade-in': { '0%': { opacity: '0', transform: 'translateY(6px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        'sweep': { '0%': { strokeDashoffset: 'var(--dash-full)' }, '100%': { strokeDashoffset: 'var(--dash-target)' } },
      },
      animation: {
        'fade-in': 'fade-in 0.35s ease-out',
        'sweep': 'sweep 0.9s ease-out forwards',
      },
    },
  },
  plugins: [],
}
