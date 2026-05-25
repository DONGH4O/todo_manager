"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { CalendarWorkbench } from "@/components/calendar/CalendarWorkbench";
import { TopNav } from "@/components/layout/TopNav";
import { CreateSubtaskModal } from "@/components/todo/CreateSubtaskModal";
import { CreateTaskModal } from "@/components/todo/CreateTaskModal";
import { DeleteConfirmModal } from "@/components/todo/DeleteConfirmModal";
import { TaskDetailPanel } from "@/components/todo/TaskDetailPanel";
import { TodayRail } from "@/components/todo/TodayRail";
import { UndoToast } from "@/components/ui/UndoToast";
import { getVisibleDateKeys, normalizeDateRange } from "@/lib/date";
import { TodoDataError, todayIso, todoData, type TasksByDate } from "@/lib/todo-data";
import type { DetailDraft, StatusFilter, SubTask, Task, TaskStatus, ThemeMode } from "@/types/todo";

function createDraft(task: Task | null): DetailDraft | null {
  if (!task) return null;

  return {
    title: task.title,
    start_date: task.start_date,
    end_date: task.end_date,
    background: task.background,
    subtasks: task.subtasks.map((subtask) => ({ ...subtask }))
  };
}

function taskMatchesQuery(task: Task, query: string): boolean {
  const text = [
    task.title,
    task.background,
    task.status,
    task.start_date,
    task.end_date,
    task.subtasks.map((subtask) => `${subtask.title} ${subtask.status} ${subtask.start_date} ${subtask.end_date}`).join(" ")
  ]
    .join(" ")
    .toLowerCase();

  return !query || text.includes(query);
}

function dataErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof TodoDataError) return error.message;
  return fallback;
}

export function TodoManagerApp() {
  const today = useMemo(() => todayIso(), []);
  const initialYear = Number(today.slice(0, 4));
  const initialMonth = Number(today.slice(5, 7)) - 1;
  const searchInputRef = useRef<HTMLInputElement>(null);
  const toastTimerRef = useRef<number | null>(null);
  const selectedTaskIdRef = useRef<string | null>(null);
  const selectedDateRef = useRef(today);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksByDate, setTasksByDate] = useState<TasksByDate>({});
  const [dataVersion, setDataVersion] = useState(0);
  const [visibleYear, setVisibleYear] = useState(initialYear);
  const [visibleMonth, setVisibleMonth] = useState(initialMonth);
  const [selectedDate, setSelectedDate] = useState(today);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [detailDraft, setDetailDraft] = useState<DetailDraft | null>(null);
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [themeMode, setThemeMode] = useState<ThemeMode>("system");
  const [systemPrefersDark, setSystemPrefersDark] = useState(false);
  const [createTaskOpen, setCreateTaskOpen] = useState(false);
  const [createSubtaskOpen, setCreateSubtaskOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletedTask, setDeletedTask] = useState<Task | null>(null);
  const [toast, setToast] = useState<{ message: string; canUndo: boolean } | null>(null);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) || null,
    [selectedTaskId, tasks]
  );
  const visibleDateKeys = useMemo(
    () => getVisibleDateKeys(visibleYear, visibleMonth, selectedDate, today),
    [visibleYear, visibleMonth, selectedDate, today]
  );
  const selectedDayTasks = tasksByDate[selectedDate] || [];

  useEffect(() => {
    selectedTaskIdRef.current = selectedTaskId;
  }, [selectedTaskId]);

  useEffect(() => {
    selectedDateRef.current = selectedDate;
  }, [selectedDate]);

  const searchResults = useMemo(() => {
    if (!searchOpen) return [];

    const normalizedQuery = query.trim().toLowerCase();
    return tasks.filter((task) => taskMatchesQuery(task, normalizedQuery));
  }, [query, searchOpen, tasks]);

  const resolvedTheme = themeMode === "system" ? (systemPrefersDark ? "dark" : "light") : themeMode;

  useEffect(() => {
    const stored = window.localStorage.getItem("todo-manager-theme") as ThemeMode | null;
    if (stored === "system" || stored === "light" || stored === "dark") {
      setThemeMode(stored);
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    setSystemPrefersDark(media.matches);

    const handleChange = (event: MediaQueryListEvent) => setSystemPrefersDark(event.matches);
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.themeMode = themeMode;
    document.documentElement.dataset.theme = resolvedTheme;
  }, [resolvedTheme, themeMode]);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    };
  }, []);

  const showToast = useCallback((message: string, canUndo = false) => {
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    setToast({ message, canUndo });
    toastTimerRef.current = window.setTimeout(() => {
      setToast(null);
      if (canUndo) setDeletedTask(null);
    }, 5000);
  }, []);

  const selectTask = useCallback((task: Task) => {
    setSelectedTaskId(task.id);
    setDetailDraft(createDraft(task));
  }, []);

  const setVisibleFromDate = useCallback((date: string) => {
    const [year, month] = date.split("-").map(Number);
    setVisibleYear(year);
    setVisibleMonth(month - 1);
  }, []);

  const markDataChanged = useCallback(() => {
    setDataVersion((version) => version + 1);
  }, []);

  const loadDateTasks = useCallback(async (dates: string[]) => {
    const dateTasks = await todoData.listTasksForDates(dates);
    setTasksByDate((currentTasksByDate) => ({ ...currentTasksByDate, ...dateTasks }));
    return dateTasks;
  }, []);

  const replaceTask = useCallback((updatedTask: Task) => {
    setTasks((currentTasks) => currentTasks.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
    setDetailDraft(createDraft(updatedTask));
  }, []);

  const refreshTasks = useCallback(
    async (showSuccess = false, preferredTaskId?: string | null) => {
      try {
        const loadedTasks = await todoData.listTasks();
        const fallbackDate = selectedDateRef.current;
        const fallbackDateTasks = await loadDateTasks([fallbackDate]);
        const displayedTasks = fallbackDateTasks[fallbackDate] || [];
        const currentTaskId = preferredTaskId ?? selectedTaskIdRef.current;
        const taskToSelect =
          (currentTaskId ? loadedTasks.find((task) => task.id === currentTaskId) : null) ||
          displayedTasks[0] ||
          null;

        setTasks(loadedTasks);
        setSelectedTaskId(taskToSelect?.id || null);
        setDetailDraft(createDraft(taskToSelect));
        if (taskToSelect && !displayedTasks.some((task) => task.id === taskToSelect.id)) {
          setSelectedDate(taskToSelect.start_date);
          setVisibleFromDate(taskToSelect.start_date);
        }
        if (showSuccess) showToast("数据已刷新");
      } catch (error) {
        showToast(dataErrorMessage(error, "数据读取失败"));
      }
    },
    [loadDateTasks, setVisibleFromDate, showToast]
  );

  useEffect(() => {
    void refreshTasks();
  }, [refreshTasks]);

  useEffect(() => {
    void loadDateTasks(visibleDateKeys).catch((error) => {
      showToast(dataErrorMessage(error, "日历数据读取失败"));
    });
  }, [dataVersion, loadDateTasks, showToast, visibleDateKeys]);

  const closeSearch = useCallback(() => setSearchOpen(false), []);

  const openTaskModal = useCallback(() => setCreateTaskOpen(true), []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName.toLowerCase();
      const typing = tag === "input" || tag === "textarea" || tag === "select" || Boolean(target?.isContentEditable);

      if (event.key === "Escape") {
        setCreateTaskOpen(false);
        setCreateSubtaskOpen(false);
        setDeleteOpen(false);
        setSearchOpen(false);
      }

      if (event.key === "/" && !typing) {
        event.preventDefault();
        setSearchOpen(true);
        searchInputRef.current?.focus();
      }

      if ((event.key === "n" || event.key === "N") && !typing) {
        openTaskModal();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [openTaskModal]);

  const handleThemeModeChange = (mode: ThemeMode) => {
    setThemeMode(mode);
    window.localStorage.setItem("todo-manager-theme", mode);
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setSearchOpen(Boolean(value.trim()));
  };

  const handleSelectSearchResult = (task: Task) => {
    setVisibleFromDate(task.start_date);
    selectedDateRef.current = task.start_date;
    setSelectedDate(task.start_date);
    selectTask(task);
    setSearchOpen(false);
  };

  const handleSelectDate = async (date: string) => {
    setSelectedDate(date);
    selectedDateRef.current = date;
    try {
      const dateTasks = await loadDateTasks([date]);
      const firstTask = dateTasks[date]?.[0] || null;
      if (firstTask) {
        selectTask(firstTask);
      } else {
        setSelectedTaskId(null);
        setDetailDraft(null);
      }
    } catch (error) {
      showToast(dataErrorMessage(error, "日历数据读取失败"));
    }
  };

  const handlePreviousMonth = () => {
    if (visibleMonth === 0) {
      setVisibleMonth(11);
      setVisibleYear((year) => year - 1);
      return;
    }
    setVisibleMonth((month) => month - 1);
  };

  const handleNextMonth = () => {
    if (visibleMonth === 11) {
      setVisibleMonth(0);
      setVisibleYear((year) => year + 1);
      return;
    }
    setVisibleMonth((month) => month + 1);
  };

  const handleToday = async () => {
    setVisibleFromDate(today);
    setSelectedDate(today);
    selectedDateRef.current = today;
    try {
      const dateTasks = await loadDateTasks([today]);
      const firstTask = dateTasks[today]?.[0] || null;
      if (firstTask) {
        selectTask(firstTask);
      } else {
        setSelectedTaskId(null);
        setDetailDraft(null);
      }
    } catch (error) {
      showToast(dataErrorMessage(error, "今日数据读取失败"));
    }
  };

  const handleCreateTask = async (task: Task) => {
    try {
      const createdTask = await todoData.createTask({
        title: task.title,
        start_date: task.start_date,
        end_date: task.end_date,
        status: task.status,
        background: task.background
      });
      setTasks((currentTasks) => [...currentTasks, createdTask]);
      selectedDateRef.current = createdTask.start_date;
      setSelectedDate(createdTask.start_date);
      setVisibleFromDate(createdTask.start_date);
      selectTask(createdTask);
      markDataChanged();
      setCreateTaskOpen(false);
    } catch (error) {
      showToast(dataErrorMessage(error, "任务创建失败"));
    }
  };

  const handleCreateSubtask = async (subtask: SubTask) => {
    if (!selectedTask || !detailDraft) return;

    try {
      const createdSubtask = await todoData.createSubtask(selectedTask.id, {
        title: subtask.title,
        start_date: subtask.start_date,
        end_date: subtask.end_date,
        status: subtask.status,
        background: subtask.background
      });
      const nextDraft = {
        ...detailDraft,
        subtasks: [...detailDraft.subtasks, createdSubtask]
      };
      const updatedTask = {
        ...selectedTask,
        subtasks: nextDraft.subtasks
      };

      setTasks((currentTasks) => currentTasks.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
      setDetailDraft(nextDraft);
      markDataChanged();
      setCreateSubtaskOpen(false);
    } catch (error) {
      showToast(dataErrorMessage(error, "子任务创建失败"));
    }
  };

  const handleTaskStatusChange = async (status: TaskStatus) => {
    if (!selectedTask) return;

    try {
      const updatedTask = await todoData.updateTask(selectedTask.id, { status });
      replaceTask(updatedTask);
      markDataChanged();
    } catch (error) {
      showToast(dataErrorMessage(error, "状态更新失败"));
    }
  };

  const handleSubtaskDraftStatusChange = (index: number, status: TaskStatus) => {
    if (!detailDraft) return;
    setDetailDraft({
      ...detailDraft,
      subtasks: detailDraft.subtasks.map((subtask, currentIndex) =>
        currentIndex === index ? { ...subtask, status } : subtask
      )
    });
  };

  const handleSave = async () => {
    if (!selectedTask || !detailDraft) return;

    const [startDate, endDate] = normalizeDateRange(detailDraft.start_date, detailDraft.end_date, selectedDate);
    const taskUpdate = {
      title: detailDraft.title.trim() || selectedTask.title,
      start_date: startDate,
      end_date: endDate,
      background: detailDraft.background.trim()
    };

    try {
      let updatedTask = await todoData.updateTask(selectedTask.id, taskUpdate);

      for (const subtask of detailDraft.subtasks) {
        const original = selectedTask.subtasks.find((item) => item.id === subtask.id);
        if (!original || original.status === subtask.status) continue;
        const updatedSubtask = await todoData.updateSubtask(selectedTask.id, subtask.id, { status: subtask.status });
        updatedTask = {
          ...updatedTask,
          subtasks: updatedTask.subtasks.map((item) => (item.id === updatedSubtask.id ? updatedSubtask : item))
        };
      }

      replaceTask(updatedTask);
      selectedDateRef.current = startDate;
      setSelectedDate(startDate);
      setVisibleFromDate(startDate);
      markDataChanged();
      showToast("修改已保存");
    } catch (error) {
      showToast(dataErrorMessage(error, "修改保存失败"));
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedTask) return;

    try {
      const deleted = await todoData.deleteTask(selectedTask.id);
      const remainingTasks = tasks.filter((task) => task.id !== selectedTask.id);
      const todayTasks = await loadDateTasks([today]);
      const fallback = todayTasks[today]?.[0] || null;
      selectedDateRef.current = today;
      selectedTaskIdRef.current = fallback?.id || null;
      setDeletedTask(deleted);
      setTasks(remainingTasks);
      setSelectedTaskId(fallback?.id || null);
      setDetailDraft(createDraft(fallback));
      setSelectedDate(today);
      setVisibleFromDate(today);
      markDataChanged();
      setDeleteOpen(false);
      showToast("任务已删除", true);
    } catch (error) {
      showToast(dataErrorMessage(error, "任务删除失败"));
    }
  };

  const handleUndoDelete = async () => {
    if (!deletedTask) return;

    try {
      const restoredTask = await todoData.undoTask(deletedTask);
      if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
      setTasks((currentTasks) => [...currentTasks, restoredTask]);
      selectedDateRef.current = restoredTask.start_date;
      setSelectedDate(restoredTask.start_date);
      setVisibleFromDate(restoredTask.start_date);
      selectTask(restoredTask);
      markDataChanged();
      setDeletedTask(null);
      setToast(null);
    } catch (error) {
      showToast(dataErrorMessage(error, "撤销删除失败"));
    }
  };

  return (
    <main className="app-bg h-dvh overflow-hidden p-4 text-ink sm:p-app">
      <div className="mx-auto flex h-full min-h-0 w-full max-w-[1440px] flex-col gap-gutter-lg">
        <TopNav
          query={query}
          searchOpen={searchOpen}
          searchInputRef={searchInputRef}
          results={searchResults}
          onQueryChange={handleQueryChange}
          onSearchFocus={() => setSearchOpen(true)}
          onSearchButton={() => setSearchOpen(true)}
          onCloseSearch={closeSearch}
          onSelectSearchResult={handleSelectSearchResult}
          onToday={handleToday}
          onRefresh={() => void refreshTasks(true)}
          onNewTask={openTaskModal}
          themeMode={themeMode}
          onThemeModeChange={handleThemeModeChange}
        />

        <section className="grid min-h-0 flex-1 grid-cols-1 gap-gutter-lg lg:grid-cols-[260px_minmax(0,1fr)] xl:grid-cols-[260px_minmax(560px,1fr)_342px]">
          <TodayRail
            tasks={tasks}
            selectedDayTasks={selectedDayTasks}
            selectedDate={selectedDate}
            selectedTaskId={selectedTaskId}
            visibleYear={visibleYear}
            visibleMonth={visibleMonth}
            filter={filter}
            onFilterChange={setFilter}
            onSelectTask={selectTask}
          />
          <CalendarWorkbench
            tasksByDate={tasksByDate}
            selectedDate={selectedDate}
            selectedDateTaskCount={selectedDayTasks.length}
            today={today}
            visibleYear={visibleYear}
            visibleMonth={visibleMonth}
            onSelectDate={handleSelectDate}
            onPreviousMonth={handlePreviousMonth}
            onNextMonth={handleNextMonth}
            onYearChange={setVisibleYear}
            onMonthChange={setVisibleMonth}
          />
          <div className="min-h-0 lg:col-span-2 xl:col-span-1">
            <TaskDetailPanel
              task={selectedTask}
              draft={detailDraft}
              onDraftChange={setDetailDraft}
              onTaskStatusChange={handleTaskStatusChange}
              onSubtaskDraftStatusChange={handleSubtaskDraftStatusChange}
              onAddSubtask={() => setCreateSubtaskOpen(true)}
              onSave={handleSave}
              onDelete={() => setDeleteOpen(true)}
            />
          </div>
        </section>
      </div>

      <CreateTaskModal
        open={createTaskOpen}
        selectedDate={selectedDate}
        onCancel={() => setCreateTaskOpen(false)}
        onCreate={handleCreateTask}
      />
      <CreateSubtaskModal
        open={createSubtaskOpen}
        task={selectedTask}
        fallbackDate={selectedDate}
        onCancel={() => setCreateSubtaskOpen(false)}
        onCreate={handleCreateSubtask}
      />
      <DeleteConfirmModal
        open={deleteOpen}
        task={selectedTask}
        onCancel={() => setDeleteOpen(false)}
        onConfirm={handleConfirmDelete}
      />
      <UndoToast message={toast?.message || null} canUndo={Boolean(toast?.canUndo)} onUndo={handleUndoDelete} />
    </main>
  );
}
