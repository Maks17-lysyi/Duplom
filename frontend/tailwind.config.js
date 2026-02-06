/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
            // Backgrounds
            background: "#0F172A", // Slate 900
            surface: "#1E293B",    // Slate 800
            "surface-hover": "#334155", // Slate 700
            
            // Text
            primary: "#F8FAFC",   // Slate 50
            secondary: "#94A3B8", // Slate 400
            muted: "#64748B",     // Slate 500

            // Accents
            accent: "#8B5CF6",    // Violet 500
            "accent-hover": "#7C3AED", // Violet 600
            success: "#22C55E",   // Green 500
            error: "#EF4444",     // Red 500
            warning: "#F59E0B",   // Amber 500
        },
        fontFamily: {
            sans: ['Outfit', 'Inter', 'sans-serif'],
        }
      },
    },
    plugins: [],
  }
