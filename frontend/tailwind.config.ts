import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f2fe",
          100: "#dde2fb",
          200: "#bcc5f8",
          300: "#9aaaf4",
          400: "#7890f0",
          500: "#5670ec",
          600: "#3450e8",  // Primary CTA (legacy — being phased out)
          700: "#2640d4",
          800: "#1a30bc",
          900: "#0e1e8c",
          950: "#080c64",
        },
        // New canonical palette (per docs/requirements.md §4.1)
        teal: "#0AE5F6",
        navy: "#080C64",
        mint: "#69E4B5",
        purple: "#9747FF",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      fontSize: {
        // Display / heading scale. Pairs: [size, lineHeight] with letterSpacing.
        // Sized for mobile; pages should scale up via md: prefix where needed.
        "h1": ["2.5rem", { lineHeight: "1.05", letterSpacing: "-0.02em", fontWeight: "700" }],
        "h2": ["2rem",   { lineHeight: "1.1",  letterSpacing: "-0.02em", fontWeight: "700" }],
        "h3": ["1.625rem", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "700" }],
        "h4": ["1.375rem", { lineHeight: "1.3", letterSpacing: "0",       fontWeight: "600" }],
        "h5": ["1.125rem", { lineHeight: "1.4", letterSpacing: "0",       fontWeight: "600" }],
        "h6": ["1rem",     { lineHeight: "1.5", letterSpacing: "0",       fontWeight: "600" }],
        // Desktop overrides via the md: variants applied at usage sites
        "h1-md": ["3.75rem", { lineHeight: "1.05", letterSpacing: "-0.02em", fontWeight: "700" }],
        "h2-md": ["2.75rem", { lineHeight: "1.1",  letterSpacing: "-0.02em", fontWeight: "700" }],
        "h3-md": ["2rem",    { lineHeight: "1.2",  letterSpacing: "-0.01em", fontWeight: "700" }],
        "h4-md": ["1.5rem",  { lineHeight: "1.3",  letterSpacing: "0",       fontWeight: "600" }],
        "h5-md": ["1.25rem", { lineHeight: "1.4",  letterSpacing: "0",       fontWeight: "600" }],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
