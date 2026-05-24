interface UndoToastProps {
  message: string | null;
  canUndo: boolean;
  onUndo: () => void;
}

export function UndoToast({ message, canUndo, onUndo }: UndoToastProps) {
  if (!message) return null;

  return (
    <div className="fixed bottom-5 left-1/2 z-[60] flex min-h-11 w-[min(420px,calc(100vw-32px))] -translate-x-1/2 items-center justify-between gap-4 rounded-default border border-line bg-surface-strong px-4 py-3 text-[13px] text-ink shadow-floating">
      <span>{message}</span>
      {canUndo ? (
        <button
          type="button"
          className="rounded-default px-3 py-1.5 text-[13px] font-semibold text-primary hover:bg-primary-soft"
          onClick={onUndo}
          title="撤销删除"
          aria-label="撤销删除"
        >
          撤销
        </button>
      ) : null}
    </div>
  );
}
