import type { CalendarDay, Task, TaskStatus } from "@/types/todo";

const ongoingDisplayStatuses: TaskStatus[] = ["未启动", "完成中"];

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

export function dateInRange(date: string, item: Pick<Task, "start_date" | "end_date">): boolean {
  return date >= item.start_date && date <= item.end_date;
}

export function shouldShowTaskOnDate(date: string, item: Pick<Task, "start_date" | "end_date" | "status">): boolean {
  return dateInRange(date, item) || (date >= item.start_date && ongoingDisplayStatuses.includes(item.status));
}

export function normalizeDateRange(start: string, end: string, fallback: string): [string, string] {
  const cleanStart = start || fallback;
  const cleanEnd = !end || end < cleanStart ? cleanStart : end;
  return [cleanStart, cleanEnd];
}

export function getMonthKey(year: number, month: number): string {
  return `${year}-${`${month + 1}`.padStart(2, "0")}`;
}

export function buildCalendarDays(
  year: number,
  month: number,
  tasks: Task[],
  selectedDate: string,
  today: string
): CalendarDay[] {
  const first = new Date(year, month, 1);
  const mondayIndex = (first.getDay() + 6) % 7;
  const start = new Date(year, month, 1 - mondayIndex);
  const last = new Date(year, month + 1, 0);
  const sundayIndex = (last.getDay() + 6) % 7;
  const end = new Date(year, month, last.getDate() + (6 - sundayIndex));
  const days: CalendarDay[] = [];

  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    const key = toYmd(date);

    days.push({
      key,
      dayNumber: date.getDate(),
      isOutsideMonth: date.getMonth() !== month,
      isToday: key === today,
      isSelected: key === selectedDate,
      tasks: tasks.filter((task) => shouldShowTaskOnDate(key, task))
    });
  }

  return days;
}
