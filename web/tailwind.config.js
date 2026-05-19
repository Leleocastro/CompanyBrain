/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#1e1e2e',
          alt: '#181825',
          hover: '#313244',
        },
        border: '#45475a',
        text: {
          primary: '#cdd6f4',
          secondary: '#a6adc8',
          muted: '#6c7086',
        },
        accent: {
          blue: '#89b4fa',
          green: '#a6e3a1',
          peach: '#fab387',
          mauve: '#cba6f7',
          red: '#f38ba8',
        },
      },
    },
  },
  plugins: [],
}
