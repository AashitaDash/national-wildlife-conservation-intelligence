/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:  ['"Instrument Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Newsreader"', 'Georgia', 'serif'],
        mono:  ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        // ── New institutional palette ──────────────────
        shell: {
          50:  '#f4f4f2', 100: '#e9e8e5', 200: '#d1cfc8', 300: '#b5b3a9',
          400: '#94918a', 500: '#77746c', 600: '#5e5b54', 700: '#484640',
          800: '#33312c', 900: '#1f1e1a', 950: '#131210',
        },
        forest: {
          50:  '#edfaf0', 100: '#d2f5db', 200: '#a7ebba', 300: '#6fd98b',
          400: '#3fc067', 500: '#1fa34a', 600: '#13843a', 700: '#11682f',
          800: '#0f5126', 900: '#0c4320', 950: '#052510',
        },
        cream: {
          50:  '#fdfcfa', 100: '#faf8f4', 200: '#f5f1ea', 300: '#ede6d8',
          400: '#ddd4c0', 500: '#c9bfa7', 600: '#b0a38a', 700: '#918470',
          800: '#726758', 900: '#504940', 950: '#302c27',
        },
        // ── Legacy compat: old component classes ───────
        charcoal: {
          50:  '#f4f4f2', 100: '#e9e8e5', 200: '#d1cfc8', 300: '#b5b3a9',
          400: '#94918a', 500: '#77746c', 600: '#5e5b54', 700: '#484640',
          800: '#2a2924', 900: '#1a1916', 950: '#131210',
        },
        earthy: {
          50:  '#fdfcfa', 100: '#faf8f4', 200: '#f0ede6', 300: '#ddd8cf',
          400: '#b5b3a9', 500: '#94918a', 600: '#77746c', 700: '#5e5b54',
          800: '#484640', 900: '#33312c', 950: '#1a1916',
        },
        warmwhite: '#faf8f4',
      },
      borderRadius: {
        sm:    '2px',
        DEFAULT: '4px',
        md:    '6px',
        lg:    '8px',
        xl:    '10px',
        '2xl': '12px',
        '3xl': '16px',
      },
    },
  },
  plugins: [],
}
