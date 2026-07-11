import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        elevated: "var(--bg-elevated)",
        overlay: "var(--bg-overlay)",
        border: "var(--border)",
        hot: "var(--border-hot)",
        fg: {
          DEFAULT: "var(--fg)",
          muted: "var(--fg-muted)",
          dim: "var(--fg-dim)",
        },
        muted: "var(--fg-muted)",
        dim: "var(--fg-dim)",
        accent: "var(--accent)",
        danger: "var(--danger)",
        warning: "var(--warning)",
        info: "var(--info)"
      },
      boxShadow: {
        phosphor: "0 0 0 1px rgba(0,255,102,0.15), 0 0 32px rgba(0,255,102,0.08)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
