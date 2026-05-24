import { formatDateRange } from "@/lib/date";
import { DatePickerField } from "@/components/ui/DatePickerField";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StatusSegmentedControl } from "@/components/ui/StatusSegmentedControl";
import { SubtaskRow } from "@/components/todo/SubtaskRow";
import type { DetailDraft, SubTask, Task, TaskStatus } from "@/types/todo";

interface TaskDetailPanelProps {
  task: Task | null;
  draft: DetailDraft | null;
  onDraftChange: (draft: DetailDraft) => void;
  onTaskStatusChange: (status: TaskStatus) => void;
  onSubtaskDraftStatusChange: (index: number, status: TaskStatus) => void;
  onAddSubtask: () => void;
  onSave: () => void;
  onDelete: () => void;
}

export function TaskDetailPanel({
  task,
  draft,
  onDraftChange,
  onTaskStatusChange,
  onSubtaskDraftStatusChange,
  onAddSubtask,
  onSave,
  onDelete
}: TaskDetailPanelProps) {
  return (
    <aside className="tm-panel h-full min-h-0" data-figma-node="Right rail / 任务详情">
      <header className="border-b border-line px-[14px] py-3">
        <h2 className="font-display text-[16px] font-bold text-ink">任务详情</h2>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-[12px] text-muted">
          {task ? (
            <>
              <span>{formatDateRange(task)}</span>
              <span aria-hidden="true">·</span>
              <StatusBadge status={task.status} />
            </>
          ) : (
            "选中任务后编辑"
          )}
        </p>
      </header>

      {task && draft ? (
        <>
          <section className="min-h-0 flex-1 space-y-4 overflow-auto p-[14px]">
            <label className="tm-field">
              <span>标题</span>
              <input
                className="tm-input h-[38px]"
                value={draft.title}
                onChange={(event) => onDraftChange({ ...draft, title: event.target.value })}
              />
            </label>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="tm-field">
                <span>开始日期</span>
                <DatePickerField
                  value={draft.start_date}
                  onChange={(start_date) => onDraftChange({ ...draft, start_date })}
                  ariaLabel="选择开始日期"
                />
              </label>
              <label className="tm-field">
                <span>截止日期</span>
                <DatePickerField
                  value={draft.end_date}
                  onChange={(end_date) => onDraftChange({ ...draft, end_date })}
                  ariaLabel="选择截止日期"
                  align="right"
                />
              </label>
            </div>
            <label className="tm-field">
              <span>备注</span>
              <textarea
                className="tm-input min-h-[84px] resize-none py-3"
                value={draft.background}
                onChange={(event) => onDraftChange({ ...draft, background: event.target.value })}
              />
            </label>
            <div className="tm-field">
              <span>状态</span>
              <StatusSegmentedControl value={task.status} onChange={onTaskStatusChange} />
            </div>
            <div className="tm-field min-h-0">
              <div className="flex items-center justify-between gap-3">
                <span>子任务</span>
                <button type="button" className="tm-button h-9 px-3 text-[12px]" onClick={onAddSubtask} title="新增子任务" aria-label="新增子任务">
                  + 子任务
                </button>
              </div>
              <div className="mt-3 max-h-[260px] space-y-2 overflow-auto pr-1">
                {draft.subtasks.length ? (
                  draft.subtasks.map((subtask: SubTask, index: number) => (
                    <SubtaskRow
                      key={subtask.id}
                      subtask={subtask}
                      onStatusChange={(status) => onSubtaskDraftStatusChange(index, status)}
                    />
                  ))
                ) : (
                  <div className="rounded-default border border-line bg-surface-soft p-3 text-[13px] text-muted">
                    暂无子任务。
                  </div>
                )}
              </div>
            </div>
          </section>
          <footer className="flex items-center justify-between border-t border-line p-[14px]">
            <button type="button" className="tm-button-danger" onClick={onDelete} title="删除任务" aria-label="删除任务">
              删除
            </button>
            <button type="button" className="tm-button-primary" onClick={onSave} title="保存修改" aria-label="保存修改">
              保存
            </button>
          </footer>
        </>
      ) : (
        <section className="p-[14px]">
          <div className="rounded-default border border-line bg-surface-soft p-4 text-[13px] leading-relaxed text-muted">
            请选择日历中的任务，或新建一个任务。
          </div>
        </section>
      )}
    </aside>
  );
}
