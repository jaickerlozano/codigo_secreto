import { Navigate, useLocation } from 'react-router'

import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, authError, retryAuth } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (authError) return <main id="main-content" className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center" role="alert"><h1 className="text-xl font-semibold text-error-500">No pudimos verificar tu sesión</h1><p className="text-base-200">{authError.message}</p><button type="button" onClick={() => void retryAuth()} className="min-h-12 rounded-lg bg-neon-cyan-500 px-6 py-3 font-semibold text-base-900">Reintentar autenticación</button></main>

  if (!isAuthenticated) {
    const next = encodeURIComponent(
      `${location.pathname}${location.search}`,
    )
    return <Navigate to={`/login?next=${next}`} replace />
  }

  return <>{children}</>
}
