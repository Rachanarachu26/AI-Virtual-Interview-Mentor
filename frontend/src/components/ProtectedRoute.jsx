import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Loader from './Loader'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <Loader full label="Loading your workspace..." />
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}
