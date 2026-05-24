import { formatDateRange } from "@/lib/date";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Task } from "@/types/todo";

interface SearchResultsDropdownProps {
  query: string;
  results: Task[];
  onSelect: (task: Task) => void;
}

export function SearchResultsDropdown({ query, results, onSelect }: SearchResultsDropdownProps) {
  return (
    <div className="space-y-2 p-2">
      <div className="flex items-center justify-between gap-3 px-1 text-[12px] text-muted">
        <span>{query ? `找到 ${results.length} 个结果` : "最近任务与可搜索字段"}</span>
        <span className="hidden sm:inline">标题 / 备注 / 子任务 / 状态 / 日期</span>
      </div>
      {results.length ? (
        <div className="max-h-[min(560px,calc(100vh-190px))] space-y-2 overflow-auto pr-1">
          {results.map((task, index) => (
            <button
              key={task.id}
              type="button"
              className={`grid w-full grid-cols-[1fr_auto] items-center gap-3 rounded-default px-3 py-2 text-left transition hover:bg-primary-soft ${
                index === 0 ? "bg-primary-soft" : ""
              }`}
              title={`定位 ${task.title}`}
              aria-label={`定位 ${task.title}`}
              onClick={() => onSelect(task)}
            >
              <span className="min-w-0">
                <strong className="block truncate text-[13px] text-ink">{task.title}</strong>
                <small className="block truncate text-[12px] text-muted">{formatDateRange(task)}</small>
                <small className="block truncate text-[12px] text-muted">{task.background}</small>
              </span>
              <StatusBadge status={task.status} />
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-default border border-line bg-surface-soft p-4 text-[13px] text-muted">没有找到匹配任务。</div>
      )}
      <div className="rounded-[6px] bg-secondary-soft px-3 py-2 text-[11px] leading-snug text-ink">
        提示：点击结果可定位到对应日期与任务；Esc关闭
      </div>
    </div>
  );
}
