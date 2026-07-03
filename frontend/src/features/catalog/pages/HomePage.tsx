import { useState } from 'react'
import { X } from 'lucide-react'

import type { Category, Product } from '../types'
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
  const [cart, setCart] = useState<Product[]>([])
  const [activeCategory, setActiveCategory] = useState<string | null>(
    null,
  )

  const filteredProducts = activeCategory
    ? PRODUCTS.filter((product) => product.category === activeCategory)
    : PRODUCTS

  const handleAddToCart = (product: Product) => {
    setCart((previous) => [...previous, product])
    // eslint-disable-next-line no-console
    console.log(
      'Agregado al carrito:',
      product.name,
      'cantidad:',
      cart.length + 1,
    )
  }

  const handleCategoryClick = (category: Category) => {
    setActiveCategory((previous) =>
      previous === category.id ? null : category.id,
    )
  }

  return (
    <div className="flex flex-col">
      <HeroSection />
      <BenefitsSection />
      <CategoryGrid
        categories={CATEGORIES}
        activeCategoryId={activeCategory ?? undefined}
        onCategoryClick={handleCategoryClick}
      />

      <section id="catalogo" className="py-8 px-4 pb-20" aria-label="Productos">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-extrabold uppercase tracking-wide text-foreground">
                {activeCategory ?? 'Los más vendidos'}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {filteredProducts.length} productos
              </p>
            </div>
            {activeCategory && (
              <button
                type="button"
                onClick={() => setActiveCategory(null)}
                className="flex items-center gap-1.5 rounded text-xs text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X size={12} /> Limpiar filtro
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {filteredProducts.map((product) => (
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
