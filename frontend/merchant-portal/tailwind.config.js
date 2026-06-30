/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e6f7ff",
          100: "#b3e5ff",
          500: "#0099ff",
          600: "#0077cc",
          700: "#005c99",
          900: "#003d66",
        },
      },
    },
  },
  plugins: [],
};
