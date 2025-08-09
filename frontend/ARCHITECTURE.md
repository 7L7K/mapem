# 🏗️ MapEm Frontend Architecture

## 📁 Project Structure

```
frontend/src/
├── app/                    # Application core
│   ├── main.jsx           # App entry with providers & router
│   ├── Providers.jsx      # Context providers & axios setup
│   └── router.jsx         # Route definitions with lazy loading
├── features/              # Feature-based modules
│   ├── analytics/         # Analytics dashboard
│   ├── dashboard/         # Home/landing page
│   ├── geocode/          # Geocoding management
│   ├── map/              # Interactive mapping
│   ├── people/           # People viewer
│   ├── timeline/         # Timeline visualization
│   ├── tree/             # Tree selection
│   └── upload/           # File upload
├── lib/                   # External integrations
│   └── api/              # API clients & configuration
├── shared/               # Shared utilities & design system
│   ├── components/       # Reusable UI components
│   │   ├── Header/       # Header components
│   │   ├── MapHUD/       # Map overlay components
│   │   └── ui/           # Base design system (17 components)
│   ├── context/          # React contexts (5 providers)
│   ├── hooks/            # Custom React hooks
│   ├── styles/           # CSS & design tokens
│   └── utils/            # Helper functions
└── index.jsx             # React DOM entry point
```

## 🧭 Routing Strategy

**Path-based with lazy loading:**
- `/` → Dashboard
- `/map/:treeId` → Interactive map with URL params
- `/map` → Auto-redirect to latest tree
- `/timeline` → Event timeline
- `/people` → People browser
- `/analytics` → System analytics
- `/upload` → File upload
- `/geocode` → Geocoding admin

## 🎨 Design System

### UI Components (17 total)
- **Interaction**: Button, Drawer, SearchBar, SegmentedNav
- **Display**: Badge, Card, Loader, Spinner, StatusBox
- **Feedback**: ErrorBox, Tooltip, GlowPulse
- **Navigation**: PillNav, TabLink
- **Layout**: PanelSection
- **Data**: Sparkline
- **Utility**: FrameworkToggle

### Design Tokens
```css
Colors: primary, accent, background, surface, text, dim, border, error, success
Fonts: Inter (sans), Chillax (display)
Animations: pulse-glow, fade-in
```

## 🔌 Path Aliases

```javascript
@features/* → src/features/*
@shared/*   → src/shared/*
@components/* → src/shared/components/*
@hooks/*    → src/shared/hooks/*
@context/*  → src/shared/context/*
@utils/*    → src/shared/utils/*
@styles/*   → src/shared/styles/*
@lib/*      → src/lib/*
@app/*      → src/app/*
@api/*      → src/lib/api/*
```

## 🏗️ Feature Slice Pattern

Each feature follows this structure:
```
features/[feature-name]/
├── components/     # Feature-specific components
├── pages/         # Route components
├── hooks/         # Feature-specific hooks (optional)
└── api/           # Feature-specific API calls (optional)
```

## 🔄 State Management

- **Context Providers**: 5 contexts for different concerns
  - `TreeContext` - Tree selection & data
  - `SearchContext` - Search filters & modes
  - `LegendContext` - Map legend state
  - `UploadStatusContext` - Upload progress
  - `MapControlContext` - Map interactions

## 🚀 Performance Features

- **Lazy loading** for all route components
- **Debounced searches** with custom hook
- **Virtualized lists** for large datasets
- **Suspense boundaries** for loading states
- **Error boundaries** for graceful failures

## 🛠️ Development Tools

- **Vite** - Fast build tool with HMR
- **Tailwind CSS v4** - Utility-first styling
- **ESLint** - Code quality & consistency
- **PostCSS** - CSS processing pipeline
- **React Router v6** - Modern routing

## 📦 Key Dependencies

**Core**: React 18, React Router DOM 6, Vite 4
**Styling**: Tailwind CSS 4, Framer Motion
**Data**: Axios, React Table, React Virtual
**Maps**: React Leaflet, Cytoscape
**UI**: Headless UI, Radix Slider, Lucide Icons
