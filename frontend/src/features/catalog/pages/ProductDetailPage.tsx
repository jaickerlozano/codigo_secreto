import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowLeft, Check, Heart, PackageX } from 'lucide-react'

import { SEO } from '@/components/SEO'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useCart } from '@/features/cart'
import { formatCLP } from '@/lib/format'

import { useCategories } from '../hooks/useCategories'
import { useProduct } from '../hooks/useProduct'
import { useProducts } from '../hooks/useProducts'
import { ProductCard } from '../components/ProductCard'
import { ProductGallery } from '../components/ProductGallery'
import { ProductModal } from '../components/ProductModal'
import { QuantitySelector } from '../components/QuantitySelector'
import { StarRating } from '../components/StarRating'
import type { Product } from '../types'

const EXPERIENCE_BADGE: Record<
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

type TabKey = 'descripcion' | 'materiales' | 'instrucciones'

const TABS: Array<[TabKey, string]> = [
  ['descripcion', 'Descripción'],
  ['materiales', 'Materiales'],
  ['instrucciones', 'Instrucciones de uso'],
]

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const numericProductId = Number(productId)

  const {
    data: product,
    isLoading: productLoading,
    error: productError,
  } = useProduct(numericProductId)

  const { data: categories } = useCategories()
  const categoryByName = useMemo(() => {
    const map = new Map<string, number>()
    categories?.forEach((category) => map.set(category.name, category.id))
    return map
  }, [categories])

  const categoryId = product ? categoryByName.get(product.category) : undefined

  const { data: relatedProductsData } = useProducts({
    pageSize: 4,
    category: categoryId,
  })

  const { addItemWithQuantity } = useCart()

  const [quantity, setQuantity] = useState(1)
  const [tab, setTab] = useState<TabKey>('descripcion')
  const [added, setAdded] = useState(false)
  const [wishlisted, setWishlisted] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  if (productLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (productError || !product) {
    return (
      <>
        <SEO pageTitle="Producto no encontrado" />
        <main
          id="main-content"
          className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-20 text-center"
        >
          <PackageX size={48} className="mb-4 text-muted-foreground" />
          <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">
            Producto no encontrado
          </h1>
          <p className="mb-6 max-w-xs text-sm text-muted-foreground">
            {productError?.message ??
              'El producto que buscas no existe o fue removido del catálogo.'}
          </p>
          <Link
            to="/"
            className="rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Volver al inicio
          </Link>
        </main>
      </>
    )
  }

  const discount =
    product.originalPrice && product.originalPrice > 0
      ? Math.round(
          (1 - product.price / product.originalPrice) * 100,
        )
      : 0

  const handleAddToCart = () => {
    addItemWithQuantity(product, quantity)
    setAdded(true)
    setTimeout(() => setAdded(false), 1600)
  }

  const relatedProducts =
    relatedProductsData?.results.filter(
      (item) => item.id !== product.id,
    ) ?? []

  return (
    <>
      <SEO
        pageTitle={product.name}
        description={product.shortDesc ?? product.description}
        ogType="product"
      />
      <main id="main-content" className="px-4 py-8">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-6"
          >
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <ArrowLeft size={14} /> Volver al catálogo
            </Link>
          </motion.div>

          <div className="grid gap-8 lg:grid-cols-2">
            <ProductGallery product={product} />

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                {product.category}
              </p>
              <h1 className="mb-3 text-2xl font-extrabold uppercase leading-tight tracking-wide text-foreground sm:text-3xl">
                {product.name}
              </h1>

              <div className="mb-4 flex flex-wrap items-center gap-3">
                <StarRating rating={product.rating ?? 0} />
                <span className="text-xs text-muted-foreground">
                  {product.rating} · {product.reviewCount} reseñas
                </span>
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${EXPERIENCE_BADGE[product.experienceLevel]}`}
                >
                  {product.experienceLevel}
                </span>
              </div>

              <div className="mb-6 flex items-center gap-3">
                <span className="text-2xl font-bold text-foreground sm:text-3xl">
                  {formatCLP(product.price)}
                </span>
                {product.originalPrice && (
                  <>
                    <span className="text-sm text-muted-foreground line-through">
                      {formatCLP(product.originalPrice)}
                    </span>
                    <span className="rounded-full bg-neon-magenta px-2 py-0.5 text-[9px] font-bold uppercase text-background">
                      -{discount}%
                    </span>
                  </>
                )}
              </div>

              <div
                className="mb-6 flex gap-1 rounded-xl bg-secondary p-1"
                role="tablist"
              >
                {TABS.map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setTab(key)}
                    role="tab"
                    aria-selected={tab === key}
                    className={`flex-1 rounded-lg py-2 text-[11px] font-bold uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
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

              <div className="mb-6 min-h-[120px]">
                <AnimatePresence mode="wait">
                  {tab === 'descripcion' && (
                    <motion.div
                      key="descripcion"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ duration: 0.2 }}
                    >
                      <p className="text-sm leading-relaxed text-muted-foreground">
                        {product.description}
                      </p>
                    </motion.div>
                  )}
                  {tab === 'materiales' && (
                    <motion.div
                      key="materiales"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-3"
                    >
                      <p className="text-sm text-muted-foreground">
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
                    </motion.div>
                  )}
                  {tab === 'instrucciones' && (
                    <motion.div
                      key="instrucciones"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-2 text-sm leading-relaxed text-muted-foreground"
                    >
                      {product.usageInstructions
                        .split('\n')
                        .map((line, index) => (
                          <p key={index}>{line}</p>
                        ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="mb-6 flex items-center gap-4">
                <QuantitySelector
                  value={quantity}
                  onChange={setQuantity}
                  min={1}
                  max={10}
                />
                <span className="text-xs text-muted-foreground">
                  Máx. 10 unidades
                </span>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={handleAddToCart}
                  className={`flex-1 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
                    added
                      ? 'bg-neon-lime text-background'
                      : 'text-white hover:shadow-[0_0_24px_rgba(255,43,214,0.45)]'
                  }`}
                  style={
                    added ? undefined : { background: 'var(--gradient-brand)' }
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

                <motion.button
                  type="button"
                  onClick={() => setWishlisted((previous) => !previous)}
                  whileTap={{ scale: 0.95 }}
                  className={`flex items-center justify-center gap-2 rounded-xl border px-6 py-3.5 text-sm font-bold uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                    wishlisted
                      ? 'border-neon-magenta bg-neon-magenta/10 text-neon-magenta'
                      : 'border-border bg-card text-foreground hover:border-neon-magenta hover:text-neon-magenta'
                  }`}
                  aria-label={
                    wishlisted
                      ? 'Quitar de wishlist'
                      : 'Agregar a wishlist'
                  }
                >
                  <Heart
                    size={16}
                    fill={wishlisted ? 'currentColor' : 'none'}
                  />
                  {wishlisted ? 'Guardado' : 'Wishlist'}
                </motion.button>
              </div>
            </motion.div>
          </div>

          {relatedProducts.length > 0 && (
            <section className="mt-16" aria-label="Productos relacionados">
              <h2 className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
                Productos relacionados
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {relatedProducts.map((item) => (
                  <ProductCard
                    key={item.id}
                    product={item}
                    onAddToCart={(item) => addItemWithQuantity(item, 1)}
                    onQuickView={setSelectedProduct}
                  />
                ))}
              </div>
            </section>
          )}
        </div>

        <ProductModal
          product={selectedProduct}
          isOpen={Boolean(selectedProduct)}
          onClose={() => setSelectedProduct(null)}
          onAddToCart={(item) => addItemWithQuantity(item, 1)}
        />
      </main>
    </>
  )
}
