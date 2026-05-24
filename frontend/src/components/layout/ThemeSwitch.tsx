import { themeOptions } from "@/lib/tokens";
import type { ThemeMode } from "@/types/todo";

interface ThemeSwitchProps {
  value: ThemeMode;
  onChange: (mode: ThemeMode) => void;
}

export function ThemeSwitch({ value, onChange }: ThemeSwitchProps) {
  return (
    <div
      className="grid h-11 grid-cols-3 gap-1 rounded-default border border-line bg-surface-soft p-1"
      role="group"
      aria-label="主题模式"
    >
      {themeOptions.map((option) => {
        const active = option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            className={`inline-flex min-w-[62px] items-center justify-center gap-1 rounded-[6px] px-2 text-[12px] font-semibold transition ${
              active
                ? "border border-line-strong bg-surface-strong text-primary shadow-sm"
                : "text-muted hover:bg-surface"
            }`}
            title={option.title}
            aria-label={option.title}
            aria-pressed={active}
            onClick={() => onChange(option.value)}
          >
            <span aria-hidden="true">{option.icon}</span>
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
