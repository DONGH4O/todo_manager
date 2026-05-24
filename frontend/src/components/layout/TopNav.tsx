import type { RefObject } from "react";

import { SearchBox } from "@/components/todo/SearchBox";
import { BrandLockup } from "@/components/layout/BrandLockup";
import { ThemeSwitch } from "@/components/layout/ThemeSwitch";
import type { Task, ThemeMode } from "@/types/todo";

interface TopNavProps {
  query: string;
  searchOpen: boolean;
  searchInputRef: RefObject<HTMLInputElement>;
  results: Task[];
  onQueryChange: (query: string) => void;
  onSearchFocus: () => void;
  onSearchButton: () => void;
  onCloseSearch: () => void;
  onSelectSearchResult: (task: Task) => void;
  onToday: () => void;
  onRefresh: () => void;
  onNewTask: () => void;
  themeMode: ThemeMode;
  onThemeModeChange: (mode: ThemeMode) => void;
}

export function TopNav({
  query,
  searchOpen,
  searchInputRef,
  results,
  onQueryChange,
  onSearchFocus,
  onSearchButton,
  onCloseSearch,
  onSelectSearchResult,
  onToday,
  onRefresh,
  onNewTask,
  themeMode,
  onThemeModeChange
}: TopNavProps) {
  return (
    <header className="relative z-[80] grid min-w-0 gap-3 overflow-visible rounded-default border border-line bg-surface-soft p-3 shadow-panel backdrop-blur-glass lg:grid-cols-[220px_minmax(280px,620px)_auto] lg:items-center">
      <BrandLockup />
      <SearchBox
        query={query}
        open={searchOpen}
        inputRef={searchInputRef}
        results={results}
        onQueryChange={onQueryChange}
        onFocus={onSearchFocus}
        onSearch={onSearchButton}
        onClose={onCloseSearch}
        onSelect={onSelectSearchResult}
      />
      <section className="flex flex-wrap items-center justify-start gap-2 lg:justify-end" aria-label="全局操作">
        <button type="button" className="tm-button" onClick={onToday} title="回到今天" aria-label="回到今天">
          ◎ 今天
        </button>
        <button type="button" className="tm-button" onClick={onRefresh} title="刷新数据" aria-label="刷新数据">
          ↻ 刷新
        </button>
        <button type="button" className="tm-button-primary" onClick={onNewTask} title="新建任务" aria-label="新建任务">
          + 新建
        </button>
        <ThemeSwitch value={themeMode} onChange={onThemeModeChange} />
      </section>
    </header>
  );
}
