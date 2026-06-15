import { Route, Routes } from 'react-router-dom'

import { AppShell } from './components/layout'
import { HomePage } from './pages/home-page'
import { MapPage } from './pages/map-page'
import { ModelPage } from './pages/model-page'
import { NotFoundPage } from './pages/not-found'
import { PrioritizationPage } from './pages/prioritization-page'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="/prioritization" element={<PrioritizationPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/model" element={<ModelPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
