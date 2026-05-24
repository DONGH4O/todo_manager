---
name: Layered Clarity
colors:
  surface: rgba(255, 255, 255, 0.84)
  surface-dim: '#c1ddfb'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#edf4ff'
  surface-container: '#e2efff'
  surface-container-high: '#d8eaff'
  surface-container-highest: '#cde5ff'
  on-surface: '#001d32'
  on-surface-variant: '#414753'
  inverse-surface: '#15334a'
  inverse-on-surface: '#e7f2ff'
  outline: '#717784'
  outline-variant: '#c0c7d5'
  surface-tint: '#005fb0'
  primary: '#005cac'
  on-primary: '#ffffff'
  primary-container: '#0075d7'
  on-primary-container: '#fefcff'
  inverse-primary: '#a6c8ff'
  secondary: '#006c4a'
  on-secondary: '#ffffff'
  secondary-container: '#75fbc0'
  on-secondary-container: '#00734f'
  tertiary: '#7a5500'
  on-tertiary: '#ffffff'
  tertiary-container: '#996c00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a6c8ff'
  on-primary-fixed: '#001c3b'
  on-primary-fixed-variant: '#004786'
  secondary-fixed: '#75fbc0'
  secondary-fixed-dim: '#56dda5'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#005237'
  tertiary-fixed: '#ffdea9'
  tertiary-fixed-dim: '#fbbc3c'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5e4100'
  background: '#f7f9ff'
  on-background: '#001d32'
  surface-variant: '#cde5ff'
  bg-a: '#dff4ff'
  bg-b: '#dff8ec'
  bg-c: '#eef2f5'
  ink: '#123047'
  muted: '#6a7d8e'
  danger: '#e05858'
  line: rgba(98, 132, 154, 0.18)
  ink-dark: '#e8f3f8'
  muted-dark: '#94a8b7'
  bg-a-dark: '#07131d'
  bg-b-dark: '#0e2230'
  bg-c-dark: '#142a38'
typography:
  brand-label:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '600'
    lineHeight: '1.1'
  metric-value:
    fontFamily: Plus Jakarta Sans
    fontSize: 21px
    fontWeight: '800'
    lineHeight: '1.2'
  panel-heading:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: '1.4'
  task-title:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: '1.35'
  subheading:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: '1.4'
  body:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.45'
  badge-count:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  app-margin: 18px
  gutter-lg: 14px
  gutter-md: 12px
  padding-base: 10px
  gap-sm: 8px
  gap-xs: 6px
---

## Brand & Style

The design system is built on the philosophy of **Layered Clarity**, a design narrative that balances high information density with a serene, airy aesthetic. It is specifically tailored for productivity environments where focus and organization are paramount. The system evokes a sense of "digital calm" through rhythmic spacing and sophisticated material properties.

### Design Style: Glassmorphism & Minimalism
This design system utilizes a refined **Glassmorphism** style, characterized by:
- **Translucency:** UI elements use semi-transparent surfaces that reveal a subtle underlying grid texture, creating a sense of depth without visual clutter.
- **Atmospheric Blur:** High-intensity backdrop filters (22px) ensure legibility while maintaining a light, ethereal quality.
- **Rhythmic Precision:** A strict adherence to a grid-based layout provides a "blueprint" feel, suggesting order and reliability.
- **Modern Professionalism:** A blend of minimalist whitespace and high-contrast semantic accents ensures that the interface feels both premium and functional.

## Colors

The color system employs a tiered approach, utilizing three distinct background shades to create environmental depth.

### Color Tiers
- **Primary (Blue):** Used for interactive elements, focus states, and primary actions.
- **Secondary (Green):** Represents success, completion, and positive status.
- **Tertiary (Amber):** Used for warnings, high-priority highlights, and attention-required states.
- **Neutral (Ink):** The core structural color for typography and heavy iconography.

### Semantic Mapping
Text contrast is strictly managed through three levels:
1. **Ink:** High-contrast primary text.
2. **Muted:** Secondary information and metadata.
3. **Soft:** Background-adaptive utility text or disabled states.

### Background & Surface
The system uses a tri-color background blend (`bg-a`, `bg-b`, `bg-c`) to create a soft gradient environment. Surfaces are not solid; they are semi-transparent containers that leverage the `surface` token to create the frosted glass effect.

## Typography

The typography strategy pairs **Plus Jakarta Sans** for display and structural headings with **Inter** for functional body and label text. This combination ensures a welcoming, modern brand voice without sacrificing the extreme legibility required for task management.

### Hierarchy Roles
- **Display Levels:** `brand-label` and `metric-value` use heavier weights to anchor the UI.
- **Functional Levels:** `task-title` and `body` are optimized for density and reading comfort.
- **Utility Levels:** `caption` and `badge-count` handle metadata and numerical indicators at small scales.

### Internationalization
For CJK character support, the system falls back to high-quality system fonts (`Microsoft YaHei`, `PingFang SC`) to maintain the same visual weight and rhythm as the primary Latin faces.

## Layout & Spacing

This design system uses a **Fluid Grid** model with fixed sidebar constraints to ensure a predictable productivity environment across devices.

### Layout Model
- **Topbar:** A global persistent header for brand, search, and system-level actions.
- **Three-Column View (Desktop):**
    - **Rail (Sidebar):** Fixed at `260px`. Contains navigation and primary filters.
    - **Calendar (Main):** Fluid (`1fr`). The primary workspace area.
    - **Detail (Panel):** Fixed at `340px`. Used for deep-dive task information.

### Responsive Behavior
- **Desktop (>1180px):** Full three-column layout.
- **Tablet (<1180px):** Two-column layout; the Detail panel reflows to full width at the bottom of the viewport.
- **Mobile (<900px):** Single-column layout; all panels stack vertically, and calendar days transition to fluid heights to accommodate touch targets.

### Spacing Rhythm
The system follows a 2px/4px incremental rhythm. The `app-margin` of 18px creates a protective "breathing zone" around the entire application interface, distinguishing it from the native OS environment.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Glassmorphism** rather than traditional elevation shadows.

### Layering Strategy
- **Base Layer:** The background grid texture provided by a linear-gradient repeating pattern.
- **Surface Layer:** All main panels (Rail, Calendar, Detail) use the `surface` token with a `22px` backdrop blur. This separates the content from the background while maintaining light transmission.
- **Floating Layer:** Modals and search overlays use a more aggressive shadow (`0 26px 80px`) to indicate temporary displacement of the main interface.

### Shadows & Borders
Shadows are highly diffused and tinted with the neutral ink color at very low opacity (14% on light, 28% on dark). Borders serve as the primary structural dividers, using `line` for standard separation and `line-strong` for interactive component boundaries.

## Shapes

The shape language is consistently "Soft-Rounded." 

- **Standard Radius (8px):** Applied to all primary containers, cards, buttons, and input fields.
- **Small Radius (6px):** Used for nested components like theme toggles and calendar day-items.
- **Pill (Full Circle):** Reserved for status indicators, tags, and badges to make them easily distinguishable from structural UI elements.

Dashed borders are used exclusively for "Empty States" or "Add New" containers to suggest a placeholder or an action that has not yet been realized.

## Components

### Buttons & Inputs
- **Buttons:** Use a `button-bg` token (a semi-opaque white or navy) to maintain the glass effect. On hover, apply a subtle `translateY(-1px)` and a slightly stronger background opacity.
- **Input Fields:** Styled with `surface-strong` for maximum contrast during data entry. The focus state uses a 4px soft blue ring (`primary-color` at 12% opacity).

### Task Cards
- **Hover State:** Cards should transition their border color to `line-strong` and increase shadow depth slightly.
- **Selection:** Use a `primary-color` border or a subtle background tint to indicate the active task being viewed in the Detail panel.

### Status Indicators
- **Status Dots:** 
    - **Green:** Active / Completed.
    - **Amber:** Pending / Warning.
    - **Blue:** In Progress / Primary.
    - **Danger:** Overdue / Error.

### Overlays & Modals
- **Search Results:** Display as a floating glass panel directly under the search bar. Use a z-index of 1000 to ensure it clears all other UI logic.
- **Modal Backdrops:** Use a tinted semi-transparent overlay to dim the rest of the UI, focusing the user's attention on the centered glass dialog.