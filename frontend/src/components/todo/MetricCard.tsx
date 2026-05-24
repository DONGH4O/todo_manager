interface MetricCardProps {
  value: number;
  label: string;
}

export function MetricCard({ value, label }: MetricCardProps) {
  return (
    <div className="min-h-[74px] rounded-default border border-line bg-surface-soft px-3 py-3">
      <b className="block font-display text-[22px] font-extrabold leading-tight text-ink">{value}</b>
      <span className="mt-2 block text-[12px] leading-tight text-muted">{label}</span>
    </div>
  );
}
