import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // FutureLens Brand Colors
        navy: {
          950: "#05070f",
          900: "#070d1a",
          800: "#0d1b33",
          700: "#112244",
          600: "#163060",
        },
        violet: {
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        crimson: {
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
        },
        gold: {
          400: "#fbbf24",
          500: "#f59e0b",
        },
        glass: {
          white: "rgba(255,255,255,0.05)",
          border: "rgba(255,255,255,0.1)",
          hover: "rgba(255,255,255,0.08)",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "hero-gradient": "linear-gradient(135deg, #05070f 0%, #0d1b33 50%, #112244 100%)",
        "card-gradient": "linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(16,185,129,0.05) 100%)",
        "success-gradient": "linear-gradient(135deg, #059669, #10b981)",
        "danger-gradient": "linear-gradient(135deg, #dc2626, #ef4444)",
        "violet-gradient": "linear-gradient(135deg, #6d28d9, #8b5cf6)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "count-up": "countUp 1s ease-out",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(139,92,246,0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(139,92,246,0.6)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
