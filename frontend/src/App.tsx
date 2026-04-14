import { Navigate, Route, Routes } from 'react-router-dom'
import NavShell from './components/NavShell'
import HistoryPage from './pages/History'
import ResultsPage from './pages/Results'
import ScanPage from './pages/Scan'

export default function App() {
  return (
    <Routes>
      <Route element={<NavShell />}>
        <Route path="/" element={<Navigate to="/scan" replace />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
    </Routes>
  )
}
