import { MiniTaskPill } from "@/components/calendar/MiniTaskPill";
import type { CalendarDay } from "@/types/todo";

interface CalendarDayCellProps {
  day: CalendarDay;
  onSelect: (date: string) => void;
}

export function CalendarDayCell({ day, onSelect }: CalendarDayCellProps) {
  return (
    <button
      type="button"
      className={`group flex h-full min-h-0 flex-col rounded-default border p-2 text-left transition ${
        day.isSelected ? "border-primary shadow-focus" : "border-line hover:border-line-strong"
      } ${day.isToday ? "bg-[linear-gradient(135deg,var(--color-primary-soft),var(--color-secondary-soft))]" : "bg-surface-soft"} ${
        day.isOutsideMonth ? "opacity-55" : ""
      }`}
      title={`查看 ${day.key}`}
      aria-label={`查看 ${day.key}`}
      onClick={() => onSelect(day.key)}
    >
      <span className="flex items-center justify-between gap-2">
        <span className="font-display text-[13px] font-bold text-ink">{day.dayNumber}</span>
        {day.tasks.length ? (
          <span className="grid size-5 place-items-center rounded-full bg-primary text-[11px] font-semibold leading-none text-white">
            {day.tasks.length}
          </span>
        ) : null}
      </span>
      <span className="mt-3 hidden min-h-0 space-y-1 overflow-hidden sm:block">
        {day.tasks.slice(0, 3).map((task) => (
          <MiniTaskPill key={task.id} task={task} />
        ))}
      </span>
    </button>
  );
}
