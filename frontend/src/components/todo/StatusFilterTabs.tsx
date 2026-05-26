import { filterTabs } from "@/lib/tokens";
import type { StatusFilter } from "@/types/todo";

interface StatusFilterTabsProps {
  value: StatusFilter;
  onChange: (value: StatusFilter) => void;
}

export function StatusFilterTabs({ value, onChange }: StatusFilterTabsProps) {
  return (
    <nav className="grid grid-cols-5 gap-[5px]" aria-label="任务视图">
      {filterTabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          className={`tm-desktop-paint-lite h-8 rounded-default text-[12px] font-medium transition ${
            value === tab.value ? "border border-line bg-surface-strong text-ink" : "text-muted hover:bg-surface-soft"
          }`}
          onClick={() => onChange(tab.value)}
          aria-pressed={value === tab.value}
          title={`筛选${tab.label}`}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
