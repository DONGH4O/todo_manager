"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

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
  // Older frozen shells may inject before documentElement exists. Apply the
  // desktop rendering policy before React's first paint as a compatibility fallback.
  useLayoutEffect(() => {
    if (window.todoDesktopShell || new URLSearchParams(window.location.search).get("desktop") === "1") {
      document.documentElement.dataset.desktopShell = "true";
    }
  }, []);

  const [today, setToday] = useState(todayIso);
  useEffect(() => {
    const checkDate = () => setToday(todayIso());
    const timer = window.setInterval(checkDate, 30_000);
    window.addEventListener("focus", checkDate);
    document.addEventListener("visibilitychange", checkDate);
    checkDate();
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", checkDate);
      document.removeEventListener("visibilitychange", checkDate);
    };
  }, []);
  const initialYear = Number(today.slice(0, 4));
  const initialMonth = Number(today.slice(5, 7)) - 1;
  const searchInputRef = useRef<HTMLInputElement>(null);
  const toastTimerRef = useRef<number | null>(null);
  const selectedTaskIdRef = useRef<string | null>(null);
  const selectedDateRef = useRef(today);
  const filterRef = useRef<StatusFilter>("all");
  const selectionSequence = useRef(0);
  const refreshSequence = useRef(0);
  const dateRequest = useRef(0);
  const latestByDate = useRef(new Map<string, { request: number; tasks: Task[] }>());

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
  const visibleDatesRef = useRef(visibleDateKeys);
  useLayoutEffect(() => {
    visibleDatesRef.current = visibleDateKeys;
  }, [visibleDateKeys]);
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

  const selectTask = useCallback((task: Task | null) => {
    ++selectionSequence.current;
    selectedTaskIdRef.current = task?.id ?? null;
    setSelectedTaskId(selectedTaskIdRef.current);
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
    const request = ++dateRequest.current;
    const dateTasks = await todoData.listTasksForDates(dates);
    const fresh: TasksByDate = {};
    for (const [date, items] of Object.entries(dateTasks)) {
      if (request >= (latestByDate.current.get(date)?.request ?? 0)) {
        latestByDate.current.set(date, { request, tasks: items });
        fresh[date] = items;
      }
    }
    setTasksByDate((previous) => ({ ...previous, ...fresh }));
    return dateTasks;
  }, []);

  const selectFromDay = useCallback((dayTasks: Task[], preferredId: string | null, preserveDraft = false) => {
    const visible = dayTasks.filter((task) => filterRef.current === "all" || task.status === filterRef.current);
    const next = visible.find((task) => task.id === preferredId) ?? visible[0] ?? null;
    if (preserveDraft && next && next.id === selectedTaskIdRef.current) return;
    selectTask(next);
  }, [selectTask]);

  const refreshTasks = useCallback(
    async (reason: "load" | "manual" | "save" | "status" = "load") => {
      const request = ++refreshSequence.current;
      const selection = ++selectionSequence.current;
      const date = selectedDateRef.current;
      try {
        const [loadedTasks] = await Promise.all([todoData.listTasks(), loadDateTasks(visibleDatesRef.current)]);
        if (request !== refreshSequence.current) return;
        setTasks(loadedTasks);
        if (selectionSequence.current === selection && selectedDateRef.current === date) {
          selectFromDay(latestByDate.current.get(date)?.tasks ?? [], selectedTaskIdRef.current);
        }
        if (reason === "manual") showToast("数据已刷新");
        if (reason === "save") showToast("修改已保存");
      } catch (error) {
        if (request !== refreshSequence.current) return;
        const message = dataErrorMessage(error, "数据读取失败");
        showToast(reason === "save" || reason === "status" ? `已保存，界面刷新失败：${message}` : message);
      }
    },
    [loadDateTasks, selectFromDay, showToast]
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
    const selection = ++selectionSequence.current;
    setSelectedDate(date);
    selectedDateRef.current = date;
    try {
      await loadDateTasks([date]);
      if (selection === selectionSequence.current && selectedDateRef.current === date) {
        selectFromDay(latestByDate.current.get(date)?.tasks ?? [], null);
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

  const handleToday = () => {
    const date = todayIso();
    setToday(date);
    setVisibleFromDate(date);
    return handleSelectDate(date);
  };

  const handleFilterChange = (next: StatusFilter) => {
    filterRef.current = next;
    setFilter(next);
    selectFromDay(selectedDayTasks, selectedTaskIdRef.current, true);
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
      setTasks((current) => current.map((task) => task.id === selectedTask.id
        ? { ...task, subtasks: [...task.subtasks, createdSubtask] }
        : task));
      if (selectedTaskIdRef.current === selectedTask.id) {
        setDetailDraft((draft) => draft && { ...draft, subtasks: [...draft.subtasks, createdSubtask] });
      }
      markDataChanged();
      setCreateSubtaskOpen(false);
    } catch (error) {
      showToast(dataErrorMessage(error, "子任务创建失败"));
    }
  };

  const handleTaskStatusChange = async (status: TaskStatus) => {
    if (!selectedTask) return;

    try {
      const saved = await todoData.updateTask(selectedTask.id, { status });
      setTasks((current) => current.map((task) => task.id === saved.id ? saved : task));
      await refreshTasks("status");
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
      const statuses: Record<string, TaskStatus> = {};
      for (const child of detailDraft.subtasks) {
        const original = selectedTask.subtasks.find((item) => item.id === child.id);
        if (original && original.status !== child.status) statuses[child.id] = child.status;
      }
      const saved = await todoData.updateTask(selectedTask.id, taskUpdate, statuses);
      setTasks((current) => current.map((task) => task.id === saved.id ? saved : task));
      await refreshTasks("save");
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
          onRefresh={() => void refreshTasks("manual")}
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
            onFilterChange={handleFilterChange}
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
