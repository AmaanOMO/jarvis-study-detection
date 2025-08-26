/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'jarvis-bg': '#0b0f14',
        'jarvis-primary': '#5AB4FF',
        'jarvis-accent': '#00E1FF',
        'jarvis-glow': '#4A90E2'
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}
