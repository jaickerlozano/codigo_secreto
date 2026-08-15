import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useCartStore } from '@/features/cart'
import { mergeOnLogin } from '@/features/cart/lib/mergeOnLogin'
import { mergeFavoritesOnLogin } from '@/features/favorites/lib/mergeFavoritesOnLogin'
import { readGuestFavoriteIds } from '@/features/favorites/store/favoritesStore'
import { SESSION_EXPIRED_EVENT } from '@/lib/api-client'

import { login as loginApi, logoutUser } from '../api/auth.api'
import type { LoginInput, UserMe } from '../types'
import { useMe } from '../hooks/useMe'

interface AuthContextValue {
  user: UserMe | null
  isAuthenticated: boolean
  isLoading: boolean
  authError: Error | null; retryAuth: () => Promise<void>
  isLoggingIn: boolean
  loginError: Error | null
  login: (credentials: LoginInput) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const { data: user, error: authError, isLoading, refetch } = useMe()
  const setCartMode = useCartStore((state) => state.setMode)

  useEffect(() => {
    if (!authError) setCartMode(user ? 'authenticated' : 'guest')
    const handleSessionExpired = () => {
      queryClient.setQueryData(['me'], null)
      queryClient.removeQueries({ queryKey: ['cart'] })
      queryClient.removeQueries({ queryKey: ['favorites'] })
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
    return () => {
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
    }
  }, [authError, queryClient, setCartMode, user])

  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginInput) => {
      await loginApi(credentials)
      await queryClient.refetchQueries({ queryKey: ['me'], exact: true })
      const itemsToMerge = [...useCartStore.getState().items]
      await mergeOnLogin(itemsToMerge, queryClient)
      await mergeFavoritesOnLogin(readGuestFavoriteIds(), queryClient)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      try {
        if (user) {
          await logoutUser()
        }
      } finally {
        // Always clean local state even if the API call fails
        queryClient.removeQueries({ queryKey: ['me'] })
        queryClient.removeQueries({ queryKey: ['cart'] })
        queryClient.removeQueries({ queryKey: ['favorites'] })
      }
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
      authError: authError ?? null, retryAuth: async () => { await refetch() },
      isLoggingIn: loginMutation.isPending,
      loginError: loginMutation.error ?? null,
      login,
      logout,
    }),
    [
      user,
      isLoading,
      authError, refetch,
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
