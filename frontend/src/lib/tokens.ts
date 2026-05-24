import type { TaskStatus, ThemeMode } from "@/types/todo";

export const designTokens = {
  colors: {
    light: {
      bgA: "#dff4ff",
      bgB: "#dff8ec",
      bgC: "#eef2f5",
      surfaceDefault: "rgba(255,255,255,0.84)",
      surfaceSoft: "rgba(255,255,255,0.68)",
      surfaceStrong: "#ffffff",
      dropdown: "#ffffff",
      textInk: "#123047",
      textMuted: "#6a7d8e",
      lineDefault: "rgba(98,132,154,0.18)",
      lineStrong: "rgba(73,121,151,0.34)",
      primaryBlue: "#2e8df5",
      primaryBlueSoft: "#e8f4ff",
      secondaryGreen: "#23b883",
      secondaryGreenSoft: "#e8f8f0",
      tertiaryAmber: "#d69b18",
      tertiaryAmberSoft: "#fff5d9",
      dangerDefault: "#e05858",
      dangerSoft: "#fff0f0",
      neutralSilver: "#eef3f6"
    },
    dark: {
      bgA: "#07131d",
      bgB: "#0e2230",
      bgC: "#142a38",
      surfaceDefault: "#102636",
      surfaceSoft: "#132d3d",
      surfaceStrong: "#193546",
      dropdown: "#102636",
      textInk: "#e8f3f8",
      textMuted: "#94a8b7",
      lineDefault: "rgba(146,180,198,0.18)",
      lineStrong: "rgba(146,180,198,0.34)",
      primaryBlue: "#65b5ff",
      primaryBlueSoft: "#173753",
      secondaryGreen: "#4dd7a1",
      secondaryGreenSoft: "#143c32",
      tertiaryAmber: "#f0bf42",
      tertiaryAmberSoft: "#46391b",
      dangerDefault: "#ff7a7a",
      dangerSoft: "#44252a",
      neutralSilver: "#203747"
    }
  },
  typography: {
    brandLabel: ["Plus Jakarta Sans", 17, 600, 1.1],
    metricValue: ["Plus Jakarta Sans", 21, 800, 1.2],
    panelHeading: ["Plus Jakarta Sans", 16, 600, 1.4],
    taskTitle: ["Inter", 14, 700, 1.35],
    body: ["Inter", 14, 400, 1.5],
    label: ["Inter", 14, 500, 1.2],
    caption: ["Inter", 12, 400, 1.45],
    badgeCount: ["Inter", 11, 600, 1]
  },
  radius: {
    sm: 4,
    default: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 9999
  },
  spacing: {
    appMargin: 18,
    gutterLg: 14,
    gutterMd: 12,
    paddingBase: 10,
    gapSm: 8,
    gapXs: 6
  },
  effects: {
    glassBlur: "blur(22px)",
    panelShadow: "0 18px 50px rgba(58,97,124,0.14)",
    floatingShadow: "0 26px 80px rgba(45,84,109,0.24)",
    focusRing: "0 0 0 4px rgba(46,141,245,0.12)"
  }
} as const;

export const statusList: TaskStatus[] = ["未启动", "完成中", "已完成", "已取消"];

export function normalizeTaskStatus(value: unknown): TaskStatus {
  return statusList.includes(value as TaskStatus) ? (value as TaskStatus) : "未启动";
}

export const filterTabs: Array<{ value: "all" | TaskStatus; label: string }> = [
  { value: "all", label: "全部" },
  { value: "未启动", label: "未启" },
  { value: "完成中", label: "进行" },
  { value: "已完成", label: "完成" },
  { value: "已取消", label: "取消" }
];

export const themeOptions: Array<{ value: ThemeMode; icon: string; label: string; title: string }> = [
  { value: "system", icon: "◐", label: "自动", title: "跟随系统主题" },
  { value: "light", icon: "☼", label: "明色", title: "使用明色主题" },
  { value: "dark", icon: "☾", label: "暗色", title: "使用暗色主题" }
];

export const statusTone: Record<
  TaskStatus,
  {
    dot: string;
    badge: string;
    mini: string;
    row: string;
  }
> = {
  未启动: {
    dot: "bg-muted",
    badge: "bg-neutral-silver text-muted",
    mini: "bg-neutral-silver text-muted",
    row: ""
  },
  完成中: {
    dot: "bg-primary",
    badge: "bg-primary-soft text-primary",
    mini: "bg-primary-soft text-primary",
    row: ""
  },
  已完成: {
    dot: "bg-secondary",
    badge: "bg-secondary-soft text-secondary",
    mini: "bg-secondary-soft text-secondary",
    row: ""
  },
  已取消: {
    dot: "bg-muted",
    badge: "bg-danger-soft text-danger",
    mini: "bg-danger-soft text-danger",
    row: "line-through opacity-70"
  }
};

export function getStatusTone(status: TaskStatus) {
  return statusTone[normalizeTaskStatus(status)];
}
