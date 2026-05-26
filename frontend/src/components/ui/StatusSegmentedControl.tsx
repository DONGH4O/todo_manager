import { statusList } from "@/lib/tokens";
import type { TaskStatus } from "@/types/todo";

interface StatusSegmentedControlProps {
  value: TaskStatus;
  onChange: (status: TaskStatus) => void;
}

export function StatusSegmentedControl({ value, onChange }: StatusSegmentedControlProps) {
  return (
    <div className="grid h-[42px] grid-cols-4 gap-1 rounded-default border border-line bg-surface-soft p-1">
      {statusList.map((status) => (
        <button
          key={status}
          type="button"
          className={`tm-desktop-paint-lite min-w-0 rounded-[6px] px-2 text-[12px] font-medium transition ${
            value === status
              ? "border border-line-strong bg-surface-strong text-ink shadow-sm"
              : "text-muted hover:bg-surface"
          }`}
          aria-pressed={value === status}
          title={`设置为${status}`}
          onClick={() => onChange(status)}
        >
          {status}
        </button>
      ))}
    </div>
  );
}
