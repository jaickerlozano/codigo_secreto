import { Navigate } from 'react-router'

import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

import { useAuth } from '../context/AuthContext'
import { LoginForm } from '../components/LoginForm'

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-base-700 bg-base-800 p-8 shadow-glow-violet">
      <h1 className="mb-6 text-center text-2xl font-bold text-neon-magenta-500">Iniciar sesión</h1>
      <LoginForm />
    </section>
  )
}
