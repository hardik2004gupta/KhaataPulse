import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // CLAUDE.md §29 design tokens
        "bg-primary": "#07090D",
        "bg-secondary": "#0C1017",
        surface: "#11161F",
        "surface-elevated": "#161E2A",
        "surface-hover": "#1C2535",
        border: "#1E2D3D",
        "border-subtle": "#172030",
        // Accent semantics
        recovery: {
          DEFAULT: "#10B981",
          dim: "#064E3B",
          text: "#34D399",
        },
        warning: {
          DEFAULT: "#F59E0B",
          dim: "#78350F",
          text: "#FCD34D",
        },
        critical: {
          DEFAULT: "#EF4444",
          dim: "#7F1D1D",
          text: "#FCA5A5",
        },
        ai: {
          DEFAULT: "#8B5CF6",
          dim: "#2E1065",
          text: "#C4B5FD",
        },
        // Text
        "text-primary": "#F1F5F9",
        "text-secondary": "#94A3B8",
        "text-muted": "#475569",
        "text-faint": "#334155",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "hero": ["3.5rem", { lineHeight: "1.05", letterSpacing: "-0.03em", fontWeight: "700" }],
        "display": ["2rem", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }],
        "metric": ["1.75rem", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" }],
      },
      backgroundImage: {
        "grid-subtle": "radial-gradient(circle, #1E2D3D 1px, transparent 1px)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      backgroundSize: {
        "grid": "28px 28px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-in": "slideIn 0.2s ease-out",
        "counter": "counter 0.8s ease-out",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideIn: { "0%": { transform: "translateX(100%)" }, "100%": { transform: "translateX(0)" } },
      },
      boxShadow: {
        "surface": "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.6)",
        "glow-recovery": "0 0 16px rgba(16,185,129,0.15)",
        "glow-warning": "0 0 16px rgba(245,158,11,0.15)",
        "glow-critical": "0 0 16px rgba(239,68,68,0.15)",
        "glow-ai": "0 0 16px rgba(139,92,246,0.15)",
      },
    },
  },
  plugins: [],
};

export default config;
