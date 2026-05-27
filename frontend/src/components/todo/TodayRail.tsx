import { useMemo } from "react";

import { formatMonthDay, getMonthKey } from "@/lib/date";
import { MetricCard } from "@/components/todo/MetricCard";
import { StatusFilterTabs } from "@/components/todo/StatusFilterTabs";
import { TaskCard } from "@/components/todo/TaskCard";
import type { StatusFilter, Task } from "@/types/todo";

interface TodayRailProps {
  tasks: Task[];
  selectedDayTasks: Task[];
  selectedDate: string;
  selectedTaskId: string | null;
  visibleYear: number;
  visibleMonth: number;
  filter: StatusFilter;
  onFilterChange: (filter: StatusFilter) => void;
  onSelectTask: (task: Task) => void;
}

export function TodayRail({
  tasks,
  selectedDayTasks,
  selectedDate,
  selectedTaskId,
  visibleYear,
  visibleMonth,
  filter,
  onFilterChange,
  onSelectTask
}: TodayRailProps) {
  const monthKey = useMemo(() => getMonthKey(visibleYear, visibleMonth), [visibleMonth, visibleYear]);
  const monthTasks = useMemo(
    () => tasks.filter((task) => task.start_date.startsWith(monthKey) || task.end_date.startsWith(monthKey)),
    [monthKey, tasks]
  );
  const filteredTasks = useMemo(
    () => selectedDayTasks.filter((task) => filter === "all" || task.status === filter),
    [filter, selectedDayTasks]
  );

  const metrics = useMemo(() => {
    let pending = 0;
    let inProgress = 0;
    let completed = 0;
    let cancelled = 0;

    for (const task of selectedDayTasks) {
      switch (task.status) {
        case "未启动":
          pending += 1;
          break;
        case "完成中":
          inProgress += 1;
          break;
        case "已完成":
          completed += 1;
          break;
        case "已取消":
          cancelled += 1;
          break;
      }
    }

    return [
      ["当月任务", monthTasks.length],
      ["当日安排", selectedDayTasks.length],
      ["未启动", pending],
      ["完成中", inProgress],
      ["已完成", completed],
      ["已取消", cancelled]
    ] as const;
  }, [monthTasks.length, selectedDayTasks]);

  return (
    <aside className="tm-panel h-full min-h-0" data-figma-node="Left rail / 今日节奏">
      <header className="border-b border-line px-[14px] py-3">
        <h2 className="font-display text-[16px] font-bold text-ink">今日节奏</h2>
        <p className="mt-1 text-[12px] text-muted">{selectedDate}</p>
      </header>
      <section className="min-h-0 flex-1 overflow-auto" aria-label="今日节奏内容">
        <section className="grid grid-cols-2 gap-2 p-3" aria-label="任务概览">
          {metrics.map(([label, value]) => (
            <MetricCard key={label} label={label} value={value} />
          ))}
        </section>
        <div className="px-3">
          <StatusFilterTabs value={filter} onChange={onFilterChange} />
        </div>
        <section className="px-3 pb-3 pt-4">
          <h3 className="text-[13px] font-semibold text-muted">{formatMonthDay(selectedDate)}</h3>
          <div className="mt-3 space-y-3 pr-1">
            {filteredTasks.length ? (
              filteredTasks.map((task) => (
                <TaskCard key={task.id} task={task} selected={task.id === selectedTaskId} onSelect={onSelectTask} />
              ))
            ) : (
              <div className="rounded-default border border-line bg-surface-soft p-4 text-[13px] text-muted">
                这一天还没有任务。
              </div>
            )}
          </div>
        </section>
      </section>
    </aside>
  );
}
