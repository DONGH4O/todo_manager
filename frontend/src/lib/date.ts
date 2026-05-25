import type { CalendarDay, Task } from "@/types/todo";

export function formatMonthDay(date: string): string {
  const [, month, day] = date.split("-");
  return `${Number(month)}月${Number(day)}日`;
}

export function formatDateRange(task: Pick<Task, "start_date" | "end_date">): string {
  return `${task.start_date} - ${task.end_date}`;
}

export function toYmd(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function parseYmd(value: string): Date | undefined {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return undefined;

  const [, year, month, day] = match.map(Number);
  const parsed = new Date(year, month - 1, day);
  return toYmd(parsed) === value ? parsed : undefined;
}

export function normalizeDateRange(start: string, end: string, fallback: string): [string, string] {
  const cleanStart = start || fallback;
  const cleanEnd = !end || end < cleanStart ? cleanStart : end;
  return [cleanStart, cleanEnd];
}

export function getMonthKey(year: number, month: number): string {
  return `${year}-${`${month + 1}`.padStart(2, "0")}`;
}

function getCalendarBounds(year: number, month: number): [Date, Date] {
  const first = new Date(year, month, 1);
  const mondayIndex = (first.getDay() + 6) % 7;
  const start = new Date(year, month, 1 - mondayIndex);
  const last = new Date(year, month + 1, 0);
  const sundayIndex = (last.getDay() + 6) % 7;
  const end = new Date(year, month, last.getDate() + (6 - sundayIndex));
  return [start, end];
}

export function getCalendarDateKeys(year: number, month: number): string[] {
  const [start, end] = getCalendarBounds(year, month);
  const keys: string[] = [];

  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    keys.push(toYmd(date));
  }

  return keys;
}

export function getVisibleDateKeys(year: number, month: number, selectedDate: string, today: string): string[] {
  return Array.from(new Set([...getCalendarDateKeys(year, month), selectedDate, today]));
}

export function buildCalendarDays(
  year: number,
  month: number,
  tasksByDate: Record<string, Task[]>,
  selectedDate: string,
  today: string
): CalendarDay[] {
  const days: CalendarDay[] = [];

  for (const key of getCalendarDateKeys(year, month)) {
    const parsed = parseYmd(key);

    days.push({
      key,
      dayNumber: parsed?.getDate() || Number(key.slice(8, 10)),
      isOutsideMonth: parsed ? parsed.getMonth() !== month : false,
      isToday: key === today,
      isSelected: key === selectedDate,
      tasks: tasksByDate[key] || []
    });
  }

  return days;
}
