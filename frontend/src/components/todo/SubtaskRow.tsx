import { StatusDropdown } from "@/components/ui/StatusDropdown";
import { getStatusTone } from "@/lib/tokens";
import type { SubTask, TaskStatus } from "@/types/todo";

interface SubtaskRowProps {
  subtask: SubTask;
  onStatusChange: (status: TaskStatus) => void;
}

export function SubtaskRow({ subtask, onStatusChange }: SubtaskRowProps) {
  const tone = getStatusTone(subtask.status);

  return (
    <div className="grid min-h-12 grid-cols-[1fr_104px] items-center gap-3 rounded-default border border-line bg-surface-soft px-3 py-2">
      <span className="min-w-0">
        <strong className={`block truncate text-[13px] font-semibold text-ink ${tone.row}`}>
          {subtask.title}
        </strong>
        <small className="block truncate text-[11px] text-muted">
          {subtask.start_date} - {subtask.end_date}
        </small>
      </span>
      <StatusDropdown
        value={subtask.status}
        onChange={onStatusChange}
        ariaLabel="设置子任务状态"
        variant="pill"
        className="h-7"
        align="right"
        menuMinWidth={116}
      />
    </div>
  );
}
