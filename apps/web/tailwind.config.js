/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // INCOME design system
        primary: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#bac8ff",
          300: "#91a7ff",
          400: "#748ffc",
          500: "#5c7cfa",
          600: "#4c6ef5",
          700: "#1e3a8a",  // Deep navy blue
          800: "#1e3a8a",
          900: "#0f2563",
          950: "#0a1a4e",
          DEFAULT: "#1e3a8a",
        },
        secondary: {
          DEFAULT: "#2563eb", // Royal blue
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        accent: {
          DEFAULT: "#059669", // Emerald
          light: "#d1fae5",
          50: "#ecfdf5",
          100: "#d1fae5",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
        surface: {
          DEFAULT: "#f8fafc",   // Off-white background
          card: "#ffffff",
          border: "#e2e8f0",
          muted: "#f1f5f9",
        },
        text: {
          primary: "#1e293b",   // Dark charcoal
          secondary: "#64748b",
          muted: "#94a3b8",
          inverse: "#ffffff",
        },
        status: {
          success: "#059669",
          warning: "#d97706",
          error: "#dc2626",
          info: "#2563eb",
          pending: "#7c3aed",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        modal: "0 25px 50px -12px rgb(0 0 0 / 0.25)",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
      },
      screens: {
        xs: "480px",
      },
    },
  },
  plugins: [],
};
