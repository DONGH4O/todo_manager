import { initialTasks } from "@/lib/sample-data";
import { normalizeTaskStatus } from "@/lib/tokens";
import type { SubTask, Task, TaskStatus } from "@/types/todo";

export interface TaskInput {
  title: string;
  start_date: string;
  end_date: string;
  status: TaskStatus;
  background: string;
}

export type TaskUpdate = Partial<TaskInput>;
export type SubtaskInput = TaskInput;
export type SubtaskUpdate = Partial<SubtaskInput>;

export interface TodoBridgeRequest {
  action:
    | "listTasks"
    | "createTask"
    | "updateTask"
    | "deleteTask"
    | "undoTask"
    | "createSubtask"
    | "updateSubtask";
  payload?: unknown;
}

export interface TodoBridgeError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export type TodoBridgeResponse<T = unknown> =
  | { ok: true; result: T }
  | { ok: false; error: TodoBridgeError };

declare global {
  interface Window {
    todoBridge?: {
      request: <T = unknown>(request: TodoBridgeRequest) => Promise<TodoBridgeResponse<T>>;
    };
    todoDesktopShell?: boolean;
  }
}

export class TodoDataError extends Error {
  code: string;
  details?: Record<string, unknown>;

  constructor(error: TodoBridgeError) {
    super(error.message);
    this.name = "TodoDataError";
    this.code = error.code;
    this.details = error.details;
  }
}

const PREVIEW_STORAGE_KEY = "todo-manager-preview-tasks";

export function todayIso(): string {
  const today = new Date();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${today.getFullYear()}-${month}-${day}`;
}

function cloneTasks(tasks: Task[]): Task[] {
  return tasks.map((task) => ({
    ...task,
    subtasks: task.subtasks.map((subtask) => ({ ...subtask }))
  }));
}

function normalizeSubtask(raw: Partial<SubTask>): SubTask {
  return {
    id: String(raw.id || ""),
    title: String(raw.title || ""),
    start_date: String(raw.start_date || todayIso()),
    end_date: String(raw.end_date || raw.start_date || todayIso()),
    status: normalizeTaskStatus(raw.status),
    background: String(raw.background || "")
  };
}

function normalizeTask(raw: Partial<Task>): Task {
  return {
    id: String(raw.id || ""),
    title: String(raw.title || ""),
    start_date: String(raw.start_date || todayIso()),
    end_date: String(raw.end_date || raw.start_date || todayIso()),
    status: normalizeTaskStatus(raw.status),
    background: String(raw.background || ""),
    subtasks: (raw.subtasks || []).map((subtask) => normalizeSubtask(subtask)).filter((subtask) => subtask.id)
  };
}

function isDesktopBridgeAvailable(): boolean {
  return typeof window !== "undefined" && typeof window.todoBridge?.request === "function";
}

function isDesktopShellExpected(): boolean {
  if (typeof window === "undefined") return false;
  if (window.todoDesktopShell === true) return true;
  return new URLSearchParams(window.location.search).get("desktop") === "1";
}

function waitForDesktopBridge(timeoutMs = 3000): Promise<boolean> {
  if (isDesktopBridgeAvailable()) return Promise.resolve(true);
  if (typeof window === "undefined") return Promise.resolve(false);

  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      window.removeEventListener("todoBridgeReady", handleReady);
      resolve(isDesktopBridgeAvailable());
    }, timeoutMs);

    function handleReady() {
      window.clearTimeout(timer);
      resolve(isDesktopBridgeAvailable());
    }

    window.addEventListener("todoBridgeReady", handleReady, { once: true });
  });
}

async function bridgeRequest<T>(request: TodoBridgeRequest): Promise<T> {
  if (!isDesktopBridgeAvailable()) {
    throw new TodoDataError({
      code: "bridge_unavailable",
      message: "桌面数据桥不可用"
    });
  }

  const response = await window.todoBridge!.request<T>(request);
  if (!response.ok) {
    throw new TodoDataError(response.error);
  }
  return response.result;
}

async function shouldUsePreviewStore(): Promise<boolean> {
  if (isDesktopBridgeAvailable()) return false;

  const bridgeReady = await waitForDesktopBridge();
  if (bridgeReady) return false;

  if (isDesktopShellExpected()) {
    throw new TodoDataError({
      code: "bridge_unavailable",
      message: "桌面数据桥不可用，已阻止回退到预览数据"
    });
  }

  return true;
}

function readPreviewTasks(): Task[] {
  if (typeof window === "undefined") return cloneTasks(initialTasks);

  const stored = window.localStorage.getItem(PREVIEW_STORAGE_KEY);
  if (!stored) return cloneTasks(initialTasks);

  try {
    const parsed = JSON.parse(stored) as Partial<Task>[];
    return parsed.map(normalizeTask).filter((task) => task.id);
  } catch {
    return cloneTasks(initialTasks);
  }
}

function writePreviewTasks(tasks: Task[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PREVIEW_STORAGE_KEY, JSON.stringify(tasks));
}

function nextPreviewId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

const previewStore = {
  async listTasks(): Promise<Task[]> {
    const tasks = readPreviewTasks();
    writePreviewTasks(tasks);
    return cloneTasks(tasks);
  },

  async createTask(input: TaskInput): Promise<Task> {
    const tasks = readPreviewTasks();
    const task: Task = {
      id: nextPreviewId("task"),
      ...input,
      subtasks: []
    };
    writePreviewTasks([...tasks, task]);
    return { ...task, subtasks: [] };
  },

  async updateTask(taskId: string, update: TaskUpdate): Promise<Task> {
    const tasks = readPreviewTasks();
    const current = tasks.find((task) => task.id === taskId);
    if (!current) throw new TodoDataError({ code: "not_found", message: "任务不存在" });

    const updated = { ...current, ...update, subtasks: current.subtasks.map((subtask) => ({ ...subtask })) };
    writePreviewTasks(tasks.map((task) => (task.id === taskId ? updated : task)));
    return updated;
  },

  async deleteTask(taskId: string): Promise<Task> {
    const tasks = readPreviewTasks();
    const current = tasks.find((task) => task.id === taskId);
    if (!current) throw new TodoDataError({ code: "not_found", message: "任务不存在" });

    writePreviewTasks(tasks.filter((task) => task.id !== taskId));
    return { ...current, subtasks: current.subtasks.map((subtask) => ({ ...subtask })) };
  },

  async undoTask(task: Task): Promise<Task> {
    const tasks = readPreviewTasks();
    if (tasks.some((current) => current.id === task.id)) return task;
    writePreviewTasks([...tasks, task]);
    return { ...task, subtasks: task.subtasks.map((subtask) => ({ ...subtask })) };
  },

  async createSubtask(taskId: string, input: SubtaskInput): Promise<SubTask> {
    const tasks = readPreviewTasks();
    const parent = tasks.find((task) => task.id === taskId);
    if (!parent) throw new TodoDataError({ code: "not_found", message: "任务不存在" });

    const subtask: SubTask = {
      id: nextPreviewId("subtask"),
      ...input
    };
    const updated = { ...parent, subtasks: [...parent.subtasks, subtask] };
    writePreviewTasks(tasks.map((task) => (task.id === taskId ? updated : task)));
    return { ...subtask };
  },

  async updateSubtask(taskId: string, subtaskId: string, update: SubtaskUpdate): Promise<SubTask> {
    const tasks = readPreviewTasks();
    const parent = tasks.find((task) => task.id === taskId);
    if (!parent) throw new TodoDataError({ code: "not_found", message: "任务不存在" });

    const current = parent.subtasks.find((subtask) => subtask.id === subtaskId);
    if (!current) throw new TodoDataError({ code: "not_found", message: "子任务不存在" });

    const updatedSubtask = { ...current, ...update };
    const updatedParent = {
      ...parent,
      subtasks: parent.subtasks.map((subtask) => (subtask.id === subtaskId ? updatedSubtask : subtask))
    };
    writePreviewTasks(tasks.map((task) => (task.id === taskId ? updatedParent : task)));
    return updatedSubtask;
  }
};

export const todoData = {
  isDesktopBridgeAvailable,

  async listTasks(): Promise<Task[]> {
    if (await shouldUsePreviewStore()) return previewStore.listTasks();
    const tasks = await bridgeRequest<Task[]>({ action: "listTasks" });
    return tasks.map(normalizeTask).filter((task) => task.id);
  },

  async createTask(input: TaskInput): Promise<Task> {
    if (await shouldUsePreviewStore()) return previewStore.createTask(input);
    const task = await bridgeRequest<Task>({ action: "createTask", payload: input });
    return normalizeTask(task);
  },

  async updateTask(taskId: string, update: TaskUpdate): Promise<Task> {
    if (await shouldUsePreviewStore()) return previewStore.updateTask(taskId, update);
    const task = await bridgeRequest<Task>({
      action: "updateTask",
      payload: { taskId, update }
    });
    return normalizeTask(task);
  },

  async deleteTask(taskId: string): Promise<Task> {
    if (await shouldUsePreviewStore()) return previewStore.deleteTask(taskId);
    const task = await bridgeRequest<Task>({
      action: "deleteTask",
      payload: { taskId }
    });
    return normalizeTask(task);
  },

  async undoTask(task: Task): Promise<Task> {
    if (await shouldUsePreviewStore()) return previewStore.undoTask(task);
    const restored = await bridgeRequest<Task>({
      action: "undoTask",
      payload: { taskId: task.id }
    });
    return normalizeTask(restored);
  },

  async createSubtask(taskId: string, input: SubtaskInput): Promise<SubTask> {
    if (await shouldUsePreviewStore()) return previewStore.createSubtask(taskId, input);
    const subtask = await bridgeRequest<SubTask>({
      action: "createSubtask",
      payload: { taskId, input }
    });
    return normalizeSubtask(subtask);
  },

  async updateSubtask(taskId: string, subtaskId: string, update: SubtaskUpdate): Promise<SubTask> {
    if (await shouldUsePreviewStore()) return previewStore.updateSubtask(taskId, subtaskId, update);
    const subtask = await bridgeRequest<SubTask>({
      action: "updateSubtask",
      payload: { taskId, subtaskId, update }
    });
    return normalizeSubtask(subtask);
  }
};
