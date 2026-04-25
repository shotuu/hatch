/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "system-ui",
          "sans-serif",
        ],
        display: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        // Hatch warm light palette
        cream: {
          50: "#FFFCF7",
          100: "#FAF6EE",
          200: "#F2ECE0",
          300: "#E8DFCE",
        },
        ink: {
          DEFAULT: "#1B1714",
          muted: "#6E6760",
          subtle: "#A8A199",
          faint: "#D4CDC1",
        },
        coral: {
          50: "#FFF4ED",
          100: "#FFE6D5",
          200: "#FFC9A9",
          400: "#FF9466",
          500: "#FF7A45",
          600: "#E85D29",
          700: "#C24813",
        },
        yolk: "#FFC857",
        mint: "#5BC586",
        lavender: "#B5A3FF",
      },
      boxShadow: {
        warm: "0 1px 2px rgba(225, 188, 144, 0.08), 0 8px 24px -8px rgba(225, 144, 96, 0.18)",
        warmlg:
          "0 2px 4px rgba(225, 188, 144, 0.10), 0 24px 48px -12px rgba(225, 144, 96, 0.25)",
        bubble: "0 1px 2px rgba(60, 50, 40, 0.06)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "tick-pop": {
          "0%": { transform: "scale(0.6)", opacity: "0" },
          "60%": { transform: "scale(1.15)", opacity: "1" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in": "fade-in 240ms cubic-bezier(0.22, 1, 0.36, 1)",
        "tick-pop": "tick-pop 360ms cubic-bezier(0.34, 1.56, 0.64, 1)",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
