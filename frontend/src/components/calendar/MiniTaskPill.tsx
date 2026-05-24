import { getStatusTone } from "@/lib/tokens";
import type { Task } from "@/types/todo";

interface MiniTaskPillProps {
  task: Task;
}

export function MiniTaskPill({ task }: MiniTaskPillProps) {
  const tone = getStatusTone(task.status);

  return (
    <span
      className={`block h-[21px] truncate rounded-[6px] px-2 py-1 text-[11px] font-semibold leading-none ${tone.mini}`}
      title={task.title}
    >
      {task.title}
    </span>
  );
}
