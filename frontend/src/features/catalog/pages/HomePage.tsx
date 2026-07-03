import { useState } from 'react'
import { Link } from 'react-router'

import { useCartStore } from '@/features/cart'

import type { Product } from '../types'
import { CATEGORIES, PRODUCTS, REVIEWS } from '../data'
import { CategoryGrid } from '../components/CategoryGrid'
import { ProductCard } from '../components/ProductCard'
import { ProductModal } from '../components/ProductModal'
import { BenefitsSection } from '../components/sections/BenefitsSection'
import { HeroSection } from '../components/sections/HeroSection'
import { PaymentLogosSection } from '../components/sections/PaymentLogosSection'
import { ReviewsSection } from '../components/sections/ReviewsSection'
import { TrustSection } from '../components/sections/TrustSection'

export function HomePage() {
  const [selectedProduct, setSelectedProduct] =
    useState<Product | null>(null)
  const addItem = useCartStore((state) => state.addItem)

  const handleAddToCart = (product: Product) => {
    addItem(product)
  }

  return (
    <div className="flex flex-col">
      <HeroSection />
      <BenefitsSection />

      <CategoryGrid categories={CATEGORIES} viewAllHref="/category/todos" />

      <section id="catalogo" className="py-8 px-4 pb-20" aria-label="Productos">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-extrabold uppercase tracking-wide text-foreground">
                Los más vendidos
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {PRODUCTS.length} productos
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
            {PRODUCTS.map((product) => (
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
