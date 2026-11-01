import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ResumeUpload from './pages/ResumeUpload'
import ResumeProfile from './pages/ResumeProfile'
import CategorySelect from './pages/CategorySelect'
import DifficultySelect from './pages/DifficultySelect'
import InterviewSetup from './pages/InterviewSetup'
import LiveInterview from './pages/LiveInterview'
import Results from './pages/Results'
import History from './pages/History'

function Shell() {
  const location = useLocation()
  // Hide the navbar on the immersive live-interview screen.
  const hideNav = /\/interview\/[^/]+\/live$/.test(location.pathname)

  return (
    <>
      {!hideNav && <Navbar />}
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume"
          element={
            <ProtectedRoute>
              <ResumeUpload />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ResumeProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/category"
          element={
            <ProtectedRoute>
              <CategorySelect />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/difficulty"
          element={
            <ProtectedRoute>
              <DifficultySelect />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/setup"
          element={
            <ProtectedRoute>
              <InterviewSetup />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/:id/live"
          element={
            <ProtectedRoute>
              <LiveInterview />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/:id/results"
          element={
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </AuthProvider>
  )
}
