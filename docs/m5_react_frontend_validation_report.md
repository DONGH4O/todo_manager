# M5 React Frontend Rewrite Validation Report

> Date: 2026-05-22  
> Scope: Figma-driven GUI rewrite under `frontend/`  
> Stack: Next.js App Router, React, TypeScript, Tailwind CSS

## Figma Inputs

- `Desktop / Todo Manager / Light theme`
- `Engineering Handoff / Codex Ready Spec`
- `Navigation dropdown / Search results overlay`
- `Modal state / 新建任务`
- `Reference / Dark theme tokens`

The implementation follows the Figma handoff component map and preserves the interaction model from `docs/m4_uiux_redesign/prototype_v1.html`.

## Implemented Surface

- Design tokens in `frontend/src/lib/tokens.ts` and Tailwind theme extensions.
- Component split matching the handoff: top nav, brand lockup, search box/results, theme switch, today rail, metrics, filter tabs, task cards, calendar workbench/day cells/mini tasks, task detail panel, status segmented control, subtask rows, create task modal, create subtask modal, delete confirmation, undo toast.
- Interactions: search/filter/select, calendar day selection, month/year navigation, today reset, task detail editing, task status update, subtask draft status update with save, create task, create subtask, delete confirmation, undo toast, keyboard `/`, `N`, and `Esc`, and system/light/dark theme switching.
- Responsive layout: desktop three columns, tablet two columns plus detail row, mobile single-column stacking.
- Follow-up polish on 2026-05-22: search results dropdown stacking context is raised above the calendar workbench; the month grid now renders only the visible weeks needed for the selected month; all day cells share equal adaptive height; subtask status pills restore the explicit down-arrow affordance.

## Verification

Commands run from `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd audit --omit=dev
```

Results:

- `npm.cmd run lint`: passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed on `Next.js 16.2.6`.
- `npm.cmd audit --omit=dev`: `found 0 vulnerabilities`.

Visual smoke:

- Dev server verified at `http://127.0.0.1:3015`.
- Chrome headless screenshots captured for desktop and mobile:
  - `.tmp/todo-frontend-desktop-validated.png`
  - `.tmp/todo-frontend-mobile-validated.png`

Follow-up verification for the 2026-05-22 polish fixes:

- `npm.cmd run lint`: passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed on `Next.js 16.2.6`.
- `npm.cmd audit --omit=dev`: `found 0 vulnerabilities`.
- Chrome headless smoke at `1440x1000` with dropdown open:
  - search dropdown exists, `z-index: 120`, and `elementFromPoint` confirms the dropdown is the top visible layer.
  - May 2026 calendar renders `35` day cells, from `2026-04-27` to `2026-05-31`.
  - all visible calendar day cells share one measured height: `118px`.
  - subtask status pill text includes the restored `▾` arrow.
  - screenshot: `.tmp/todo-frontend-polish-dropdown.png`.

Follow-up verification for the 2026-05-23 height and scroll fixes:

- `npm.cmd run lint`: passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed on `Next.js 16.2.6`.
- Production-build smoke served from `.next` static output:
  - at `1440x1000`, May 2026 still renders `35` day cells and all day cells share one measured height: `145px`.
  - the calendar grid fills the usable calendar body; measured bottom gap is `0px`.
  - at `1440x520`, calendar body has `overflow-y: auto`, `clientHeight: 347`, `scrollHeight: 562`, `canScroll: true`.
  - at `1440x520`, the Today rail content region has `overflow-y: auto`, `clientHeight: 347`, `scrollHeight: 943`, `canScroll: true` after task-list stress.
  - at `1440x520`, the task detail edit region has `overflow-y: auto`, `clientHeight: 268`, `scrollHeight: 1272`, `canScroll: true` after content stress.
  - screenshots: `.tmp/todo-frontend-fill-calendar-desktop.png`, `.tmp/todo-frontend-scroll-short-window.png`.

## Notes

- The React frontend is intentionally isolated in `frontend/` and does not import or mutate the legacy PySide6 GUI.
- Figma MCP rate limit prevented repeated pulls for every secondary frame, but the main desktop frame, search overlay, engineering handoff, and page metadata provided the required implementation details.
