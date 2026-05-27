import { memo } from "react";

import { getStatusTone } from "@/lib/tokens";
import type { TaskStatus } from "@/types/todo";

interface StatusBadgeProps {
  status: TaskStatus;
  className?: string;
}

function StatusBadgeComponent({ status, className = "" }: StatusBadgeProps) {
  const tone = getStatusTone(status);

  return (
    <span
      className={`inline-flex h-6 shrink-0 items-center justify-center rounded-full px-3 text-[11px] font-semibold leading-none ${tone.badge} ${className}`}
    >
      {status}
    </span>
  );
}

export const StatusBadge = memo(StatusBadgeComponent);
