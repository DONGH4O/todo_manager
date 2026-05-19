# Design System: Todo Manager

## Visual Identity
A clean, functional, and productivity-focused interface that balances a data-dense calendar view with a clear detail-oriented side panel. The system supports both light and dark modes with a robust token-based approach.

## Design Tokens

### Color Palette

#### Light Theme (Default)
- **Backgrounds:**
  - `bg-root`: #F1F5F9 (Soft gray for the main workspace)
  - `bg-surface`: #FFFFFF (Primary card and panel background)
  - `bg-surface-alt`: #F8FAFC (Subtle contrast for list items)
  - `bg-today`: #EFF6FF (Highlighted background for current date)
- **Text:**
  - `text-primary`: #0F172A (Deep navy for high readability)
  - `text-secondary`: #475569 (Medium gray for labels and secondary info)
  - `text-tertiary`: #94A3B8 (Light gray for placeholder and disabled states)
  - `text-link`: #2563EB (Brand blue for interactive text)
- **Status Colors:**
  - `pending`: #9CA3AF (Gray)
  - `active`: #3B82F6 (Blue)
  - `done`: #10B981 (Green)
  - `cancelled`: #9CA3AF (Muted gray)
- **Accents & Borders:**
  - `border`: #E2E8F0
  - `color-danger`: #EF4444 (System red for "New" and "Delete" actions)

#### Dark Theme
- **Backgrounds:**
  - `bg-root`: #0B1120
  - `bg-surface`: #1E293B
  - `bg-surface-alt`: #172033
- **Text:**
  - `text-primary`: #F1F5F9
  - `text-secondary`: #94A3B8
- **Accents:**
  - `border`: #334155
  - `color-danger`: #F87171

### Typography
- **Font Stack:** "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", "Noto Sans CJK SC", system-ui, sans-serif.
- **Sizes:**
  - `base`: 14px (Standard body text)
  - `heading`: 20px (Month/Year navigation)
  - `sub-heading`: 16px (Panel titles)
  - `small`: 12px (Labels, badges, and metadata)
  - `xs`: 10px (Status dots and "More" indicators)

### Spacing & Layout
- **Radius:**
  - `sm`: 6px (Inputs, buttons)
  - `md`: 10px (Nav arrows, theme toggle)
  - `lg`: 14px (Search dropdown, task cards)
  - `xl`: 18px (Main calendar and detail panels)
- **Grid:** 7-column calendar grid with responsive scaling for different resolutions.
- **Layout Ratio:** 6:4 split between the Calendar Wrap and Detail Panel.

## Component Patterns

### 1. Navigation Bar
A top-aligned bar containing the theme toggle and a full-width search input with a result dropdown.

### 2. Search Dropdown
- **Dimensions:** Width matches the parent search input; max-height of 360px with vertical scrolling.
- **Positioning:** Absolute positioning, 44px from the top of the search container.
- **Spacing:** 12px 16px padding for each result item.
- **Visuals:** Features a `shadow-xl` elevation, `radius-lg` corners, and a structured layout showing task titles, dates, and background snippets.
- **Animation:** Uses a `0.2s ease-out` fade-in animation (`searchIn`) with a subtle 10px downward slide upon activation.
- **Content:** Title-date row with emphasis on title; secondary background text uses ellipsis for overflow.

### 3. Month/Year Picker
Centralized navigation controls with custom dropdowns for selecting specific months or navigating a 5-year range.

### 4. Calendar Grid
- **Cells:** Interactive containers that display day numbers and a vertical list of task bars.
- **Task Bars:** Status-colored indicators with title text and hover-triggered action buttons (Edit, Delete, Add Subtask).

### 5. Task Bar Actions (Floating)
- **Visibility:** Hidden by default (`display: none`); revealed on parent `.task-bar` hover (`display: flex`).
- **Button Styling:**
  - `size`: 20x20px square.
  - `radius`: 4px.
  - `background`: `rgba(255, 255, 255, 0.7)` for adaptive contrast.
  - `interaction`: Background color shifts on hover based on action type (Blue for Add, Red for Danger, Gray for Edit).
- **Icons:** Emoji-based identifiers (✏️, ❌, ➕).

### 6. Detail Panel
A right-aligned panel for inspecting task data. Includes a "New Task" primary action and vertical scrolling for long descriptions or subtask lists.

### 7. Modals & Overlays
Standardized form layout with:
- Required field indicators (red asterisk).
- Date pickers for start/end dates.
- Segmented "Status" radio group.
- Textarea for "Background" descriptions.

## Animation & Interactions
- **Transitions:** `0.15s ease` for hover states; `0.25s cubic-bezier` for structural transitions.
- **Modal Entry:** `0.2s ease` with a slight scale and translateY effect.
- **Search Entry:** `0.2s ease-out` fade and slide from top.
- **Toasts:** Automatic fade-in and slide-up animation with a 5-second persistence and an "Undo" capability for destructive actions.
