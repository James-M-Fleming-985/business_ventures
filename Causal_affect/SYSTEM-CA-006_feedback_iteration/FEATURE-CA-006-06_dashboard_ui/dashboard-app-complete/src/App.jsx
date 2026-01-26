import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import MVPDetail from './pages/MVPDetail'
import SignalRadar from './pages/SignalRadar'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/mvp/:id" element={<MVPDetail />} />
          <Route path="/signal-radar" element={<SignalRadar />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App