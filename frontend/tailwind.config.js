/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#030712"
        }
      },
      boxShadow: {
        glow: "0 0 40px rgba(34, 211, 238, 0.12)"
      },
      animation: {
        pulseSlow: "pulse 2.2s ease-in-out infinite"
      }
    }
  },
  plugins: []
};
