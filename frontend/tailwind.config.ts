import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: {
          a: "var(--color-bg-a)",
          b: "var(--color-bg-b)",
          c: "var(--color-bg-c)"
        },
        surface: {
          DEFAULT: "var(--color-surface)",
          soft: "var(--color-surface-soft)",
          strong: "var(--color-surface-strong)"
        },
        dropdown: "var(--color-dropdown)",
        ink: "var(--color-ink)",
        muted: "var(--color-muted)",
        line: {
          DEFAULT: "var(--color-line)",
          strong: "var(--color-line-strong)"
        },
        primary: {
          DEFAULT: "var(--color-primary)",
          soft: "var(--color-primary-soft)"
        },
        secondary: {
          DEFAULT: "var(--color-secondary)",
          soft: "var(--color-secondary-soft)"
        },
        tertiary: {
          DEFAULT: "var(--color-tertiary)",
          soft: "var(--color-tertiary-soft)"
        },
        danger: {
          DEFAULT: "var(--color-danger)",
          soft: "var(--color-danger-soft)"
        },
        neutral: {
          silver: "var(--color-neutral-silver)"
        }
      },
      fontFamily: {
        sans: [
          "Inter",
          "Plus Jakarta Sans",
          "Noto Sans SC",
          "Microsoft YaHei",
          "PingFang SC",
          "system-ui",
          "sans-serif"
        ],
        display: [
          "Plus Jakarta Sans",
          "Inter",
          "Noto Sans SC",
          "Microsoft YaHei",
          "system-ui",
          "sans-serif"
        ]
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        default: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        full: "9999px"
      },
      spacing: {
        app: "18px",
        "gutter-lg": "14px",
        "gutter-md": "12px",
        "padding-base": "10px",
        "gap-sm": "8px",
        "gap-xs": "6px"
      },
      boxShadow: {
        panel: "0 18px 50px rgba(58, 97, 124, 0.14)",
        floating: "0 26px 80px rgba(45, 84, 109, 0.24)",
        dropdown: "0 18px 42px rgba(48, 89, 115, 0.18)",
        focus: "0 0 0 4px rgba(46, 141, 245, 0.12)"
      },
      backdropBlur: {
        glass: "22px"
      }
    }
  },
  plugins: []
};

export default config;
