export type TaskStatus = "未启动" | "完成中" | "已完成" | "已取消";

export type StatusFilter = TaskStatus | "all";

export type ThemeMode = "system" | "light" | "dark";

export interface SubTask {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  status: TaskStatus;
  background: string;
}

export interface Task {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  status: TaskStatus;
  background: string;
  subtasks: SubTask[];
}

export interface DetailDraft {
  title: string;
  start_date: string;
  end_date: string;
  background: string;
  subtasks: SubTask[];
}

export interface CalendarDay {
  key: string;
  dayNumber: number;
  isOutsideMonth: boolean;
  isToday: boolean;
  isSelected: boolean;
  tasks: Task[];
}
