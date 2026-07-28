import { useState } from 'react'
import { motion } from 'motion/react'
import { Check, Lock, Package, Shield } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from '@/components/ui/dialog'
import { formatCLP } from '@/lib/format'

import type { Product } from '../types'
import { ProductGallery } from './ProductGallery'
import { StarRating } from './StarRating'

interface ProductModalProps {
  product: Product | null
  isOpen: boolean
  onClose: () => void
  onAddToCart: (product: Product) => void
}

type TabKey = 'descripcion' | 'materiales' | 'uso'

const tabs: Array<[TabKey, string]> = [
  ['descripcion', 'Descripción'],
  ['materiales', 'Materiales'],
  ['uso', 'Uso'],
]

export function ProductModal({
  product,
  isOpen,
  onClose,
  onAddToCart,
}: ProductModalProps) {
  const [added, setAdded] = useState(false)
  const [tab, setTab] = useState<TabKey>('descripcion')

  if (!product) return null

  const handleAdd = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    e.stopPropagation()
    onAddToCart(product)
    setAdded(true)
    setTimeout(() => {
      setAdded(false)
      onClose()
    }, 1200)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        aria-label={`Vista rápida de ${product.name}`}
        className="max-w-2xl overflow-hidden border-white/10 bg-[#141414] p-0"
      >
        <DialogTitle className="sr-only">{product.name}</DialogTitle>
        <DialogDescription className="sr-only">
          Vista rápida de {product.name}
        </DialogDescription>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 30 }}
          transition={{ duration: 0.26, ease: [0.4, 0, 0.2, 1] }}
        >
          <div className="grid sm:grid-cols-2">
            <div className="max-h-[50vh] overflow-hidden sm:max-h-[60vh]">
              <ProductGallery product={product} />
            </div>

            <div className="p-6">
              <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                {product.category}
              </p>
              <h2
                id="pm-title"
                className="mb-2 text-xl font-extrabold uppercase tracking-wide text-foreground"
              >
                {product.name}
              </h2>

              <div className="mb-4 flex items-center gap-2.5">
                <StarRating rating={product.rating ?? 0} />
                <span className="text-xs text-muted-foreground">
                  {product.rating} · {product.reviewCount} reseñas
                </span>
              </div>

              <div className="mb-5 flex items-center gap-3">
                <span className="text-2xl font-bold text-foreground">
                  {formatCLP(product.price)}
                </span>
                {product.originalPrice && (
                  <span className="text-sm text-muted-foreground line-through">
                    {formatCLP(product.originalPrice)}
                  </span>
                )}
              </div>

              <div
                className="mb-4 flex gap-1 rounded-xl bg-secondary p-1"
                role="tablist"
              >
                {tabs.map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setTab(key)}
                    role="tab"
                    aria-selected={tab === key}
                    className={`flex-1 rounded-lg py-1.5 text-[11px] font-bold uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                      tab === key
                        ? 'text-white'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                    style={
                      tab === key
                        ? { background: 'var(--gradient-brand)' }
                        : undefined
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="mb-5 min-h-[90px]">
                {tab === 'descripcion' && (
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {product.description}
                  </p>
                )}
                {tab === 'materiales' && (
                  <div>
                    <p className="mb-3 text-sm text-muted-foreground">
                      Material:{' '}
                      <span className="font-semibold text-foreground">
                        {product.materials.join(', ')}
                      </span>
                    </p>
                    <ul className="space-y-1.5">
                      {product.features.map((feature, index) => (
                        <li
                          key={index}
                          className="flex items-start gap-2 text-sm text-muted-foreground"
                        >
                          <Check
                            size={12}
                            className="mt-0.5 shrink-0 text-neon-lime"
                            aria-hidden="true"
                          />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {tab === 'uso' && (
                  <div className="space-y-2 text-sm leading-relaxed text-muted-foreground">
                    {product.usageInstructions
                      .split('\n')
                      .map((line, index) => (
                        <p key={index}>{line}</p>
                      ))}
                  </div>
                )}
              </div>

              <div className="mb-5 flex flex-wrap gap-4">
                {[
                  { icon: Lock, label: 'Pago seguro' },
                  { icon: Package, label: 'Envío discreto' },
                  { icon: Shield, label: 'Garantía 6m' },
                ].map(({ icon: Icon, label }) => (
                  <span
                    key={label}
                    className="flex items-center gap-1 text-[10px] text-muted-foreground"
                  >
                    <Icon
                      size={10}
                      className="text-neon-lime"
                      aria-hidden="true"
                    />{' '}
                    {label}
                  </span>
                ))}
              </div>

              <button
                type="button"
                onClick={handleAdd}
                className={`w-full rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-[#141414] ${
                  added
                    ? 'bg-neon-lime text-background'
                    : 'text-white hover:shadow-[0_0_22px_rgba(255,43,214,0.45)]'
                }`}
                style={
                  added
                    ? undefined
                    : { background: 'var(--gradient-brand)' }
                }
                aria-live="polite"
              >
                {added ? (
                  <span className="flex items-center justify-center gap-2">
                    <Check size={15} aria-hidden="true" /> Agregado
                  </span>
                ) : (
                  'Agregar al carrito'
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </DialogContent>
    </Dialog>
  )
}
