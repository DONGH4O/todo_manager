import { useEffect, useRef, useState } from "react";

import { normalizeDateRange } from "@/lib/date";
import { statusList } from "@/lib/tokens";
import { DatePickerField } from "@/components/ui/DatePickerField";
import { ModalShell } from "@/components/ui/ModalShell";
import type { Task, TaskStatus } from "@/types/todo";

interface CreateTaskModalProps {
  open: boolean;
  selectedDate: string;
  onCancel: () => void;
  onCreate: (task: Task) => void;
}

export function CreateTaskModal({ open, selectedDate, onCancel, onCreate }: CreateTaskModalProps) {
  const titleRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState("");
  const [startDate, setStartDate] = useState(selectedDate);
  const [endDate, setEndDate] = useState(selectedDate);
  const [status, setStatus] = useState<TaskStatus>("未启动");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!open) return;
    setTitle("");
    setNote("");
    setStatus("未启动");
    setStartDate(selectedDate);
    setEndDate(selectedDate);
    window.setTimeout(() => titleRef.current?.focus(), 0);
  }, [open, selectedDate]);

  const handleCreate = () => {
    const [cleanStart, cleanEnd] = normalizeDateRange(startDate, endDate, selectedDate);
    onCreate({
      id: `new-${Date.now()}`,
      title: title.trim() || "未命名任务",
      start_date: cleanStart,
      end_date: cleanEnd,
      status,
      background: note.trim() || "新任务说明待补充。",
      subtasks: []
    });
  };

  return (
    <ModalShell
      open={open}
      title="新建任务"
      footer={
        <>
          <button type="button" className="tm-button h-8 px-4" onClick={onCancel} title="取消" aria-label="取消">
            取消
          </button>
          <button type="button" className="tm-button-primary h-8 px-4" onClick={handleCreate} title="创建任务" aria-label="创建任务">
            创建
          </button>
        </>
      }
    >
      <div className="space-y-3">
        <label className="tm-field">
          <span>标题</span>
          <input ref={titleRef} className="tm-input h-[38px]" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="输入任务标题" />
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
          <select className="tm-select h-[38px] w-full" value={status} onChange={(event) => setStatus(event.target.value as TaskStatus)}>
            {statusList.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="tm-field">
          <span>备注</span>
          <textarea className="tm-input min-h-[74px] resize-none py-3" value={note} onChange={(event) => setNote(event.target.value)} placeholder="可选说明" />
        </label>
      </div>
    </ModalShell>
  );
}
