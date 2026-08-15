import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Heart, Trash2 } from 'lucide-react'
import { Link } from 'react-router'

import { useAuth } from '@/features/auth/context/AuthContext'
import { formatCLP } from '@/lib/format'

import { deleteFavorite } from '../api/favorites.api'
import { useFavoriteProducts, useFavorites } from '../hooks/useFavorites'
import { useFavoritesStore } from '../store/favoritesStore'

function ErrorAlert({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div role="alert" className="my-8 rounded-xl bg-destructive/10 p-4 text-center"><p className="mb-3 text-base text-destructive">{message}</p><button type="button" onClick={onRetry} className="min-h-12 rounded-lg px-4 text-sm font-bold text-neon-magenta underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button></div>
}

export function FavoritesPage() {
  const { isAuthenticated, isLoading, authError, retryAuth } = useAuth()
  const queryClient = useQueryClient()
  const guestIds = useFavoritesStore((s) => s.ids)
  const { data: favorites, isLoading: listLoading, isError: listError, refetch: retryList } = useFavorites()
  const ids = isAuthenticated ? (favorites ?? []).map((f) => f.product) : guestIds
  const products = useFavoriteProducts(ids)
  const removeMutation = useMutation({
    mutationFn: async (productId: number) => {
      if (isAuthenticated) {
        await deleteFavorite(productId)
        await queryClient.invalidateQueries({ queryKey: ['favorites'] })
      } else useFavoritesStore.getState().removeId(productId)
    },
  })
  const retry = () => { if (listError) void retryList(); products.forEach((p) => { if (p.isError) void p.refetch() }) }
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-8 text-2xl font-extrabold uppercase tracking-wide text-foreground">Mis Favoritos</h1>
      {isLoading ? <p role="status" className="py-20 text-center text-base text-muted-foreground">Cargando favoritos…</p> : authError ? <ErrorAlert message="No pudimos verificar tu sesión." onRetry={() => void retryAuth()} /> : removeMutation.isError ? <ErrorAlert message="No pudimos quitar el favorito." onRetry={() => removeMutation.mutate(removeMutation.variables as number)} /> : listLoading || products.some((p) => p.isLoading) ? <p role="status" className="py-20 text-center text-base text-muted-foreground">Cargando favoritos…</p> : listError || products.some((p) => p.isError) ? <ErrorAlert message="No pudimos cargar tus favoritos." onRetry={retry} /> : ids.length === 0 ? (
        <div className="py-20 text-center">
          <Heart size={36} className="mx-auto mb-4 text-muted" aria-hidden="true" />
          <p className="mb-4 text-sm text-muted-foreground">No tienes favoritos todavía.</p>
          <Link to="/category/todos" className="rounded text-sm text-neon-magenta hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Explorar productos</Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {products.map(({ id, data: product }) => (
            <li key={id} className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-card p-4">
              <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${product?.gradient}`} aria-hidden="true"><span className="text-xl opacity-25">{product?.icon}</span></div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-foreground">{product?.name}</p>
                <p className="text-sm text-muted-foreground">{product ? formatCLP(product.price) : ''}</p>
              </div>
              {removeMutation.isPending && removeMutation.variables === id ? <span role="status" className="flex min-h-12 items-center gap-1.5 rounded-lg px-3 text-xs font-bold text-muted-foreground">Quitando favorito: {product?.name ?? id}…</span> : <button type="button" onClick={() => removeMutation.mutate(id)} disabled={removeMutation.isPending} className="flex min-h-12 items-center gap-1.5 rounded-lg px-3 text-xs font-bold text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-label={`Quitar ${product?.name ?? id} de favoritos`}><Trash2 size={14} aria-hidden="true" /> Quitar</button>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
