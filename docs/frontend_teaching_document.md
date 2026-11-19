# NWCIP – Frontend Teaching Guide for **Kiran**

---

## Table of Contents
1. [Frontend Development Fundamentals](#chapter-1-frontend-development-fundamentals)
2. [React](#chapter-2-react)
3. [TypeScript](#chapter-3-typescript)
4. [Vite & Tailwind CSS](#chapter-4-vite-and-tailwind-css)
5. [NWCIP Frontend Architecture](#chapter-5-nwcip-frontend-architecture)
6. [Four User Roles – UI Requirements](#chapter-6-four-user-roles)
7. [Frontend‑Backend Communication](#chapter-7-frontend-and-backend-communication)
8. [Maps and Leaflet Integration](#chapter-8-maps-and-leaflet)
9. [Security & User Experience](#chapter-9-security-and-user-experience)
10. [Practical Project Walk‑through](#chapter-10-practical-project-walkthrough)
11. [Presentation Script (5 min)](#chapter-11-presentation-script)
12. [Viva Questions & Answers](#chapter-12-viva)
13. [Glossary]
14. [Final Revision Sheet]

---

## Chapter 1: Frontend Development Fundamentals {#chapter-1-frontend-development-fundamentals}

### 1.1 What is Front‑end Development?
Frontend development is the discipline that builds the **user‑facing part** of a web application – the HTML structure, CSS styling, and JavaScript behaviour that run **inside the web browser** (Chrome, Edge, Firefox, etc.).  The code you write is downloaded to the client’s device, rendered, and interacted with directly by the user.

### 1.2 Front‑end vs Back‑end
| Aspect | Front‑end | Back‑end |
|--------|-----------|----------|
| Runs on | Browser (client) | Server (cloud VM, container, etc.) |
| Primary languages | HTML, CSS, JavaScript/TypeScript | Python, Go, Java, Node.js, etc. |
| Responsibility | UI, UX, accessibility, responsive layout, client‑side logic | Business logic, data persistence, authentication, APIs |
| Data source | API calls (REST/GraphQL), local storage | Databases, file systems, external services |

### 1.3 Client‑Server Architecture
1. **Client (browser)** sends an HTTP request to a server endpoint.
2. **Server** processes the request, accesses databases, applies business rules, and returns a response (usually JSON).
3. **Client** receives the JSON, updates the UI accordingly.

In NWCIP, the **frontend** (React + Vite) is the client; the **backend** (FastAPI + SQLAlchemy) is the server exposing endpoints such as `POST /observations`.

### 1.4 How a Browser Renders a Website
1. **Parsing** – The browser receives the HTML file and builds the **DOM (Document Object Model)** tree.
2. **CSSOM** – CSS files are parsed into a **CSS Object Model**.
3. **Render Tree** – DOM + CSSOM → a tree of visual elements.
4. **Layout** – Calculates exact positions and sizes for each node.
5. **Paint** – Rasterises each node onto the screen.

During this pipeline, JavaScript can manipulate the DOM (via the **JS engine**) causing **re‑flows** and **re‑paints**.

### 1.5 HTML, CSS & JavaScript Fundamentals
* **HTML** – Mark‑up language defining element hierarchy (`<div>`, `<header>`, `<section>`). Attributes add metadata (`class`, `id`).
* **CSS** – Cascading style sheets describe how elements look (`color`, `margin`, `grid`). The cascade resolves conflicts based on specificity and source order.
* **JavaScript** – Dynamic language that interacts with the DOM (`document.getElementById`), makes network calls (`fetch`), and holds application state.

### 1.6 What is a Single‑Page Application (SPA)?
An SPA loads a **single HTML page** once and then dynamically updates the view via JavaScript routing. Navigation between “pages” does **not** trigger a full‑page reload; instead the router swaps components, improving perceived performance and enabling richer interactions.

### 1.7 How React Fits In
React is a **UI library** that makes building SPAs simpler by:
* Declaring UI with **JSX** (HTML‑like syntax inside JavaScript).
* Managing UI state with **hooks** (`useState`, `useEffect`).
* Providing a **virtual DOM** – a lightweight copy of the real DOM. When state changes, React calculates the minimal set of actual DOM updates, leading to efficient re‑rendering.

---

## Chapter 2: React {#chapter-2-react}

### 2.1 What is React?
React (by Facebook) is a **JavaScript library** for building component‑based user interfaces. It encourages a **declarative** style – you describe *what* the UI should look like for a given state, and React renders it.

### 2.2 Components & Reusable Components
A **component** is a self‑contained piece of UI with its own markup, styling, and behaviour. Components can be **re‑used** throughout the app, reducing duplication.

#### Example: `Navbar.tsx`
```tsx
// src/components/Navbar.tsx
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const Navbar = () => {
  const { user, logout } = useAuth();
  return (
    <nav className="bg-green-800 text-white p-4 flex justify-between items-center">
      <Link to="/" className="font-bold text-xl">NWCIP</Link>
      <div>
        {user ? (
          <button onClick={logout} className="ml-4">Logout</button>
        ) : (
          <Link to="/login" className="ml-4">Login</Link>
        )}
      </div>
    </nav>
  );
};
```
**Line‑by‑line explanation**
1. `import { Link } …` – pulls in React‑Router’s `Link` component for client‑side navigation.
2. `useAuth` – a custom hook (see `src/hooks/useAuth.ts`) that provides the current user and a logout function.
3. `const { user, logout } = useAuth();` – destructuring the hook’s return value.
4. JSX starts with `<nav>` – a semantic HTML5 element styled via Tailwind classes.
5. `Link to="/"` renders an anchor that navigates to the home route without a page reload.
6. Conditional rendering (`{user ? … : …}`) shows *Logout* when a user is logged in and *Login* otherwise.

### 2.3 Functional Components
React components can be written as **functions** (preferred) or as class components (legacy). A functional component is simply a JavaScript function that returns JSX.
```tsx
const Greeting = ({ name }: { name: string }) => <h2>Hello, {name}!</h2>;
```
The parameter `{ name }` is a **prop** – data passed from a parent component.

### 2.4 JSX
JSX (JavaScript XML) lets you write HTML‑like markup inside JavaScript. Under the hood, Babel transpiles JSX to `React.createElement` calls.
```tsx
// JSX
<div className="p-2">{message}</div>

// Transpiled (simplified)
React.createElement('div', { className: 'p-2' }, message);
```
Key points:
* Use **className** instead of class (reserved word).
* Curly braces `{}` embed JavaScript expressions.

### 2.5 Props
Props are **read‑only** inputs to a component.
```tsx
type CardProps = { title: string; count: number };
const StatCard = ({ title, count }: CardProps) => (
  <div className="border rounded p-4">
    <h3>{title}</h3>
    <p className="text-2xl">{count}</p>
  </div>
);
```
> **Why read‑only?** – So a child cannot accidentally change data that belongs to its parent, preserving a **unidirectional data flow**.

### 2.6 State & `useState`
State is mutable data that lives **inside** a component. `useState` returns a **state variable** and a **setter**.
```tsx
const Counter = () => {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount(count + 1)}>Clicked {count} times</button>
  );
};
```
* `count` – current value.
* `setCount` – function that schedules a re‑render with the new value.

### 2.7 `useEffect`
`useEffect` runs side‑effects after render (e.g., fetching data, subscribing to events).
```tsx
useEffect(() => {
  // fetch sightings for the logged‑in officer
  api.get('/observations?officerId=' + user.id)
    .then(res => setObservations(res.data))
    .catch(err => console.error(err));
}, [user.id]); // dependency array – runs when user.id changes
```
* The **cleanup** function (return value) runs before the effect re‑executes or when the component unmounts.

### 2.8 Event Handling
React normalises DOM events. Event handlers receive a **SyntheticEvent** object.
```tsx
<input type="text" onChange={e => setSearch(e.target.value)} />
```
* `e.target.value` – the current value of the input field.

### 2.9 Conditional Rendering
Use JavaScript operators inside JSX.
```tsx
{isLoading ? <Spinner /> : <DataTable data={data} />}
```
* Ternary operator renders a **spinner** while data loads.

### 2.10 Lists & Keys
When rendering an array, each element needs a **key** for React to identify it.
```tsx
<ul>
  {species.map(s => (
    <li key={s.id}>{s.common_name}</li>
  ))}
</ul>
```
* Keys should be **stable** (e.g., database IDs) not indexes.

### 2.11 Component Lifecycle Concepts (via Hooks)
| Phase | Hook(s) | Typical Use |
|-------|----------|--------------|
| Mount | `useEffect(() => …, [])` | Fetch initial data, subscribe to events |
| Update | `useEffect(() => …, [deps])` | React to prop or state changes |
| Unmount | Return cleanup from `useEffect` | Remove listeners, cancel timers |

### 2.12 Routing & Protected Routes
React‑Router (`react-router-dom`) provides `<Routes>` and `<Route>`.
```tsx
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route element={<ProtectedRoute allowedRoles={["Officer", "Admin"]} />}>
    <Route path="/officer" element={<OfficerDashboardPage />} />
    <Route path="/admin" element={<AdminPage />} />
  </Route>
</Routes>
```
`ProtectedRoute` (found in `src/components/ProtectedRoute.tsx`) checks authentication and role, redirecting to `/login` if the user lacks permission.

### 2.13 Component Hierarchy (Simplified)
```
App
├─ Navbar
├─ Sidebar (role‑based)
├─ Routes
│   ├─ LoginPage
│   ├─ RegisterPage
│   ├─ DashboardPage (generic wrapper)
│   │   ├─ GeneralPublicDashboard
│   │   ├─ ResearcherDashboard
│   │   ├─ OfficerDashboard
│   │   └─ AdminDashboard
│   └─ … (Other pages)
└─ Footer (optional)
```
---

## Chapter 3: TypeScript {#chapter-3-typescript}

### 3.1 JavaScript vs TypeScript
* **JavaScript** – dynamically typed, interpreted.
* **TypeScript** – a superset that adds **static type annotations** which are stripped away at compile‑time.

Benefits in a large project like NWCIP:
* Early detection of bugs (e.g., passing a string where a number is expected).
* Autocompletion & IDE assistance.
* Clear contracts for API responses.

### 3.2 Variables and Data Types
```ts
let count: number = 0;          // mutable
const PI: readonly number = 3.14; // immutable (const) + explicit
let name?: string;               // optional variable (may be undefined)
```

### 3.3 Interfaces
```ts
export interface Species {
  id: number;
  scientific_name: string;
  common_name: string;
  image_url?: string; // optional field
}
```
* Interfaces describe **shape** of objects; they are used for props and API data.

### 3.4 Type Aliases
```ts
type ID = number | string;
type ApiResponse<T> = { data: T; error?: string };
```
* Useful for reusable generic structures.

### 3.5 Functions and Parameters
```ts
function sum(a: number, b: number): number {
  return a + b;
}

const multiply = (a: number, b: number): number => a * b;
```
* Parameter types and return type are explicit.

### 3.6 Optional Properties
```ts
interface ObservationPayload {
  species_id: number;
  location_id: number;
  description?: string; // may be omitted by the client
}
```
When the payload is sent with `fetch`, the request body is typed as `ObservationPayload` ensuring compile‑time safety.

### 3.7 API Response Typing
```ts
// src/types/index.ts
export interface Observation {
  id: number;
  species_id: number;
  location_id: number;
  submitted_by_user_id: number;
  observed_at: string; // ISO‑8601 string
  notes?: string;
}

export type ObservationResponse = ApiResponse<Observation>;
```
The `api.ts` service will return a `Promise<ObservationResponse>` so callers can rely on the shape.

---

## Chapter 4: Vite and Tailwind CSS {#chapter-4-vite-and-tailwind-css}

### 4.1 What Vite Does
Vite is a **next‑generation frontend build tool** that:
* Serves source files via native ES modules during development (instant hot‑module reload).
* Bundles production assets with **esbuild** (fast) and **Rollup** (optimised output).
* Generates a **`dist/`** folder containing minified JS, CSS, and hashed assets ready for deployment.

### 4.2 Development Server vs Production Build
* `npm run dev` (or `vite`) → launches a dev server at `http://localhost:5173` with live reload.
* `npm run build` → produces static assets in `dist/` for a web server (nginx in this project).

### 4.3 npm & `package.json`
* `package.json` lists **dependencies** (runtime) and **devDependencies** (build tools). Example snippet:
```json
"dependencies": {
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.14.0",
  "axios": "^1.6.0",
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.0"
},
"devDependencies": {
  "vite": "^5.0.0",
  "typescript": "^5.2.2",
  "tailwindcss": "^3.3.3"
}
```

### 4.4 What Tailwind CSS Is
Tailwind is a **utility‑first CSS framework**. Instead of writing custom CSS classes, you compose small utility classes directly in the markup.
```tsx
<div className="bg-emerald-100 text-gray-800 p-4 rounded-lg shadow-md">
  {/* content */}
</div>
```
* No separate stylesheet needed for most UI; design is expressed declaratively.

### 4.5 Responsive Layouts with Tailwind
Tailwind’s breakpoint prefixes (`sm:`, `md:`, `lg:`, `xl:`) apply utilities at specific viewport widths.
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* cards */}
</div>
```
* On mobile (`grid-cols-1`) → one column, on tablet (`md:grid-cols-2`) two columns, on desktop (`lg:grid-cols-4`) four columns.

### 4.6 Flexbox & CSS Grid via Tailwind
* **Flexbox** – `flex`, `items-center`, `justify-between`.
* **Grid** – `grid`, `grid-cols-3`, `gap-2`.
Both are composable utilities that eliminate the need for custom CSS files.

### 4.7 Styling Reusable Components
When creating a component (e.g., `StatCard`), you can expose **className props** to allow callers to extend styling.
```tsx
export const StatCard = ({ title, count, className }: CardProps) => (
  <div className={`border rounded p-4 ${className}`}>/* ... */</div>
);
```
---

## Chapter 5: NWCIP Frontend Architecture {#chapter-5-nwcip-frontend-architecture}

### 5.1 Directory Overview (as of *this* repository)
```
frontend/
│   package.json
│   vite.config.ts
│   tailwind.config.js
│   tsconfig.json
│   index.html
│
├─ public/               # static assets served as‑is
│   ├─ chital-deer-bg.jpg
│   └─ login-bg.jpg
│
├─ src/
│   ├─ main.tsx               # React entry point, mounts <App />
│   ├─ App.tsx                # Top‑level component, sets up router & context
│   ├─ index.css              # Tailwind base import
│   │
│   ├─ components/            # Re‑usable UI pieces
│   │   ├─ Navbar.tsx
│   │   ├─ Sidebar.tsx
│   │   ├─ ProtectedRoute.tsx
│   │   ├─ MapView.tsx
│   │   └─ (many others)…
│   │
│   ├─ pages/                 # One component per *route*
│   │   ├─ LoginPage.tsx
│   │   ├─ RegisterPage.tsx
│   │   ├─ OfficerDashboardPage.tsx
│   │   ├─ ResearcherDashboardPage.tsx
│   │   ├─ AdminPage.tsx
│   │   └─ …
│   │
│   ├─ context/               # React Context providers
│   │   └─ AuthContext.tsx      # Holds JWT, user object, login/logout helpers
│   │
│   ├─ hooks/                 # Custom reusable hooks
│   │   └─ useAuth.ts          # Wrapper around AuthContext
│   │
│   ├─ services/              # API wrapper (Axios instance)
│   │   └─ api.ts
│   │
│   ├─ types/                 # Shared TypeScript interfaces
│   │   └─ index.ts
│   │
│   └─ utils/                 # Helper functions (date formatting, etc.)
```

### 5.2 How the Pages Connect
* `main.tsx` renders `<App />` inside `<BrowserRouter>` (React‑Router).
* `<App />` provides `<AuthContext.Provider>` and defines the `<Routes>` tree.
* Each route loads a **page component** (`LoginPage`, `OfficerDashboardPage`, …).
* Page components import **shared UI components** (cards, tables, maps) and **services** (`api.get('/observations')`).

### 5.3 Core UI Elements
| Element | File | Purpose |
|---------|------|----------|
| `Navbar.tsx` | `src/components/Navbar.tsx` | Top navigation bar with brand, login/logout button |
| `Sidebar.tsx` | `src/components/Sidebar.tsx` | Role‑based side navigation (links differ per role) |
| `ProtectedRoute.tsx` | `src/components/ProtectedRoute.tsx` | Guard routes – redirects unauthenticated users |
| `MapView.tsx` | `src/components/MapView.tsx` | Wrapper around **react‑leaflet** displaying GIS layers |
| `StatCard.tsx` | `src/components/StatCard.tsx` | Shows numeric KPI values (e.g., total sightings) |
| `Alert.tsx` | `src/components/Alert.tsx` | Toast‑style feedback for success / error |

### 5.4 Role‑Based Interface Logic
* `AuthContext` stores `user.role` (one of `Public`, `Researcher`, `Officer`, `Admin`).
* `Sidebar` reads the role and renders a different set of `<NavLink>` items.
* `ProtectedRoute` receives `allowedRoles` prop – if the current user’s role is not in the list, it navigates to `/login`.
* Example (excerpt from `Sidebar.tsx`):
```tsx
const links = {
  Public: [ {to: '/', label: 'Home'}, {to: '/species', label: 'Species'} ],
  Researcher: [ {to: '/research', label: 'Research Dashboard'}, {to: '/documents', label: 'Documents'} ],
  Officer: [ {to: '/field', label: 'Field Dashboard'}, {to: '/map', label: 'Spatial Map'} ],
  Admin: [ {to: '/admin/users', label: 'User Management'}, {to: '/admin/analytics', label: 'Platform Analytics'} ],
};
return (
  <nav>
    {links[user.role].map(l => (
      <NavLink key={l.to} to={l.to}>{l.label}</NavLink>
    ))}
  </nav>
);
```
---

## Chapter 6: Four User Roles – UI Requirements {#chapter-6-four-user-roles}

### 6.1 General Public (Educational Portal)
* **Goal** – Provide wildlife knowledge, species catalog, static maps, news feed.
* **Pages** – `Home`, `SpeciesCatalogPage`, `SpeciesDetailPage`, `InteractiveMapPage`, `NewsPage`.
* **Key UI** – Card grid of species, filter/search bar, map with protected‑area overlays, no edit/delete actions.
* **Why separate?** – No need for authentication, lower security surface, read‑only data.

### 6.2 Researcher (Investigator Dashboard)
* **Goal** – Submit research documents, view analytics, use AI assistant.
* **Pages** – `ResearcherDashboardPage`, `DocumentsPage`, `MySubmissionsPage`, `AIAssistantPage`.
* **Key UI** – Data tables with pagination, document upload modal, chart components (`recharts`) showing trends, NLP summary box.
* **Why separate?** – Requires access to **research‑only APIs** (`/documents`, `/analysis`) and higher quota.

### 6.3 Forest Officer (Operational Dashboard)
* **Goal** – Record field observations, monitor alerts, view GIS layers.
* **Pages** – `OfficerDashboardPage`, `SubmitSightingPage`, `AlertsPage`, `InteractiveMapPage` (with draw tools).
* **Key UI** – Form with required fields (species, location, photo upload), map for pinpointing GPS, real‑time alert list, quick status badges.
* **Why separate?** – Must enforce **field‑level permissions**, disallow access to research data, and log actions for audit.

### 6.4 Administrator (Governance Dashboard)
* **Goal** – Manage users, assign roles, monitor system health.
* **Pages** – `AdminPage`, `AdminPlatformPage`, `UserManagementPage`, `AuditLogsPage`.
* **Key UI** – Table of users with role‑dropdown editors, platform usage charts, log viewer with filters.
* **Why separate?** – Highest privilege; UI must hide all edit actions from lower‑privilege users.

---

## Chapter 7: Frontend‑Backend Communication {#chapter-7-frontend-and-backend-communication}

### 7.1 What is an API?
An **Application Programming Interface** is a contract that defines how a client can interact with a server over HTTP. NWCIP uses **RESTful JSON APIs**.

### 7.2 HTTP Methods
| Method | Meaning | Typical Use in NWCIP |
|--------|---------|-----------------------|
| GET | Retrieve data | `GET /species`, `GET /observations?officerId=5` |
| POST | Create new resource | `POST /observations` (field report) |
| PUT | Replace entire resource | `PUT /users/12` (admin updates user) |
| PATCH | Partial update | `PATCH /users/12/role` (role change) |
| DELETE | Remove | `DELETE /observations/45` (admin only) |

### 7.3 JSON Payload Example (Create Observation)
**Request** (`POST /observations`)
```json
{
  "species_id": 3,
  "location_id": 12,
  "observed_at": "2026-11-15T14:20:00Z",
  "description": "Lone Chital near waterhole",
  "photo_url": "https://s3.amazonaws.com/nwcip/uploads/obs123.jpg"
}
```
**Response** (`200 OK`)
```json
{
  "data": {
    "id": 124,
    "species_id": 3,
    "location_id": 12,
    "submitted_by_user_id": 7,
    "observed_at": "2026-11-15T14:20:00Z",
    "description": "Lone Chital near waterhole",
    "photo_url": "https://s3.amazonaws.com/nwcip/uploads/obs123.jpg"
  }
}
```

### 7.4 `api.ts` – Centralised Axios Instance
```ts
// src/services/api.ts
import axios from 'axios';
import { useAuth } from '../hooks/useAuth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Attach Authorization header to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
```
* `import.meta.env` – Vite environment variables.
* Interceptor adds **JWT** token automatically.

### 7.5 Example: Officer Submits an Incident
```tsx
// src/pages/SubmitSightingPage.tsx
import { useState } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

export const SubmitSightingPage = () => {
  const { user } = useAuth();
  const [payload, setPayload] = useState({ species_id: 0, location_id: 0, description: '' });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    try {
      const res = await api.post('/observations', {
        ...payload,
        submitted_by_user_id: user.id,
        observed_at: new Date().toISOString(),
      });
      console.log('saved', res.data);
      setStatus('success');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-lg mx-auto p-4">
      {/* Form fields with onChange updating payload */}
      <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded" disabled={status==='loading'}>
        {status === 'loading' ? 'Submitting…' : 'Submit Observation'}
      </button>
      {status === 'success' && <p className="text-green-500 mt-2">Observation saved!</p>}
      {status === 'error' && <p className="text-red-500 mt-2">Failed to save. Try again.</p>}
    </form>
  );
};
```
**Explanation of critical lines**
* `useAuth()` gives the logged‑in officer’s `user.id`.
* `api.post('/observations', …)` triggers the HTTP request defined in **Section 7.4**.
* The JWT token (stored in `localStorage`) is automatically added by the interceptor.
* UI shows loading state, success or error messages.

### 7.6 Loading States & Error Handling
* Set local state (`status`) to control UI feedback.
* Use a **global error interceptor** (in `api.ts`) to catch 401/403 and redirect to `/login`.
* Show toast messages via an `Alert` component for non‑blocking feedback.

---

## Chapter 8: Maps and Leaflet {#chapter-8-maps-and-leaflet}

### 8.1 What is GIS?
**Geographic Information System** – a framework for capturing, storing, analyzing, and visualizing spatial data (coordinates, shapes, layers).

### 8.2 Leaflet Overview
Leaflet is a lightweight, open‑source JavaScript library for interactive maps. It works well with **React‑Leaflet**, a set of React components.

### 8.3 Core Leaflet Concepts
| Concept | Description |
|---------|-------------|
| **Map** | Container that displays tiles and layers.
| **Tile Layer** | Raster images (e.g., OpenStreetMap) that make up the base map.
| **Marker** | Pin at a specific latitude/longitude.
| **Popup** | Small overlay that appears when a marker is clicked.
| **Layer Control** | UI to toggle overlays (e.g., protected‑area polygons).

### 8.4 Example Component – `MapView.tsx`
```tsx
// src/components/MapView.tsx
import { MapContainer, TileLayer, Marker, Popup, LayersControl, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';
import api from '../services/api';

export const MapView = () => {
  const [protectedAreas, setProtectedAreas] = useState<any[]>([]);

  useEffect(() => {
    // Load GeoJSON polygon data from backend (or static file)
    api.get('/geo/protected_areas').then(res => setProtectedAreas(res.data));
  }, []);

  return (
    <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: '600px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap contributors"
      />
      <LayersControl position="topright">
        {protectedAreas.map((area, i) => (
          <LayersControl.Overlay key={i} name={area.name} checked>
            <GeoJSON data={area.geometry} style={{ color: '#2b6d32', weight: 2 }} />
          </LayersControl.Overlay>
        ))}
      </LayersControl>
    </MapContainer>
  );
};
```
**Explanation**
1. `MapContainer` creates the actual Leaflet map with initial centre over India.
2. `TileLayer` loads OpenStreetMap tiles – free, no API key.
3. `useEffect` fetches GeoJSON polygons representing protected areas (backend endpoint `/geo/protected_areas`).
4. For each area, a `<GeoJSON>` component draws the polygon with a green stroke.
5. `LayersControl` allows the user to toggle the visibility of each area.

### 8.5 How Data Flows
* Backend stores geometry in a **PostGIS** column (`geometry_geojson`).
* Endpoint `/geo/protected_areas` returns an array of `{ id, name, geometry }`.
* Frontend receives JSON, passes to `GeoJSON` component which renders directly.

---

## Chapter 9: Security and User Experience {#chapter-9-security-and-user-experience}

### 9.1 Authentication vs Authorization
* **Authentication** – Verifies identity (login). Implemented via **JWT**. The token is stored in `localStorage` and attached to every request.
* **Authorization** – Determines what an authenticated user may do (role‑based access). Enforced in `ProtectedRoute` and UI conditionals.

### 9.2 Why Hiding a Button Is Not Security
A button hidden via CSS (`display:none`) can still be triggered by a crafted request. Real security must be enforced **server‑side** (e.g., the `/observations` POST endpoint checks the user’s role).

### 9.3 Protected Routes (Implementation Recap)
```tsx
// src/components/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Props { allowedRoles: string[]; }
export const ProtectedRoute = ({ allowedRoles }: Props) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(user.role)) return <Navigate to="/unauthorized" replace />;
  return <Outlet />; // renders child route component
};
```
* `Outlet` renders the nested route only when checks pass.

### 9.4 Form Validation
* **Client‑side** – using HTML attributes (`required`, `pattern`) and custom React validation (e.g., checking that a latitude is between –90 and 90).
* **Server‑side** – FastAPI pydantic models validate payloads; the frontend must handle validation errors returned as `422 Unprocessable Entity`.

### 9.5 Responsive Design
Tailwind’s breakpoints (`sm`, `md`, `lg`) ensure the UI re‑flows on mobile, tablet, and desktop. Example: the dashboard grid switches from a single column on mobile to a 3‑column layout on wide screens.

### 9.6 Accessibility (a11y)
* Use **semantic HTML** (`<nav>`, `<main>`, `<button>`).
* Provide **ARIA labels** for custom components (e.g., `<button aria-label="Close map popup">`).
* Ensure colour contrast meets WCAG AA (green text on white background may need darkening).

### 9.7 Error & Empty States
* When an API returns `[]`, display a friendly message (“No observations recorded yet”).
* Global error boundary component catches rendering errors and shows a fallback UI.

---

## Chapter 10: Practical Project Walk‑through {#chapter-10-practical-project-walkthrough}

### 10.1 Prerequisites
* Node ≥ 20, npm ≥ 10 installed.
* Backend server running (`uvicorn backend.app.main:app --port 8000`).
* Frontend dev server started: `npm run dev` (Vite runs at `http://localhost:5173`).

### 10.2 Step‑by‑Step Demonstration
1. **Open Browser** → navigate to `http://localhost:5173`.
2. **Login** – click *Login* in the navbar, fill the demo credentials (`officer@example.com / password`). Show that the sidebar now displays Officer‑specific links.
3. **Navigate to “Field Observation”** – click the link. Explain the form fields (species selector, map location picker, description, optional photo).
4. **Submit a new observation** – fill dummy data, click *Submit*. Observe the loading spinner, then success message.
5. **Open Developer Tools (F12)** – go to the *Network* tab, filter by `observations`. Show the `POST` request with JSON payload and the JWT `Authorization` header.
6. **Check the Map** – go to *Explore Spatial Map* from the Public role (log out first). Demonstrate zooming, toggling protected‑area layers, and clicking a marker to view a popup.
7. **Show a protected route failure** – while logged out, attempt to navigate directly to `/officer`. The app redirects to `/login`.
8. **Trigger an error** – disconnect the backend, click *Submit Observation* again, and show the error toast (“Failed to save”).
9. **Responsive test** – resize the browser window; note how the dashboard cards stack vertically on narrow screens.

### 10.3 Common Debugging Tips
* **Blank page** – check the console for syntax errors; Vite will display the error overlay.
* **CORS issues** – ensure the backend includes `Access-Control-Allow-Origin: *` during development (FastAPI `CORSMiddleware`).
* **Missing token** – look at `localStorage` (DevTools → Application → Local Storage) for `access_token`.
* **Incorrect role mapping** – verify `user.role` in the AuthContext state.

---

## Chapter 11: Presentation Script (≈ 5 min) {#chapter-11-presentation-script}

> **Speaker:** *Kiran – Frontend Lead*

1. **Opening (30 s)**
   *“Good afternoon. I am Kiran, responsible for the user interface of the National Wildlife Conservation Intelligence Platform, NWCIP.”*
2. **Problem Statement (45 s)**
   *“Conservation officers, researchers, and the public need a single, intuitive portal to access real‑time wildlife data, submit field observations, and analyse trends.”*
3. **Technology Stack (45 s)**
   *“We built the frontend as a **Single‑Page Application** using **React** on top of **Vite**, written in **TypeScript**, and styled with **Tailwind CSS**. The map visualisation relies on **Leaflet** via **react‑leaflet**.”*
4. **Architecture Overview (60 s)**
   *“The app follows a clean component hierarchy: `App` provides routing and authentication context; a role‑aware `Sidebar` renders navigation; each route loads a page component that composes reusable UI widgets (cards, tables, maps). All API calls go through a central Axios instance that automatically attaches the JWT token.”*
5. **Key Features Demonstration (90 s)** – (live demo)
   *Login as a Forest Officer, submit an observation – show form, loading state, success toast.*
   *Switch to Public view, open the interactive map – toggle protected‑area layers, click a marker.*
   *Navigate to the Researcher dashboard – display a chart built with Recharts.*
6. **Security & Role‑Based UI (30 s)**
   *“We enforce authentication via JWT, and every protected route checks the user’s role. The server also validates the role, so UI hiding alone is not enough.”*
7. **Performance & UX (30 s)**
   *“Vite gives us sub‑second hot reload. Tailwind’s utility classes keep CSS bundle under 50 KB. Lazy‑loaded map tiles ensure smooth scrolling.”*
8. **Closing (30 s)**
   *“In summary, the frontend provides a fast, responsive, and secure experience for all stakeholder groups, enabling better wildlife conservation decisions.”*

---

## Chapter 12: Viva Questions & Answers {#chapter-12-viva}
### Basic (1‑10)
1. **What is the virtual DOM and why does React use it?**
   *Answer:* React keeps an in‑memory copy of the DOM. When state changes, it diffs the virtual DOM against the previous one, calculates the minimal set of real DOM updates, and applies them. This avoids costly full re‑paints and results in faster UI updates.
2. **Explain the purpose of `useEffect` with an empty dependency array.**
   *Answer:* It runs once after the component mounts (similar to `componentDidMount`), ideal for one‑time data fetching or subscribing to events.
3. **How does TypeScript improve reliability in a React project?**
   *Answer:* It catches mismatched prop types, missing fields in API responses, and incorrect function signatures at compile time, preventing many runtime errors.
4. **What does the `protected` attribute in `ProtectedRoute` do?**
   *Answer:* It checks whether a user is authenticated and whether their role is listed in `allowedRoles`. If not, it redirects to `/login` or `/unauthorized`.
5. **Describe how Tailwind’s utility‑first approach differs from traditional CSS.**
   *Answer:* Instead of writing custom class selectors, you compose small, single‑purpose utility classes directly in markup, which reduces the amount of separate CSS code and promotes design consistency.
6. **What is the role of `vite.config.ts`?**
   *Answer:* It configures Vite’s plugins (e.g., React Refresh, environment variables), alias paths, and the development server proxy to forward `/api` calls to the backend.
7. **How does the application store the JWT token, and why is that location chosen?**
   *Answer:* The token is stored in `localStorage`. This persists across page reloads and tabs, making it easy for the Axios interceptor to read it on every request.
8. **When would you use `PATCH` instead of `PUT`?**
   *Answer:* `PATCH` updates only specific fields (partial update), while `PUT` replaces the entire resource. For role changes (`PATCH /users/12/role`) we use PATCH.
9. **Explain the flow of a field‑observation submission from UI to database.**
   *Answer:* User fills the form → component calls `api.post('/observations')` → Axios adds JWT → FastAPI endpoint validates the payload, extracts `user.id` from token, creates a new `Observation` row via SQLAlchemy, commits, returns JSON → frontend shows success toast.
10. **What is a CORS error and how is it solved in this project?**
    *Answer:* Cross‑Origin Resource Sharing blocks browsers from calling a different origin without proper headers. The backend registers `CORSMiddleware` with `allow_origins=['*']` during development, allowing the Vite dev server to communicate.

### Intermediate (11‑20)
11. **How does `react‑leaflet` connect Leaflet’s map to React’s lifecycle?**
    *Answer:* `react‑leaflet` provides React components (`MapContainer`, `TileLayer`, `Marker`) that internally create Leaflet instances on mount and clean them up on unmount, syncing props to Leaflet options.
12. **What is the purpose of `useAuth` hook?**
    *Answer:* It abstracts interaction with `AuthContext`, exposing `user`, `login`, `logout`, and token refresh logic to any component.
13. **Why is it important to include a cleanup function in `useEffect`?**
    *Answer:* To avoid memory leaks (e.g., lingering WebSocket listeners) and to stop timers when the component unmounts.
14. **Explain how role‑based navigation is generated dynamically.**
    *Answer:* `Sidebar` reads `user.role` from context, selects the appropriate link array, and maps each to a `<NavLink>`. Adding a new role only requires extending the `links` map.
15. **What are “keys” in a React list and why must they be stable?**
    *Answer:* Keys uniquely identify list items for React’s diffing algorithm. Stable keys (e.g., database IDs) prevent items from being incorrectly reordered or losing state.
16. **How does the Axios interceptor handle token expiration?**
    *Answer:* It can intercept a `401` response, clear stored token, and optionally redirect to `/login`. In this project, the interceptor logs out the user on 401.
17. **Describe how the `MapView` component fetches GeoJSON data and renders it.**
    *Answer:* On mount, `useEffect` calls `api.get('/geo/protected_areas')`. The response (array of GeoJSON objects) is stored in state and passed to `<GeoJSON>` components, which draw the polygons.
18. **What is the difference between `GET /observations` and `GET /observations?officerId=5`?**
    *Answer:* The former returns all observations (admin only). The latter filters by `officerId` and is used by officers to view their own reports.
19. **How would you add server‑side pagination to the observations table?**
    *Answer:* Backend would accept `?skip=0&limit=20`. Frontend calls `api.get('/observations', { params: { skip, limit } })`, stores `totalCount`, and renders pagination controls that update `skip`.
20. **Explain the purpose of `process.env` vs `import.meta.env` in Vite.**
    *Answer:* `process.env` is Node’s environment during build time. Vite injects variables prefixed with `VITE_` into `import.meta.env` for use in client code. The two are not interchangeable.

### Advanced (21‑30)
21. **How does the JWT validation flow differ between client and server?**
    *Answer:* Client trusts the token’s presence and includes it in the Authorization header. Server verifies the signature, expiry, and claims (e.g., role) before granting access.
22. **If you wanted to cache API responses on the client, which strategy would you use?**
    *Answer:* Use a library such as **React Query** (not currently in the project) for stale‑while‑revalidate caching, or implement a simple in‑memory cache keyed by request URL.
23. **What would be the impact of moving from `axios` to the native `fetch` API?**
    *Answer:* `fetch` reduces bundle size but lacks built‑in request interceptors, requiring manual header injection. Error handling is also more verbose because non‑2xx responses don’t throw.
24. **How can you optimise the bundle size of the Tailwind build?**
    *Answer:* Enable `purge` (content paths) in `tailwind.config.js` so unused utilities are removed in production. Also use `@layer utilities` for custom classes.
25. **Explain how you would implement localisation (i18n) for the NWCIP UI.**
    *Answer:* Introduce a library like **react‑i18next**, store translation JSON files per language, wrap UI strings with the `t()` function, and switch language via context.
26. **Describe a method to unit‑test a React component that uses `useAuth`.**
    *Answer:* Wrap the component in a mock `AuthContext.Provider` supplying a fake user object, then render with **Testing Library** and assert UI based on role.
27. **What security considerations should be taken when uploading photos for observations?**
    *Answer:* Validate file type and size client‑side, enforce virus scanning on the server, store images in a secure bucket with signed URLs, and never expose the original file path.
28. **How would you add real‑time updates for new observations on the officer dashboard?**
    *Answer:* Use **WebSocket** (e.g., FastAPI’s `WebSocket` endpoint) and a React hook that opens a socket, listens for `observation_created` events, and updates state accordingly.
29. **If the map becomes unresponsive on low‑end devices, what optimisation steps would you take?**
    *Answer:* Reduce the number of rendered markers (cluster them with `leaflet.markercluster`), simplify GeoJSON geometry, lazy‑load the map component, and limit max zoom levels.
30. **Explain how you would perform a security audit of the frontend code.**
    *Answer:* Review token storage, ensure all API calls are over HTTPS, verify role checks both client‑side and server‑side, run static analysis (e.g., `npm audit`), check third‑party dependencies for known vulnerabilities, and test for XSS via user‑generated content.

---

## Glossary
| Term | Definition |
|------|------------|
| **SPA** | Single‑Page Application – a web app that loads a single HTML page and dynamically updates the UI.
| **JSX** | JavaScript XML – syntax extension allowing HTML‑like code inside JavaScript.
| **Hook** | A special function (`useState`, `useEffect`, custom hooks) that lets functional components have state and side‑effects.
| **JWT** | JSON Web Token – a signed token containing claims, used for stateless authentication.
| **CORS** | Cross‑Origin Resource Sharing – browser security mechanism that restricts AJAX requests to other origins.
| **Tailwind** | Utility‑first CSS framework; classes are composable directly in markup.
| **Vite** | Build tool that serves modules natively during development and bundles for production.
| **Leaflet** | Open‑source JavaScript library for interactive maps.
| **Role‑Based Access Control (RBAC)** | Permission model where each user is assigned a role that determines allowed actions.
| **GeoJSON** | JSON format for encoding geographic features (points, lines, polygons).
| **Axios** | Promise‑based HTTP client for the browser.
| **ProtectedRoute** | React‑Router component that guards a route based on authentication/authorization.
| **Context API** | React feature to share data (e.g., auth state) across the component tree without prop‑drilling.
| **Responsive** | Design that adapts layout to different viewport sizes.
| **Accessibility (a11y)** | Practices ensuring UI can be used by people with disabilities.

---

## Final Revision Sheet
| Topic | Key Points to Remember |
|-------|------------------------|
| **React Core** | Virtual DOM, functional components, hooks (`useState`, `useEffect`), JSX, component hierarchy.
| **Routing** | `<Routes>`, `<Route>`, `<ProtectedRoute>`, role‑based `allowedRoles`.
| **State Management** | Local component state, context (`AuthContext`), lifting state up when needed.
| **TypeScript** | Interfaces for API models, type safety on props, generic `ApiResponse<T>`.
| **Vite** | `npm run dev` (hot reload), `npm run build` (production), proxy config for `/api`.
| **Tailwind** | Utility classes, breakpoints (`sm:`, `md:`), dark‑green colour palette used throughout NWCIP.
| **API Interaction** | Central Axios instance, JWT interceptor, handling loading/error states.
| **Role‑Based UI** | `Sidebar` renders links per role, `ProtectedRoute` blocks unauthorized navigation.
| **Leaflet Map** | `MapContainer`, `TileLayer`, `GeoJSON`, fetching geometry from `/geo/protected_areas`.
| **Security** | JWT storage, server‑side role checks, never rely on hidden UI for protection.
| **Testing & Debugging** | Use React DevTools, Chrome Network panel, console errors, Vite error overlay.
| **Presentation Tips** | Start with problem, show tech stack, demo key flows, emphasize security & scalability.

---

*End of Document*.

---

*Prepared by the project mentor for Kiran, Front‑end Lead of NWCIP.*
"

