import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import CsvManager from './pages/CsvManager'
import CampaignsManager from './pages/CampaignsManager'
function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/csv" element={<CsvManager />} />
        <Route path="/campaigns" element={<CampaignsManager />} />
      </Routes>
    </Layout>
  )
}

export default App