import { useState } from 'react'
import { Link } from 'react-router'

import { SEO } from '@/components/SEO'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useCartStore } from '@/features/cart'

import type { Product } from '../types'
import { REVIEWS } from '../data'
import { useCategories } from '../hooks/useCategories'
import { useProducts } from '../hooks/useProducts'
import { CategoryGrid } from '../components/CategoryGrid'
import { ProductCard } from '../components/ProductCard'
import { ProductModal } from '../components/ProductModal'
import { BenefitsSection } from '../components/sections/BenefitsSection'
import { HeroSection } from '../components/sections/HeroSection'
import { PaymentLogosSection } from '../components/sections/PaymentLogosSection'
import { ReviewsSection } from '../components/sections/ReviewsSection'
import { TrustSection } from '../components/sections/TrustSection'

export function HomePage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const addItem = useCartStore((state) => state.addItem)

  const {
    data: productsData,
    isLoading: productsLoading,
    error: productsError,
  } = useProducts({ pageSize: 8 })
  const {
    data: categories,
    isLoading: categoriesLoading,
    error: categoriesError,
  } = useCategories()

  if (productsLoading || categoriesLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (productsError || categoriesError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <h1 className="mb-2 text-xl font-bold text-foreground">
          Error cargando el catálogo
        </h1>
        <p className="mb-6 text-sm text-muted-foreground">
          {productsError?.message ?? categoriesError?.message}
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Reintentar
        </button>
      </div>
    )
  }

  const products = productsData?.results ?? []
  const totalCount = productsData?.count ?? products.length

  const handleAddToCart = (product: Product) => {
    addItem(product)
  }

  return (
    <div className="flex flex-col">
      <SEO />
      <HeroSection />
      <BenefitsSection />

      <CategoryGrid
        categories={categories ?? []}
        viewAllHref="/category/todos"
      />

      <section id="catalogo" className="py-8 px-4 pb-20" aria-label="Productos">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-extrabold uppercase tracking-wide text-foreground">
                Los más vendidos
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {totalCount} productos
              </p>
            </div>
            <Link
              to="/category/todos"
              className="text-xs font-semibold text-neon-magenta transition-colors hover:text-neon-magenta/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Ver todos
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                onQuickView={setSelectedProduct}
              />
            ))}
          </div>
        </div>
      </section>

      <TrustSection />
      <ReviewsSection reviews={REVIEWS} />
      <PaymentLogosSection />

      <ProductModal
        product={selectedProduct}
        isOpen={Boolean(selectedProduct)}
        onClose={() => setSelectedProduct(null)}
        onAddToCart={handleAddToCart}
      />
    </div>
  )
}
