import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { getStatusTone, statusList } from "@/lib/tokens";
import type { TaskStatus } from "@/types/todo";

interface StatusDropdownProps {
  value: TaskStatus;
  onChange: (status: TaskStatus) => void;
  ariaLabel: string;
  variant?: "field" | "pill";
  className?: string;
  buttonClassName?: string;
  align?: "left" | "right";
  menuMinWidth?: number;
}

export function StatusDropdown({
  value,
  onChange,
  ariaLabel,
  variant = "field",
  className = "",
  buttonClassName = "",
  align = "left",
  menuMinWidth = 132
}: StatusDropdownProps) {
  const rootRef = useRef<HTMLSpanElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState<{ left: number; top: number; width: number } | null>(null);
  const tone = getStatusTone(value);
  const menuHeight = statusList.length * 32 + 8;
  const menuGap = 6;
  const buttonClasses =
    variant === "pill"
      ? `tm-desktop-paint-lite flex h-7 w-full items-center justify-between gap-1 rounded-full px-3 text-[11px] font-semibold leading-none outline-none transition hover:brightness-95 focus-visible:shadow-focus ${tone.badge}`
      : "tm-desktop-paint-lite tm-select flex h-[38px] w-full min-w-0 items-center justify-between gap-2";

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
      const menuWidth = Math.max(menuMinWidth, Math.round(rect.width));
      const availableBelow = viewportHeight - rect.bottom;
      const shouldOpenDown = availableBelow >= menuHeight + menuGap + edgePadding;
      const rawTop = shouldOpenDown ? rect.bottom + menuGap : rect.top - menuHeight - menuGap;
      const rawLeft = align === "right" ? rect.right - menuWidth : rect.left;

      setMenuPosition({
        left: Math.min(Math.max(edgePadding, rawLeft), viewportWidth - menuWidth - edgePadding),
        top: Math.min(Math.max(edgePadding, rawTop), viewportHeight - menuHeight - edgePadding),
        width: menuWidth
      });
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [align, menuHeight, menuMinWidth, open]);

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
    <span ref={rootRef} className={`relative block min-w-0 ${className}`}>
      <button
        type="button"
        className={`${buttonClasses} ${buttonClassName}`}
        title={ariaLabel}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="truncate">{value}</span>
        <span className={variant === "pill" ? "text-[10px] leading-none" : "text-[12px] text-muted"} aria-hidden="true">
          ▾
        </span>
      </button>
      {open && menuPosition
        ? createPortal(
            <div
              ref={menuRef}
              className="fixed z-[300] rounded-default border border-line bg-dropdown p-1 text-ink shadow-dropdown"
              style={{ left: menuPosition.left, top: menuPosition.top, width: menuPosition.width }}
              role="listbox"
              aria-label={ariaLabel}
            >
              {statusList.map((status) => {
                const itemTone = getStatusTone(status);
                return (
                  <button
                    key={status}
                    type="button"
                    className={`tm-desktop-paint-lite flex h-8 w-full items-center rounded-[6px] px-2 text-left text-[12px] font-semibold transition ${
                      status === value ? itemTone.badge : "text-muted hover:bg-surface-soft"
                    }`}
                    role="option"
                    aria-selected={status === value}
                    onClick={() => {
                      onChange(status);
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
  );
}
