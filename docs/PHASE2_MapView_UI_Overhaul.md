# 🗺️ MapEm Phase 2 – Map View UI Overhaul

This doc outlines the Phase 2 upgrade plan for the Map View and Filter UI. Core tasks are listed by priority, with optional enhancements you can layer in to bring soul, clarity, and polish to the frontend.

---

## ✅ Core Steps (To Be Implemented)

### 1. MapView Layout Restructure
- [ ] Convert layout to responsive `grid-cols-[300px_1fr]`
- [ ] Wrap sidebar in `<Drawer>` UI Kit component
- [ ] Embed map in full-width layout or `<Card>`
- [ ] Float a `<Button>` for "Reset View"
- [ ] Style Loader and Error overlays as centered `Panel`s

### 2. Refactor Filter Components
- [ ] Use `<Input>`, `<Select>`, and `<Button>` from UI Kit
- [ ] Swap raw filters with styled form elements
- [ ] Group toggles under labeled `<PanelSection>` headers
- [ ] Use new `<Drawer>` UI Kit for Advanced Filter drawer

### 3. Polish Map + Legend
- [ ] Float `<Legend>` in a `<Card>` on map corner
- [ ] Add toggle button to hide/show legend
- [ ] Add marker clustering (react-leaflet-markercluster or custom)
- [ ] Add “Reset View” button over map
- [ ] Optional: auto-zoom to selected person

### 4. Unify Layout & Spacing
- [ ] Use `max-w-6xl mx-auto px-6 md:px-12` for main wrappers
- [ ] Replace magic spacing values with `gap-6`, `space-y-4`, etc.
- [ ] Tokenize map height (`calc(100vh - var(--header-height))`)
- [ ] Ensure padding/margin across all pages follow design rules

---

## 🌀 Optional Enhancements

### ✨ Layout & Experience
- [ ] Mini top nav bar showing active tree + filter summary
- [ ] Floating HUD with stats: total pins, people, filters
- [ ] Blur/overlay the map when drawers or modals are open

### 🎛 Filters
- [ ] “Clear All Filters” button with 🗑️ icon
- [ ] Preset filter dropdown (e.g. 1900s + Birth + Direct Family)
- [ ] Slider UI for year range
- [ ] Display “3 filters applied” counter with filter chips

### 🗺 Map Features
- [ ] Hover marker = tooltip (name, event, year)
- [ ] Auto-focus to selected person’s last event
- [ ] Dark map tile layer or map theme switcher
- [ ] Add subtle bounce or glow to selected person pins
- [ ] Animate migration lines between events

### 🧬 Storytelling
- [ ] “Story Mode” walkthrough of a person/family’s timeline
- [ ] Unresolved pin overlay (ghost pins)
- [ ] Timeline bar above map for event filtering by year
- [ ] Show path lines chronologically

### 📈 Analytics & Meta Layers
- [ ] Heatmap toggle to show dense event zones
- [ ] Analytics overlay (most common last names, location frequency)
- [ ] Sidebar stats by time period (e.g. 1910s → 12 migrations)

---

## 🧩 UI Kit Utilities

- [x] `<Button />` – styled w/ `variant`, `loading`, `disabled`
- [x] `<Card />` – reusable `bg-surface` + padding shell
- [x] `<GlowPulse />` – animation wrapper
- [ ] `<Drawer />` – animated slide-in panel
- [ ] `<Input />` – styled text input
- [ ] `<Select />` – styled dropdown
- [ ] `<Badge />` – color chip for tags/filters
- [ ] `<PanelSection />` – group content under label
- [ ] `<Overlay />` – modal or status dimmer

---

## 🗂 Suggested File Structure


frontend/ ├── components/ │ ├── MapView.jsx │ ├── QuickFilterBar.jsx │ ├── AdvancedFilterDrawer.jsx │ └── Legend.jsx │ └── components/ui/ ├── Button.jsx ├── Card.jsx ├── Drawer.jsx ├── Input.jsx ├── Select.jsx ├── Badge.jsx ├── PanelSection.jsx └── Overlay.jsx


---

## 🔄 Phase Tracking

| Phase | Status  |
|-------|---------|
| Phase 1 – Design Tokens + Visual Identity | ✅ Complete |
| Phase 2 – Map View & Filter UX Overhaul | 🚧 In Progress |
| Phase 3 – Analytics + Insights Page | ⏳ Not started |
| Phase 4 – Profile Management & Upload History | ⏳ Not started |

---

**Last Updated:** April 19, 2025  
**Author:** King Al 👑  
**Project:** MapEm – Soul Meets System

# 📊 MapEm Phase 2 – UI/UX Upgrade Plan

This doc tracks the improvements we're making to the Map View layout, filters, and polish across the system. Each section includes planned upgrades, optional ideas, and current implementation status.

---

## ✅ Step 1 – MapView Layout Overhaul

| Feature                              | Status     | Notes                                  |
|--------------------------------------|------------|----------------------------------------|
| 🧭 Mini top nav bar (tree, filters)  | ✅ Planned | Display tree name, person count       |
| 📊 Floating HUD (pin counts, reset)  | ✅ Planned | Top-right or bottom corner HUD        |
| 🧍 Auto-focus to active person       | ✅ Planned | Zoom in on latest pin on selection    |
| 🎨 Map theme switcher                | ❌ Rejected | Will not implement                    |
| 🧵 Marker hover tooltip              | ⏳ Later   | Save for Phase 3                      |

---

## ✅ Step 2 – Filter Components Refactor

| Feature                              | Status     | Notes                                  |
|--------------------------------------|------------|----------------------------------------|
| 🔄 Clear all filters button          | ✅ Planned | With trash icon                        |
| 🎛 Preset filter dropdown            | ✅ Planned | Save/reload common combos              |
| 📅 Smart year range slider           | ✅ Planned | Dual input or slider                   |
| ⌨️ Keyboard shortcuts (F, R, etc.)    | ✅ Planned | 'F' to toggle filters                  |
| 🔢 Active filter count + tags        | ✅ Planned | Summary like “3 filters applied”       |

---

## ✅ Step 3 – MigrationMap + Legend Polish

| Feature                              | Status     | Notes                                  |
|--------------------------------------|------------|----------------------------------------|
| 🗺️ Floating legend card              | ✅ Planned | Absolute position over map             |
| 🔄 Reset view button                 | ✅ Planned | Top-right corner                       |
| 🌋 Animated marker bounce            | ✅ Planned | On person switch or upload             |
| 👁️ Legend toggle                    | ✅ Planned | Hide/show legend                       |
| 🧊 Map blur when drawer open         | ✅ Planned | Optional visual focus effect           |

---

## ✅ Step 4 – Layout & Spacing Cleanup

| Feature                              | Status     | Notes                                  |
|--------------------------------------|------------|----------------------------------------|
| 🧱 Grid-based layout (2-col at md)   | ✅ Planned | Sidebar + map split                    |
| 🧮 Spacing token audit               | ✅ Planned | Use px-6, gap-6, max-w-6xl, etc.       |
| 📏 Layout variable system            | ✅ Planned | Use `--surface`, `--sidebar-width`, etc. |
| 🌒 Dark mode defaults                | ✅ Done    | Already locked in with design tokens  |
| 🎚️ Responsive sizing + flow tweaks   | ✅ Planned | Apply Tailwind flow/grid improvements |

---

## 🌀 Future Upgrades (Phase 3+)

- 🧬 Tooltip on marker hover
- 🧭 Heatmap overlay for density mapping
- 🧑‍🤝‍🧑 Story mode explorer (migration slideshow)
- 📊 Analytics dashboard map integration
- ✨ Focus mode (minimal map-only view)
- 🎚️ Animations between filter changes

---# 🗺 MapEm Phase 2: Soul Meets System

**Status:** In Progress  
**Owner:** King 👑  
**Focus:** Frontend Layout + Map UX Polishing  
**Theme:** Soulful, Modern, Clean, Intuitive

---

## ✅ STEP 1: MapView Layout Overhaul

### 🎯 Core Tasks
- [ ] Convert MapView layout to grid (`md:grid-cols-[300px_1fr]`)
- [ ] Wrap sidebar content in `<Drawer>` (for responsive filters)
- [ ] Use `<Card>` + `<Button>` from UI kit for all controls

### 🔥 Enhancements (Selected)
- [x] Mini top nav bar (tree name, person count)
- [x] Floating HUD (active filters, reset view)
- [x] Auto-focus to active person pins on select
- [ ] Tooltip-on-hover for markers (future)
- [ ] Map theme switcher (🚫 skipped)

---

## ✅ STEP 2: Filters (Quick + Advanced)

### 🎯 Core Tasks
- [ ] Refactor `QuickFilterBar` with `<Input>`, `<Select>`, `<Button>`
- [ ] Wrap advanced filter sections in `<PanelSection>` blocks
- [ ] Use new `<Drawer>` for advanced filters

### 🔥 Enhancements
- [ ] Add “Clear All” filters button (🗑 icon)
- [ ] Add filter preset dropdown
- [ ] Smart year range with dual sliders
- [ ] Show active filter count
- [ ] Keyboard shortcuts: F (filters), R (reset), H (help)

---

## ✅ STEP 3: Map Polish

### 🎯 Core Tasks
- [ ] Swap in marker clustering in `MigrationMap.jsx`
- [ ] Convert `Legend.jsx` into a floating `<Card>` on top of map
- [ ] Add toggle to hide/show Legend

### 🔥 Enhancements
- [ ] Marker bounce or glow when selected
- [ ] Map blur when drawer is open
- [ ] Cluster glow or pulse
- [ ] Add timeline decade slider (future add-on)

---

## ✅ STEP 4: Layout + Spacing System

### 🎯 Core Tasks
- [ ] Standardize page spacing: `max-w-6xl mx-auto px-6 md:px-12`
- [ ] Replace magic paddings with Tailwind token values
- [ ] Use `gap-6`, `space-y-4`, `py-12` consistently

### 🔥 Enhancements
- [ ] Add layout dev visualizer (optional overlay)
- [ ] Grid snap system for internal layout (optional)
- [ ] Layout tokens: `--sidebar-width`, `--map-padding`
- [ ] Dark/light toggle (future, optional)

---

## 🧩 Bonus Add‑Ons (Optional/Future)
- [ ] “Story Mode” Tree Explorer
- [ ] Analytics heatmap overlay
- [ ] Ghost pins for unresolved locations
- [ ] Full-screen “Focus Mode” map toggle
