import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf6e3",
          100: "#faecc7",
          200: "#f5d98f",
          300: "#f0c657",
          400: "#ebb31f",
          500: "#d4a017",
          600: "#a67c12",
          700: "#79590d",
          800: "#4b3708",
          900: "#1e1603",
        },
      },
    },
  },
  plugins: [],
};

export default config;
