import { formatDateRange } from "@/lib/date";
import { getStatusTone } from "@/lib/tokens";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Task } from "@/types/todo";

interface TaskCardProps {
  task: Task;
  selected: boolean;
  onSelect: (task: Task) => void;
}

export function TaskCard({ task, selected, onSelect }: TaskCardProps) {
  const completedSubtasks = task.subtasks.filter((subtask) => subtask.status === "已完成").length;
  const tone = getStatusTone(task.status);

  return (
    <button
      type="button"
      className={`min-h-[144px] w-full rounded-default border bg-surface-soft p-3 text-left transition hover:border-line-strong hover:bg-surface ${
        selected ? "border-primary shadow-focus" : "border-line"
      }`}
      title={`查看 ${task.title}`}
      aria-label={`查看 ${task.title}`}
      onClick={() => onSelect(task)}
    >
      <div className="flex min-w-0 items-start gap-2">
        <span className={`mt-1.5 size-2 shrink-0 rounded-full ${tone.dot}`} aria-hidden="true" />
        <span className={`min-w-0 flex-1 truncate text-[14px] font-bold text-ink ${tone.row}`}>
          {task.title}
        </span>
        <StatusBadge status={task.status} />
      </div>
      <div className="mt-2 text-[12px] text-muted">{formatDateRange(task)}</div>
      <p className="mt-2 line-clamp-2 text-[12px] leading-snug text-muted">{task.background}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="inline-flex h-6 items-center rounded-full bg-neutral-silver px-3 text-[11px] font-semibold text-ink">
          {task.subtasks.length} 个子任务
        </span>
        <span className="inline-flex h-6 items-center rounded-full bg-secondary-soft px-3 text-[11px] font-semibold text-secondary">
          {completedSubtasks} 已完成
        </span>
      </div>
    </button>
  );
}
