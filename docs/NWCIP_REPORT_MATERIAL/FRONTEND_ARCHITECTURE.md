# Frontend Architecture

The NWCIP front‑end is a **React 18** single‑page application built with **Vite** and styled using **Tailwind CSS**. The main entry point is `frontend/src/App.tsx` which sets up routing, authentication context, and the overall layout (navbar + sidebar). 

## Project Structure (relevant files)
```
frontend/src/
├─ App.tsx                 # Root component, Router & AuthProvider
├─ index.tsx               # ReactDOM render
├─ components/             # Re‑usable UI widgets
│   ├─ Navbar.tsx
│   ├─ Sidebar.tsx
│   ├─ ProtectedRoute.tsx   # RBAC guard, uses roles prop
│   ├─ MapView.tsx           # Leaflet map wrapper (see GIS section)
│   └─ …
├─ pages/                  # Route‑level screens
│   ├─ DashboardPage.tsx
│   ├─ InteractiveMapPage.tsx
│   ├─ SpeciesCatalogPage.tsx
│   ├─ SpeciesDetailPage.tsx
│   ├─ AIAssistantPage.tsx
│   └─ …
├─ context/AuthContext.ts   # JWT handling, UserContext
├─ hooks/useAuth.ts        # Helper hook for auth state
├─ services/api.ts          # Thin wrapper around fetch for backend calls
├─ types/                  # TypeScript interfaces that mirror backend Pydantic models
└─ utils/format.ts         # Helper functions for date / number formatting
```

## Routing & Access Control
`App.tsx` defines a **router tree** using `react‑router-dom`. Public routes (`/login`, `/register`) are accessible without a token. All other routes are wrapped in `<ProtectedRoute>` which checks the JWT and, optionally, the required roles (e.g. `['ADMIN']`).

```tsx
<Route element={<ProtectedRoute roles={['RESEARCHER','FOREST_OFFICER','ADMIN','NGO']} />}> 
  <Route path="/assistant" element={<AIAssistantPage />} /> 
  <Route path="/map"       element={<InteractiveMapPage />} /> 
  …
</Route>
```

## State Management
The app uses the **React Context API** (`AuthContext`) to store the current user, JWT token and helper functions (`login`, `logout`). No external state library (Redux, Zustand) is used.

## UI Library & Styling
- **Tailwind CSS** provides utility‑first styling; the dark theme for the map is achieved by custom Tailwind colors (`bg-[#131210]`).
- **Recharts** is used for KPI charts on the dashboard.
- **Lucide React** supplies icons.

## GIS Integration (Leaflet)
`components/MapView.tsx` imports `react‑leaflet` components (`MapContainer`, `TileLayer`, `Marker`, `GeoJSON`). It loads static GeoJSON files (`india‑states.geojson`, `india‑boundary.geojson`) from the backend static folder and renders them. Custom markers are created via `createCustomIcon` which adds a dashed border when `is_fuzzy` is true (sensitive‑species handling).

## Example Code Snippet (Custom Marker)
```tsx
const createCustomIcon = (color = '#10b981', selected = false, isFuzzy = false) => {
  const size = selected ? 18 : 12;
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="background-color:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid #fff;${isFuzzy ? 'border-style:dashed;opacity:0.85;' : ''}"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};
```

## Build & Run
```bash
# install dependencies
npm install
# dev server (http://localhost:3000)
npm run dev
# production build
npm run build
```

All paths and filenames referenced above exist in the repository under `frontend/src/`.


