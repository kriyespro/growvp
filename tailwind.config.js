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
          bg: "#0f1419",
          panel: "#161b22",
          border: "#30363d",
          muted: "#8b949e",
          text: "#e6edf3",
          accent: "#3fb950",
          warn: "#d29922",
          danger: "#f85149",
          link: "#58a6ff",
        },
      },
    },
  },
  plugins: [],
};
