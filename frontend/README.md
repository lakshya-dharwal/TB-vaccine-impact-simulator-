# TB Futures Frontend

React + TypeScript + Vite single-page app for the TB Futures experience.

## Stack

- React 19
- Vite
- Tailwind CSS v4
- React Router
- TanStack Query
- Framer Motion
- Recharts
- Plotly.js
- Vitest + React Testing Library
- Playwright

## Local Development

Start the FastAPI backend from the repository root:

```bash
uvicorn src.api.main:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend expects the API base URL in `VITE_API_BASE_URL`. The default `.env.example`
points at `http://localhost:8000`.

## Scripts

```bash
npm run dev        # start Vite dev server
npm run build      # type-check and build production assets
npm run preview    # preview the production build
npm run test       # run Vitest suite once
npm run test:watch # run Vitest in watch mode
npm run test:e2e   # run Playwright smoke test
```

## Route Map

- `/` scenario explorer
- `/prioritization`
- `/map`
- `/model`

## Testing Notes

- Unit and integration coverage focuses on API normalization, route/query-param sync,
  and core page state flow.
- Playwright includes a smoke path across the main routes. Browser binaries may need
  to be installed locally with `npx playwright install`.
