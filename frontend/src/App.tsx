import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import { useState } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 10000 },
  },
})

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/app">
        <div className="min-h-screen bg-background flex">
          <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
          <main
            className={`flex-1 transition-all ${sidebarOpen ? 'ml-64' : 'ml-16'}`}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
