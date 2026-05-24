import { useEffect, useRef, type RefObject } from "react";

import { SearchResultsDropdown } from "@/components/todo/SearchResultsDropdown";
import type { Task } from "@/types/todo";

interface SearchBoxProps {
  query: string;
  open: boolean;
  inputRef: RefObject<HTMLInputElement>;
  results: Task[];
  onQueryChange: (query: string) => void;
  onFocus: () => void;
  onSearch: () => void;
  onClose: () => void;
  onSelect: (task: Task) => void;
}

export function SearchBox({
  query,
  open,
  inputRef,
  results,
  onQueryChange,
  onFocus,
  onSearch,
  onClose,
  onSelect
}: SearchBoxProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current || rootRef.current.contains(event.target as Node)) return;
      onClose();
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [onClose, open]);

  return (
    <section
      ref={rootRef}
      className="relative z-[90] grid w-full min-w-0 grid-cols-[minmax(0,1fr)_60px] gap-1"
      aria-label="搜索任务"
    >
      <div className="min-w-0">
        <input
          ref={inputRef}
          className="tm-input h-11 w-full min-w-0"
          type="search"
          value={query}
          placeholder="搜索标题、备注、子任务、状态"
          autoComplete="off"
          onChange={(event) => onQueryChange(event.target.value)}
          onFocus={onFocus}
          aria-label="搜索标题、备注、子任务、状态"
        />
      </div>
      <button
        type="button"
        className="h-11 rounded-default border border-line bg-surface-strong text-[13px] font-medium text-ink hover:border-line-strong"
        onClick={onSearch}
        title="搜索"
        aria-label="搜索"
      >
        搜索
      </button>
      {open ? (
        <div className="absolute left-0 top-[calc(100%+8px)] z-[120] w-full rounded-default border border-line bg-dropdown text-ink shadow-dropdown">
          <SearchResultsDropdown query={query} results={results} onSelect={onSelect} />
        </div>
      ) : null}
    </section>
  );
}
