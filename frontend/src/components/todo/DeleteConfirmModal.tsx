import { ModalShell } from "@/components/ui/ModalShell";
import type { Task } from "@/types/todo";

interface DeleteConfirmModalProps {
  open: boolean;
  task: Task | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DeleteConfirmModal({ open, task, onCancel, onConfirm }: DeleteConfirmModalProps) {
  return (
    <ModalShell
      open={open}
      title="确认删除"
      footer={
        <>
          <button type="button" className="tm-button h-8 px-4" onClick={onCancel} title="取消删除" aria-label="取消删除">
            取消
          </button>
          <button type="button" className="tm-button-danger h-8 px-4" onClick={onConfirm} title="确认删除" aria-label="确认删除">
            删除
          </button>
        </>
      }
    >
      <p className="text-[13px] leading-relaxed text-muted">
        {task ? `删除“${task.title}”后会显示撤销提示，超时后视为确认。` : "删除后会显示撤销提示，超时后视为确认。"}
      </p>
    </ModalShell>
  );
}
