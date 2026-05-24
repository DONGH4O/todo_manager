export function BrandLockup() {
  return (
    <section className="flex min-w-[220px] items-center gap-3" aria-label="Todo Manager 品牌">
      <div className="grid size-[34px] place-items-center rounded-default bg-[linear-gradient(135deg,var(--color-primary),var(--color-secondary))] font-bold text-white">
        T
      </div>
      <div className="min-w-0">
        <h1 className="font-display text-[17px] font-bold leading-tight text-ink">Todo Manager</h1>
        <p className="truncate text-[12px] leading-tight text-muted">让每个待办都有清晰节奏</p>
      </div>
    </section>
  );
}
