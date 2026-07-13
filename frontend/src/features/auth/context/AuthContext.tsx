import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { login as loginApi, logoutUser } from '../api/auth.api'
import type { LoginInput, UserMe } from '../types'
import { useMe } from '../hooks/useMe'

interface AuthContextValue {
  user: UserMe | null
  isAuthenticated: boolean
  isLoading: boolean
  isLoggingIn: boolean
  loginError: Error | null
  login: (credentials: LoginInput) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const { data: user, isLoading } = useMe()

  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginInput) => {
      await loginApi(credentials)
      await queryClient.refetchQueries({ queryKey: ['me'], exact: true })
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      if (user) {
        await logoutUser()
      }
      queryClient.removeQueries({ queryKey: ['me'] })
    },
  })

  const login = useCallback(
    async (credentials: LoginInput) => {
      await loginMutation.mutateAsync(credentials)
    },
    [loginMutation],
  )

  const logout = useCallback(
    async () => {
      await logoutMutation.mutateAsync()
    },
    [logoutMutation],
  )

  const value = useMemo(
    () => ({
      user: user ?? null,
      isAuthenticated: !!user,
      isLoading,
      isLoggingIn: loginMutation.isPending,
      loginError: loginMutation.error ?? null,
      login,
      logout,
    }),
    [
      user,
      isLoading,
      loginMutation.isPending,
      loginMutation.error,
      login,
      logout,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider')
  }
  return context
}
