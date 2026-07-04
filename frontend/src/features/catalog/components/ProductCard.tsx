import { useState } from 'react'
import { Link } from 'react-router'
import { motion } from 'motion/react'
import { Check, Eye } from 'lucide-react'

import { useReducedMotion } from '@/hooks/useReducedMotion'
import { formatCLP } from '@/lib/format'

import type { Product } from '../types'
import { StarRating } from './StarRating'

interface ProductCardProps {
  product: Product
  onAddToCart: (product: Product) => void
  onQuickView: (product: Product) => void
}

const experienceStyle: Record<
  Product['experienceLevel'],
  string
> = {
  principiante:
    'bg-neon-lime/15 text-neon-lime border-neon-lime/25',
  intermedio:
    'bg-amber-500/15 text-amber-400 border-amber-500/25',
  avanzado:
    'bg-red-500/15 text-red-400 border-red-500/25',
}

export function ProductCard({
  product,
  onAddToCart,
  onQuickView,
}: ProductCardProps) {
  const [added, setAdded] = useState(false)
  const prefersReduced = useReducedMotion()

  const discount =
    product.originalPrice && product.originalPrice > 0
      ? Math.round(
          (1 - product.price / product.originalPrice) * 100,
        )
      : 0

  const activeBadge = product.badge ??
    (product.isNew ? 'new' : product.isOnSale ? 'discount' : undefined)

  const handleAdd = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    e.stopPropagation()
    onAddToCart(product)
    setAdded(true)
    setTimeout(() => setAdded(false), 1600)
  }

  const handleQuickView = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    e.stopPropagation()
    onQuickView(product)
  }

  return (
    <motion.article
      whileHover={prefersReduced ? undefined : { scale: 1.02 }}
      transition={prefersReduced ? { duration: 0 } : { duration: 0.2 }}
      className="group relative overflow-hidden rounded-2xl border border-border bg-card hover:border-neon-magenta/40 hover:shadow-[0_0_24px_rgba(255,43,214,0.12)]"
    >
      <Link
        to={`/product/${product.id}`}
        className="absolute inset-0 z-0 rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label={`Ver detalles de ${product.name}`}
      />

      <div
        className={`relative flex aspect-square items-center justify-center overflow-hidden bg-gradient-to-br ${product.gradient}`}
      >
        <span
          className="select-none text-7xl opacity-[0.18]"
          aria-hidden="true"
        >
          {product.icon}
        </span>
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage: 'var(--circuit-overlay)',
          }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 z-10 flex items-center justify-center gap-3 bg-black/60 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          <button
            type="button"
            onClick={handleQuickView}
            className="rounded-xl bg-white/10 p-3 text-white backdrop-blur-sm transition-colors hover:bg-white/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
            aria-label={`Vista rápida de ${product.name}`}
          >
            <Eye size={16} />
          </button>
        </div>

        <div className="absolute top-2.5 left-2.5 flex flex-col gap-1.5">
          {activeBadge === 'new' && (
            <span className="rounded-full bg-neon-cyan px-2 py-0.5 text-[9px] font-bold uppercase text-background">
              Nuevo
            </span>
          )}
          {activeBadge === 'discount' && (
            <span className="rounded-full bg-neon-magenta px-2 py-0.5 text-[9px] font-bold uppercase text-background">
              -{discount}%
            </span>
          )}
          {activeBadge === 'popular' && (
            <span className="rounded-full bg-gradient-to-r from-neon-magenta to-neon-violet px-2 py-0.5 text-[9px] font-bold uppercase text-background shadow-[0_0_10px_rgba(255,43,214,0.35)]">
              Popular
            </span>
          )}
        </div>

        <div className="absolute bottom-2.5 right-2.5">
          <span
            className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${experienceStyle[product.experienceLevel]}`}
          >
            {product.experienceLevel}
          </span>
        </div>
      </div>

      <div className="p-4">
        <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
          {product.category}
        </p>
        <h3 className="mb-1 text-[13px] font-semibold leading-snug text-foreground">
          {product.name}
        </h3>
        <p className="mb-3 line-clamp-1 text-xs text-muted-foreground">
          {product.shortDesc ?? product.description}
        </p>

        <div className="mb-3 flex items-center gap-2">
          <StarRating
            rating={product.rating ?? 0}
            size={11}
          />
          <span className="text-[11px] text-muted-foreground">
            ({product.reviewCount ?? 0})
          </span>
        </div>

        <div className="mb-3.5 flex items-center gap-2.5">
          <span className="text-[15px] font-bold text-foreground">
            {formatCLP(product.price)}
          </span>
          {product.originalPrice && (
            <span className="text-xs text-muted-foreground line-through">
              {formatCLP(product.originalPrice)}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={handleAdd}
          className={`relative z-10 w-full rounded-xl py-2.5 text-[13px] font-bold uppercase tracking-wide transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card ${
            added
              ? 'bg-neon-lime text-background'
              : 'text-white hover:shadow-[0_0_18px_rgba(255,43,214,0.45)]'
          }`}
          style={
            added
              ? undefined
              : {
                  background: 'var(--gradient-brand)',
                }
          }
          aria-live="polite"
        >
          {added ? (
            <span className="flex items-center justify-center gap-1.5">
              <Check size={14} aria-hidden="true" /> Agregado
            </span>
          ) : (
            'Agregar al carrito'
          )}
        </button>
      </div>
    </motion.article>
  )
}
