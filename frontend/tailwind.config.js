/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        line: "#d8dee8",
        surface: "#f6f8fb",
        brand: "#0f766e",
        accent: "#b45309"
      }
    },
  },
  plugins: [],
};
