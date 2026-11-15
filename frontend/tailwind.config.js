// tailwind.config.js — Evalify's "marked paper" design tokens.
// Warm paper neutrals, ink-blue actions, one red-pen accent, square corners, hairlines instead of shadows.
// The palette names Tailwind already used across the pages (gray, green, red, amber, …) are remapped here so
// every existing page picks up the same look without per-page colour edits.

// Warm paper → ink neutrals (replaces gray)
const paper = { 50: "#FBFAF6", 100: "#F4F1EA", 200: "#E9E4D8", 300: "#D8D1C1", 400: "#B4AC9B",
                500: "#8A8476", 600: "#686358", 700: "#4A463F", 800: "#2C2A26", 900: "#1B1A17" };
// Fountain-pen ink blue: links, primary actions, active states (replaces green, blue, indigo)
const ink = { 50: "#EEF2F7", 100: "#DCE4EE", 200: "#B8C7DA", 300: "#8DA4C1", 400: "#5E7EA5", 500: "#3B5E88",
              600: "#21446F", 700: "#1A3758", 800: "#132A44", 900: "#0D1D2F" };
// Teacher's red pen: marks, flags, errors (replaces red)
const pen = { 50: "#FBEFED", 100: "#F5DAD6", 200: "#EBB4AC", 300: "#DC877A", 400: "#C95B4B", 500: "#B12A20",
              600: "#99231B", 700: "#7C1C16", 800: "#5E1510", 900: "#410E0B" };
// Ochre highlighter: warnings, pending (replaces amber / yellow / orange)
const ochre = { 50: "#FAF4E4", 100: "#F2E4BF", 200: "#E6CB8B", 300: "#D6AD57", 400: "#C09233", 500: "#A3781B",
                600: "#876213", 700: "#6A4C0E", 800: "#4D370A", 900: "#332406" };
// Moss: correct / done (replaces emerald, teal)
const moss = { 50: "#EFF3EC", 100: "#DCE6D6", 200: "#B8CCAE", 300: "#8FAE82", 400: "#678E59", 500: "#4A713D",
               600: "#3A5B30", 700: "#2E4826", 800: "#22361C", 900: "#172413" };

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper, ink, pen, ochre, moss,
        gray: paper, green: ink, blue: ink, indigo: ink, sky: ink,
        red: pen, amber: ochre, yellow: ochre, orange: ochre, emerald: moss, teal: moss,
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      // Square, printed-form corners everywhere (pills stay round)
      borderRadius: { sm: "1px", DEFAULT: "2px", md: "2px", lg: "2px", xl: "3px", "2xl": "3px", "3xl": "4px" },
      // No floating cards: shadows become a hairline
      boxShadow: { sm: "0 0 0 1px rgba(27,26,23,0.04)", DEFAULT: "none", md: "0 1px 0 rgba(27,26,23,0.06)",
                   lg: "0 1px 0 rgba(27,26,23,0.08)", xl: "0 2px 0 rgba(27,26,23,0.08)" },
      letterSpacing: { label: "0.08em" },
    },
  },
  plugins: [],
};
