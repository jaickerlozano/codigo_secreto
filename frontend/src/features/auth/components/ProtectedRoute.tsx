import { Navigate, useLocation } from 'react-router'

import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    const next = encodeURIComponent(
      `${location.pathname}${location.search}`,
    )
    return <Navigate to={`/login?next=${next}`} replace />
  }

  return <>{children}</>
}
