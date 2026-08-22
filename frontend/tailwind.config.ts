import type { Config } from "tailwindcss";

/**
 * KhaataPulse design tokens — CLAUDE.md §29.
 * Every colour carries semantic meaning. No decorative palette entries.
 */
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
        // ── Surfaces ────────────────────────────────────────────────────
        "bg-primary": "#07090D",
        "bg-secondary": "#0C1017",
        surface: "#11161F",
        "surface-elevated": "#161E2A",
        "surface-hover": "#1C2535",

        // ── Borders ─────────────────────────────────────────────────────
        border: "#1E2D3D",
        "border-subtle": "#172030",

        // ── Semantic accents ────────────────────────────────────────────
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
          DEFAULT: "#6366F1",
          dim: "#1E1B4B",
          text: "#A5B4FC",
        },

        // ── Text ────────────────────────────────────────────────────────
        "text-primary": "#F1F5F9",
        "text-secondary": "#94A3B8",
        "text-muted": "#475569",
        "text-faint": "#334155",
      },

      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "Fira Code", "monospace"],
      },

      fontSize: {
        hero: ["3.5rem", { lineHeight: "1.04", letterSpacing: "-0.035em", fontWeight: "700" }],
        display: ["2rem", { lineHeight: "1.1", letterSpacing: "-0.025em", fontWeight: "700" }],
        metric: ["1.75rem", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" }],
        eyebrow: ["0.6875rem", { lineHeight: "1.4", letterSpacing: "0.16em", fontWeight: "500" }],
      },

      letterSpacing: {
        tightest: "-0.04em",
        eyebrow: "0.16em",
      },

      spacing: {
        section: "7rem",
        "section-sm": "4.5rem",
      },

      maxWidth: {
        prose: "38rem",
        shell: "80rem",
      },

      borderRadius: {
        panel: "0.625rem",
      },

      transitionTimingFunction: {
        out: "cubic-bezier(0.16, 1, 0.3, 1)",
        "in-out": "cubic-bezier(0.65, 0, 0.35, 1)",
      },

      transitionDuration: {
        fast: "160ms",
        base: "260ms",
        slow: "600ms",
      },

      zIndex: {
        ambient: "0",
        content: "10",
        nav: "50",
        overlay: "60",
        drawer: "70",
      },

      backgroundImage: {
        "grid-subtle": "radial-gradient(circle, #1E2D3D 1px, transparent 1px)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },

      backgroundSize: {
        grid: "28px 28px",
      },

      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fade-in 0.35s cubic-bezier(0.16, 1, 0.3, 1) both",
        "rise-in": "rise-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "slide-in": "slide-in-right 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
      },

      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "rise-in": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },

      boxShadow: {
        surface: "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.6)",
        panel: "0 1px 2px rgba(0,0,0,0.5), 0 8px 24px -12px rgba(0,0,0,0.8)",
        "glow-recovery": "0 0 16px rgba(16,185,129,0.15)",
        "glow-warning": "0 0 16px rgba(245,158,11,0.15)",
        "glow-critical": "0 0 16px rgba(239,68,68,0.15)",
        "glow-ai": "0 0 16px rgba(99,102,241,0.15)",
      },
    },
  },
  plugins: [],
};

export default config;
