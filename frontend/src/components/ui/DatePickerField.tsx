import { useEffect, useMemo, useRef, useState } from "react";
import { DayPicker } from "react-day-picker";
import { zhCN } from "react-day-picker/locale";

import { parseYmd, toYmd } from "@/lib/date";

interface DatePickerFieldProps {
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  align?: "left" | "right";
}

export function DatePickerField({ value, onChange, ariaLabel, align = "left" }: DatePickerFieldProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const selectedDate = useMemo(() => parseYmd(value), [value]);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current || rootRef.current.contains(event.target as Node)) return;
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
    <div ref={rootRef} className="relative min-w-0">
      <button
        type="button"
        className="tm-input flex h-[38px] w-full min-w-0 items-center justify-between gap-2"
        aria-label={ariaLabel}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="truncate">{value || "选择日期"}</span>
        <span aria-hidden="true" className="text-[12px] text-muted">
          ▾
        </span>
      </button>
      {open ? (
        <div
          className={`tm-date-popover absolute top-[calc(100%+6px)] z-[160] w-[292px] max-w-[calc(100vw-48px)] rounded-default border border-line bg-dropdown p-2 text-ink shadow-dropdown ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          <DayPicker
            mode="single"
            selected={selectedDate}
            defaultMonth={selectedDate}
            locale={zhCN}
            weekStartsOn={1}
            showOutsideDays
            fixedWeeks
            onSelect={(date) => {
              if (!date) return;
              onChange(toYmd(date));
              setOpen(false);
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
