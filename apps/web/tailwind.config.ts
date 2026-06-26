import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211c",
        field: "#f5f7f4",
        line: "#d8ded8",
        accent: "#1f7a5c",
        amber: "#b56a12",
        danger: "#b33838",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
