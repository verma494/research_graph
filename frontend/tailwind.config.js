/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        primary: '#3b82f6',
        accent: '#8b5cf6',
        text: '#f8fafc',
        muted: '#94a3b8',
      }
    },
  },
  plugins: [],
}
