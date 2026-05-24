import type { ReactNode } from "react";

interface ModalShellProps {
  open: boolean;
  title: string;
  children: ReactNode;
  footer: ReactNode;
}

export function ModalShell({ open, title, children, footer }: ModalShellProps) {
  if (!open) return null;

  const titleId = `${title.replace(/\s+/g, "-")}-title`;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-slate-950/28 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      <section className="max-h-[min(720px,calc(100vh-32px))] w-full max-w-[480px] overflow-auto rounded-default border border-line bg-surface-strong p-4 shadow-floating">
        <h2 id={titleId} className="font-display text-[18px] font-bold text-ink">
          {title}
        </h2>
        <div className="mt-4">{children}</div>
        <footer className="mt-4 flex justify-end gap-3">{footer}</footer>
      </section>
    </div>
  );
}
