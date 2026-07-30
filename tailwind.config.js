/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.jinja",
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Figtree", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        creameBg: "#FDFBF7",
        creameSurface: "#FFFFFF",
        brand: "#b45309",
        brandHover: "#92400e",
        textMain: "#292524",
        textMuted: "#78716c",
        control: {
          bg: "#f5f5f4",
          panel: "#ffffff",
          border: "#e7e5e4",
          muted: "#78716c",
          text: "#1c1917",
          accent: "#b45309",
          warn: "#d97706",
          danger: "#dc2626",
          link: "#b45309",
        },
      },
    },
  },
  plugins: [],
};
