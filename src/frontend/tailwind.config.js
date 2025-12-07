/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Dark Teal/Forest Green (from logo)
        primary: {
          50: '#f0faf9',
          100: '#d9f2ef',
          200: '#b3e5df',
          300: '#80d1c8',
          400: '#4db8ac',
          500: '#2d8a80',
          600: '#236b63',  // Main brand color
          700: '#1a5f5f',  // Logo teal
          800: '#164d4d',
          900: '#123d3d',
        },
        // Cream/Beige (from logo background)
        cream: {
          50: '#fdfcf9',
          100: '#faf8f2',
          200: '#f5f3e8',  // Logo background
          300: '#ede9d5',
          400: '#e2dcc4',
          500: '#d4ccae',
          600: '#b8ad8a',
          700: '#968d6e',
          800: '#736b55',
          900: '#524d3f',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
