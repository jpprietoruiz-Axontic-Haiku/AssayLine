import { Route, Routes } from 'react-router-dom'
import { ReportDetailPage } from './pages/ReportDetailPage'
import { ReportsListPage } from './pages/ReportsListPage'

function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <span className="app-brand">AssayLine</span>
        <span className="app-tagline">Technical report review</span>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<ReportsListPage />} />
          <Route path="/reports/:id" element={<ReportDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
