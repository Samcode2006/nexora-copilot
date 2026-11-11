/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coral: {
          50: '#FDF4F0',
          100: '#FBE8E1',
          200: '#F6D2C4',
          300: '#F0B39E',
          400: '#EB8A6C',
          500: '#E86338', // Vibrant warm coral / terracotta (Dribbble accent)
          600: '#D95227',
          700: '#B83F19',
          800: '#943415',
        },
        ochre: {
          50: '#FEF9EE',
          100: '#FDF1D5',
          200: '#FBE2AA',
          300: '#F7CE74',
          400: '#F5B838', // Golden yellow / marigold (from Image 2)
          500: '#E59F1E',
          600: '#C77F14',
        },
        violet: {
          50: '#F4F2FF',
          100: '#EBE7FF',
          200: '#D9D2FE',
          300: '#BFB1FE',
          400: '#9C85FC',
          500: '#7B5AF7', // Royal purple / violet (from Image 2)
          600: '#6938EF',
          700: '#5322E5',
        },
        sand: {
          50: '#FAF9F6',
          100: '#F5F3ED',
          200: '#ECE8DE', // Warm cream banner background
          300: '#DFD9CB',
          400: '#C5BCAB',
        },
        navy: {
          950: '#0B121B',
          900: '#111B27', // Deep midnight hero navy (from Image 1)
          850: '#162232',
          800: '#1F2E42',
          700: '#2A3D56',
          600: '#3D5473',
          500: '#526E94',
        },
        steel: {
          700: '#3D586E',
          600: '#4F728C',
          500: '#688CA7',
          400: '#8EB0C9',
          100: '#E9F1F6',
          50: '#F4F8FA',
        },
        canvas: {
          50: '#FAF9F6',
          100: '#F4F2EC', // Warm editorial background (Filko aesthetic)
          200: '#EAE7DD',
          300: '#DDD8CB',
        },
        charcoal: {
          950: '#121210',
          900: '#1E1D1A', // Deep espresso text
          800: '#31302C',
          700: '#4D4B46',
          600: '#6E6B65',
          500: '#8F8B83',
          400: '#B5B1A8',
          300: '#D5D1C7',
          200: '#E5E2D8',
          100: '#F0EDE4',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Outfit', '"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(18, 18, 16, 0.04)',
        'card': '0 2px 8px -2px rgba(18, 18, 16, 0.05), 0 1px 3px 0 rgba(18, 18, 16, 0.03)',
        'float': '0 12px 32px -4px rgba(18, 18, 16, 0.08), 0 4px 12px -2px rgba(18, 18, 16, 0.04)',
        'hero': '0 24px 60px -12px rgba(17, 27, 39, 0.25)',
        'dropdown': '0 16px 40px -8px rgba(18, 18, 16, 0.12), 0 4px 12px -2px rgba(18, 18, 16, 0.06)',
      }
    },
  },
  plugins: [],
}
