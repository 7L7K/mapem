🧱 MapEm Frontend Overview

Frameworks/Tools:
React (via Vite): Fast component-based rendering
React Router DOM: Handles navigation between views
Tailwind CSS v4.1+: Utility-first CSS framework
PostCSS: Middleware to process Tailwind styles
Vite: Build tool + local dev server (hot reload)
🗂 Project Structure (Frontend)

frontend/
├── index.html               # Main HTML entrypoint
├── index.jsx                # React entry root (renders <App />)
├── App.jsx                  # Wraps all routes + layout
├── postcss.config.cjs       # Tailwind/PostCSS plugin config
├── tailwind.config.js       # Tailwind theme & plugin setup (optional)
├── styles/
│   └── main.css             # Your Tailwind entrypoint + base styles
└── src/
    └── components/
        ├── Header.jsx       # Sticky top nav with logo, tabs, CTA
        ├── Dashboard.jsx    # Home screen view
        ├── Layout.jsx       # Main page wrapper (optional UI shell)
        ├── UploadPanel.jsx  # GEDCOM upload form
        ├── MapView.jsx      # Map rendering with filters
        ├── TreeViewer.jsx   # Tree visualizer (graph/cytoscape)
        ├── PeopleViewer.jsx # List of individuals
        ├── Timeline.jsx     # Timeline view of events
        ├── EventPanel.jsx   # Raw event viewer
        └── ui/              # Reusable UI pieces (Loader, ErrorBox, etc.)
💡 Component Flow Chart

<index.jsx>
   └── <App />
         ├── <Header />      ← always visible, sticky
         ├── <Routes>
         │     ├── "/" → <Dashboard />
         │     ├── "/upload" → <UploadPanel />
         │     ├── "/map" → <MapView />
         │     ├── "/timeline" → <Timeline />
         │     ├── "/people" → <PeopleViewer />
         │     └── etc...
         └── optional: <Layout> wrapper
🌀 Tailwind CSS Flow

main.css  ─▶  PostCSS  ─▶  Tailwind compiler  ─▶  injected into Vite
You load Tailwind in styles/main.css with:
@tailwind base;
@tailwind components;
@tailwind utilities;
Vite finds that file during the build and uses postcss.config.cjs to process it.
All class names in JSX (className="bg-zinc-900 gap-6") are compiled and included in the final bundle.
🧬 What We Fixed So Far (Frontend):


Issue	Fix
🔥 Tailwind CLI not installing	Switched to @tailwindcss/cli
❌ PostCSS config crash	Renamed to postcss.config.cjs for CommonJS
🚫 Tailwind plugin mismatch	Installed @tailwindcss/postcss plugin
😑 Nav links stuck together	Applied flex gap-6 in Header nav
🙅🏽‍♂️ Tailwind not loading	Cleared broken install, reinstalled with proper CLI
😤 Vite hot reload fails	Confirmed main.css is loaded and no config errors
🧪 Visual Debugging Checklist (Now Working ✅)

 Tailwind green block appears
 Header has spacing between links
 Active tab has a bottom border
 Upload button styled with amber background
 Dark background, white text via Tailwind
 No console errors from PostCSS or Vite
🎨 Design System Roadmap (What We Can Add)

Tailwind Theme Customization
Custom color palette (earthTone, sunsetAmber, etc.)
Font setup ('Inter', 'JetBrains Mono')
Extend spacing, borderRadius, shadows
UI Structure
Layout.jsx → slot in sidebars/toolbars
QuickFilterBar, AdvancedDrawer (MapView)
Responsive Design
flex-wrap, md:flex-col, etc. for mobile
Collapse sidebar, burger menu
Reusable Components
<Button />, <Card />, <Section />
Tailwind @apply for DRYness
