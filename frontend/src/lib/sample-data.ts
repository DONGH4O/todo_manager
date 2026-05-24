import type { Task } from "@/types/todo";

export const TODAY = "2026-05-20";

export const initialTasks: Task[] = [
  {
    id: "t1",
    title: "确认 M4 UI 视觉方向",
    start_date: "2026-05-20",
    end_date: "2026-05-22",
    status: "完成中",
    background: "先确认浅蓝、浅绿、浅银渐变背景下的主界面信息层级。",
    subtasks: [
      {
        id: "t1-s1",
        title: "检查月历可读性",
        start_date: "2026-05-20",
        end_date: "2026-05-20",
        status: "已完成",
        background: ""
      },
      {
        id: "t1-s2",
        title: "确认详情区密度",
        start_date: "2026-05-20",
        end_date: "2026-05-21",
        status: "完成中",
        background: ""
      },
      {
        id: "t1-s3",
        title: "记录第一轮反馈",
        start_date: "2026-05-21",
        end_date: "2026-05-22",
        status: "未启动",
        background: ""
      }
    ]
  },
  {
    id: "t2",
    title: "整理关键工作流",
    start_date: "2026-05-20",
    end_date: "2026-05-26",
    status: "未启动",
    background: "覆盖搜索定位、新建、编辑状态、删除与撤销。",
    subtasks: [
      {
        id: "t2-s1",
        title: "搜索结果跳转",
        start_date: "2026-05-20",
        end_date: "2026-05-21",
        status: "未启动",
        background: ""
      },
      {
        id: "t2-s2",
        title: "删除确认弹窗",
        start_date: "2026-05-22",
        end_date: "2026-05-22",
        status: "未启动",
        background: ""
      }
    ]
  },
  {
    id: "t3",
    title: "输出设计系统 v2 目录",
    start_date: "2026-05-21",
    end_date: "2026-05-27",
    status: "完成中",
    background: "下一轮确认方向后拆解颜色、间距、控件、状态和暗色主题。",
    subtasks: [
      {
        id: "t3-s1",
        title: "颜色命名",
        start_date: "2026-05-21",
        end_date: "2026-05-22",
        status: "完成中",
        background: ""
      },
      {
        id: "t3-s2",
        title: "状态组件",
        start_date: "2026-05-23",
        end_date: "2026-05-25",
        status: "未启动",
        background: ""
      }
    ]
  },
  {
    id: "t4",
    title: "月历 2K 布局检查",
    start_date: "2026-05-24",
    end_date: "2026-05-29",
    status: "未启动",
    background: "确认日格、任务条和右侧详情不拥挤。",
    subtasks: [
      {
        id: "t4-s1",
        title: "宽屏三列布局",
        start_date: "2026-05-24",
        end_date: "2026-05-25",
        status: "未启动",
        background: ""
      },
      {
        id: "t4-s2",
        title: "窄屏单列布局",
        start_date: "2026-05-26",
        end_date: "2026-05-27",
        status: "未启动",
        background: ""
      }
    ]
  },
  {
    id: "t5",
    title: "完成 M3 验收回看",
    start_date: "2026-05-18",
    end_date: "2026-05-19",
    status: "已完成",
    background: "作为 M4 设计输入，不改动业务层契约。",
    subtasks: [
      {
        id: "t5-s1",
        title: "确认 CLI 契约",
        start_date: "2026-05-18",
        end_date: "2026-05-18",
        status: "已完成",
        background: ""
      },
      {
        id: "t5-s2",
        title: "确认 GUI 问题清单",
        start_date: "2026-05-19",
        end_date: "2026-05-19",
        status: "已完成",
        background: ""
      }
    ]
  },
  {
    id: "t6",
    title: "旧版视觉方案废弃",
    start_date: "2026-05-15",
    end_date: "2026-05-16",
    status: "已取消",
    background: "保留在原型中用于检查已取消任务的展示效果。",
    subtasks: [
      {
        id: "t6-s1",
        title: "归档旧配色",
        start_date: "2026-05-15",
        end_date: "2026-05-15",
        status: "已取消",
        background: ""
      }
    ]
  }
];
