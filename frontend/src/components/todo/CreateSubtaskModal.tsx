import { useEffect, useRef, useState } from "react";

import { normalizeDateRange } from "@/lib/date";
import { DatePickerField } from "@/components/ui/DatePickerField";
import { ModalShell } from "@/components/ui/ModalShell";
import { StatusDropdown } from "@/components/ui/StatusDropdown";
import type { SubTask, Task, TaskStatus } from "@/types/todo";

interface CreateSubtaskModalProps {
  open: boolean;
  task: Task | null;
  fallbackDate: string;
  onCancel: () => void;
  onCreate: (subtask: SubTask) => void;
}

export function CreateSubtaskModal({ open, task, fallbackDate, onCancel, onCreate }: CreateSubtaskModalProps) {
  const titleRef = useRef<HTMLInputElement>(null);
  const [startDate, setStartDate] = useState(fallbackDate);
  const [endDate, setEndDate] = useState(fallbackDate);
  const [status, setStatus] = useState<TaskStatus>("未启动");

  useEffect(() => {
    if (!open) return;
    setStatus("未启动");
    setStartDate(task?.start_date || fallbackDate);
    setEndDate(task?.end_date || fallbackDate);
    if (titleRef.current) titleRef.current.value = "";
    window.setTimeout(() => titleRef.current?.focus(), 0);
  }, [fallbackDate, open, task]);

  const handleCreate = () => {
    const [cleanStart, cleanEnd] = normalizeDateRange(startDate, endDate, fallbackDate);
    const title = titleRef.current?.value.trim() || "";

    onCreate({
      id: `sub-${Date.now()}`,
      title: title || "未命名子任务",
      start_date: cleanStart,
      end_date: cleanEnd,
      status,
      background: ""
    });
  };

  return (
    <ModalShell
      open={open}
      title="新增子任务"
      footer={
        <>
          <button type="button" className="tm-button h-8 px-4" onClick={onCancel} title="取消" aria-label="取消">
            取消
          </button>
          <button type="button" className="tm-button-primary h-8 px-4" onClick={handleCreate} title="添加子任务" aria-label="添加子任务">
            添加
          </button>
        </>
      }
    >
      <div className="space-y-3">
        <label className="tm-field">
          <span>标题</span>
          <input ref={titleRef} className="tm-input h-[38px]" defaultValue="" placeholder="输入子任务标题" />
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="tm-field">
            <span>开始日期</span>
            <DatePickerField value={startDate} onChange={setStartDate} ariaLabel="选择开始日期" />
          </label>
          <label className="tm-field">
            <span>截止日期</span>
            <DatePickerField value={endDate} onChange={setEndDate} ariaLabel="选择截止日期" align="right" />
          </label>
        </div>
        <label className="tm-field">
          <span>当前状态</span>
          <StatusDropdown value={status} onChange={setStatus} ariaLabel="选择子任务状态" className="w-full" />
        </label>
      </div>
    </ModalShell>
  );
}
