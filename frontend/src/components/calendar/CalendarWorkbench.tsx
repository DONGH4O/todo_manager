import { buildCalendarDays, shouldShowTaskOnDate } from "@/lib/date";
import { CalendarDayCell } from "@/components/calendar/CalendarDayCell";
import type { Task } from "@/types/todo";

interface CalendarWorkbenchProps {
  tasks: Task[];
  selectedDate: string;
  today: string;
  visibleYear: number;
  visibleMonth: number;
  onSelectDate: (date: string) => void;
  onPreviousMonth: () => void;
  onNextMonth: () => void;
  onYearChange: (year: number) => void;
  onMonthChange: (month: number) => void;
}

const weekdays = ["一", "二", "三", "四", "五", "六", "日"];
const years = Array.from({ length: 201 }, (_, index) => 1900 + index);
const months = Array.from({ length: 12 }, (_, index) => index);

export function CalendarWorkbench({
  tasks,
  selectedDate,
  today,
  visibleYear,
  visibleMonth,
  onSelectDate,
  onPreviousMonth,
  onNextMonth,
  onYearChange,
  onMonthChange
}: CalendarWorkbenchProps) {
  const days = buildCalendarDays(visibleYear, visibleMonth, tasks, selectedDate, today);
  const weekCount = Math.ceil(days.length / 7);
  const selectedDateTaskCount = tasks.filter((task) => shouldShowTaskOnDate(selectedDate, task)).length;
  const calendarGridStyle = {
    gridTemplateRows: `repeat(${weekCount}, minmax(96px, 1fr))`,
    minHeight: `${weekCount * 96 + (weekCount - 1) * 8}px`
  };

  return (
    <section className="tm-panel h-full min-h-0" data-figma-node="Center / 月历工作台">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-[14px] py-3">
        <div>
          <h2 className="font-display text-[16px] font-bold text-ink">月历工作台</h2>
          <p className="mt-1 text-[12px] text-muted">
            {selectedDate} · {selectedDateTaskCount} 个任务
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className="tm-icon-button" onClick={onPreviousMonth} title="上个月" aria-label="上个月">
            ‹
          </button>
          <select
            className="tm-select h-[38px] w-[92px]"
            value={visibleYear}
            onChange={(event) => onYearChange(Number(event.target.value))}
            title="选择年份"
            aria-label="选择年份"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}年
              </option>
            ))}
          </select>
          <select
            className="tm-select h-[38px] w-[66px]"
            value={visibleMonth}
            onChange={(event) => onMonthChange(Number(event.target.value))}
            title="选择月份"
            aria-label="选择月份"
          >
            {months.map((month) => (
              <option key={month} value={month}>
                {month + 1}月
              </option>
            ))}
          </select>
          <button type="button" className="tm-icon-button" onClick={onNextMonth} title="下个月" aria-label="下个月">
            ›
          </button>
        </div>
      </header>
      <section className="flex min-h-0 flex-1 flex-col overflow-auto p-3">
        <div className="grid grid-cols-7 gap-2 px-1 pb-2 text-center text-[12px] font-bold text-muted" aria-hidden="true">
          {weekdays.map((weekday) => (
            <span key={weekday}>{weekday}</span>
          ))}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-7 gap-2" style={calendarGridStyle}>
          {days.map((day) => (
            <CalendarDayCell key={day.key} day={day} onSelect={onSelectDate} />
          ))}
        </div>
      </section>
    </section>
  );
}
