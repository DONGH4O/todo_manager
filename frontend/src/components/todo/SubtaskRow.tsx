import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { getStatusTone, statusList } from "@/lib/tokens";
import type { SubTask, TaskStatus } from "@/types/todo";

interface SubtaskRowProps {
  subtask: SubTask;
  onStatusChange: (status: TaskStatus) => void;
}

export function SubtaskRow({ subtask, onStatusChange }: SubtaskRowProps) {
  const rootRef = useRef<HTMLSpanElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState<{ left: number; top: number } | null>(null);
  const tone = getStatusTone(subtask.status);
  const menuWidth = 116;
  const menuHeight = statusList.length * 32 + 8;
  const menuGap = 6;

  useLayoutEffect(() => {
    if (!open) {
      setMenuPosition(null);
      return undefined;
    }

    const updatePosition = () => {
      const trigger = rootRef.current;
      if (!trigger) return;

      const rect = trigger.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const edgePadding = 8;
      const availableBelow = viewportHeight - rect.bottom;
      const shouldOpenDown = availableBelow >= menuHeight + menuGap + edgePadding;
      const rawTop = shouldOpenDown ? rect.bottom + menuGap : rect.top - menuHeight - menuGap;
      const rawLeft = rect.right - menuWidth;

      setMenuPosition({
        left: Math.min(Math.max(edgePadding, rawLeft), viewportWidth - menuWidth - edgePadding),
        top: Math.min(Math.max(edgePadding, rawTop), viewportHeight - menuHeight - edgePadding)
      });
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [menuHeight, open]);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (rootRef.current?.contains(target) || menuRef.current?.contains(target)) return;
      setOpen(false);
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

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
      <span ref={rootRef} className="relative block h-7">
        <button
          type="button"
          className={`flex h-7 w-full items-center justify-between gap-1 rounded-full px-3 text-[11px] font-semibold leading-none outline-none transition hover:brightness-95 focus-visible:shadow-focus ${tone.badge}`}
          title="设置子任务状态"
          aria-label="设置子任务状态"
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="truncate">{subtask.status}</span>
          <span className="text-[10px] leading-none" aria-hidden="true">
            ▾
          </span>
        </button>
        {open && menuPosition
          ? createPortal(
              <div
                ref={menuRef}
                className="fixed z-[300] rounded-default border border-line bg-dropdown p-1 text-ink shadow-dropdown"
                style={{ left: menuPosition.left, top: menuPosition.top, width: menuWidth }}
                role="listbox"
                aria-label="子任务状态选项"
              >
                {statusList.map((status) => {
                  const itemTone = getStatusTone(status);
                  return (
                    <button
                      key={status}
                      type="button"
                      className={`flex h-8 w-full items-center rounded-[6px] px-2 text-left text-[12px] font-semibold transition ${
                        status === subtask.status ? itemTone.badge : "text-muted hover:bg-surface-soft"
                      }`}
                      role="option"
                      aria-selected={status === subtask.status}
                      onClick={() => {
                        onStatusChange(status);
                        setOpen(false);
                      }}
                    >
                      {status}
                    </button>
                  );
                })}
              </div>,
              document.body
            )
          : null}
      </span>
    </div>
  );
}
