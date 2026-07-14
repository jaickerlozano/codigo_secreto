import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { motion } from 'motion/react'
import { ArrowLeft, ChevronLeft, ChevronRight, PackageX } from 'lucide-react'

import { SEO } from '@/components/SEO'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useCart } from '@/features/cart'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

import { useCategories } from '../hooks/useCategories'
import { useProducts } from '../hooks/useProducts'
import { useProductFilters, type SortOption } from '../hooks/useProductFilters'
import { CategoryGrid } from '../components/CategoryGrid'
import { FilterSheet } from '../components/FilterSheet'
import { FilterSidebar } from '../components/FilterSidebar'
import { ProductCard } from '../components/ProductCard'
import { ProductModal } from '../components/ProductModal'
import type { Product } from '../types'

const SORT_LABELS: Record<SortOption, string> = {
  'price-asc': 'Precio: menor a mayor',
  'price-desc': 'Precio: mayor a menor',
  name: 'Nombre A-Z',
  newest: 'Más recientes',
}

const PAGE_SIZE = 12

export function CategoryPage() {
  const { categoryId } = useParams<{ categoryId: string }>()
  const isAllView = categoryId === 'todos'
  const numericCategoryId = isAllView ? undefined : Number(categoryId)

  const [page, setPage] = useState(1)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const { addItem } = useCart()

  const {
    data: categories,
    isLoading: categoriesLoading,
    error: categoriesError,
  } = useCategories()

  const currentCategory = useMemo(
    () => categories?.find((category) => category.id === numericCategoryId),
    [categories, numericCategoryId],
  )

  const {
    data: productsData,
    isLoading: productsLoading,
    error: productsError,
  } = useProducts({
    page,
    pageSize: PAGE_SIZE,
    category: currentCategory?.id,
  })

  const filters = useProductFilters({
    products: productsData?.results ?? [],
    initialCategory: currentCategory?.name,
  })

  const displayProducts = useMemo(() => {
    let result = productsData?.results ?? []

    if (filters.experience.length > 0) {
      result = result.filter((product) =>
        filters.experience.includes(product.experienceLevel),
      )
    }

    switch (filters.sort) {
      case 'price-asc':
        result = [...result].sort((a, b) => a.price - b.price)
        break
      case 'price-desc':
        result = [...result].sort((a, b) => b.price - a.price)
        break
      case 'name':
        result = [...result].sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'newest':
      default:
        result = [...result].sort((a, b) => b.id - a.id)
        break
    }

    return result
  }, [productsData, filters.experience, filters.sort])

  if (categoriesLoading || productsLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (categoriesError || productsError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <h1 className="mb-2 text-xl font-bold text-foreground">
          Error cargando la categoría
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

  if (!isAllView && !currentCategory) {
    return (
      <>
        <SEO pageTitle="Categoría no encontrada" />
        <main
          id="main-content"
          className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-20 text-center"
        >
          <PackageX size={48} className="mb-4 text-muted-foreground" />
          <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">
            Categoría no encontrada
          </h1>
          <p className="mb-6 max-w-xs text-sm text-muted-foreground">
            La categoría que buscas no existe en nuestro catálogo.
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

  const heading = currentCategory?.name ?? 'Todos los productos'
  const resultCount = displayProducts.length
  const totalCount = productsData?.count ?? resultCount
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const categoryDescription = `Explora ${heading.toLowerCase()} en Código Secreto. Envío discreto a todo Chile.`

  return (
    <>
      <SEO
        pageTitle={heading}
        description={categoryDescription}
        ogType="website"
      />
      <main id="main-content" className="px-4 py-8">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-6"
          >
            <Link
              to="/"
              className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <ArrowLeft size={14} /> Volver al inicio
            </Link>
            <h1 className="text-2xl font-extrabold uppercase tracking-wide text-foreground sm:text-3xl">
              {heading}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {resultCount} {resultCount === 1 ? 'producto' : 'productos'}
            </p>
          </motion.div>

          <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
            <FilterSidebar categories={categories ?? []} {...filters} />

            <section aria-label="Productos filtrados">
              <div className="mb-4 flex items-center justify-between gap-4">
                <FilterSheet categories={categories ?? []} {...filters} />

                <div className="flex items-center gap-2">
                  <label
                    htmlFor="sort-select"
                    className="hidden text-xs text-muted-foreground sm:inline"
                  >
                    Ordenar por
                  </label>
                  <Select
                    value={filters.sort}
                    onValueChange={(value) =>
                      filters.setSort(value as SortOption)
                    }
                  >
                    <SelectTrigger
                      id="sort-select"
                      className="h-9 w-[170px] border-border bg-card text-xs text-foreground"
                    >
                      <SelectValue placeholder="Ordenar" />
                    </SelectTrigger>
                    <SelectContent className="border-border bg-card">
                      {(
                        Object.keys(SORT_LABELS) as SortOption[]
                      ).map((option) => (
                        <SelectItem
                          key={option}
                          value={option}
                          className="text-xs text-foreground"
                        >
                          {SORT_LABELS[option]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {resultCount > 0 ? (
                <motion.div
                  layout
                  className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                >
                  {displayProducts.map((product, index) => (
                    <motion.div
                      key={product.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        duration: 0.3,
                        delay: Math.min(index * 0.05, 0.4),
                      }}
                    >
                      <ProductCard
                        product={product}
                        onAddToCart={addItem}
                        onQuickView={setSelectedProduct}
                      />
                    </motion.div>
                  ))}
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                  className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-border bg-card p-8 text-center"
                >
                  <PackageX
                    size={40}
                    className="mb-3 text-muted-foreground"
                  />
                  <p className="mb-1 text-sm font-semibold text-foreground">
                    No encontramos productos con esos filtros.
                  </p>
                  <p className="mb-5 text-xs text-muted-foreground">
                    Prueba ajustando el rango de precio o las categorías.
                  </p>
                  <button
                    type="button"
                    onClick={filters.clearFilters}
                    className="rounded-xl px-5 py-2.5 text-xs font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    style={{ background: 'var(--gradient-brand)' }}
                  >
                    Limpiar filtros
                  </button>
                </motion.div>
              )}

              {totalPages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-4">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((previous) => previous - 1)}
                    className="flex items-center gap-1 rounded-xl border border-border bg-card px-4 py-2 text-xs font-bold uppercase tracking-wide text-foreground transition-all hover:border-neon-magenta hover:text-neon-magenta disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <ChevronLeft size={14} /> Anterior
                  </button>
                  <span className="text-xs text-muted-foreground">
                    Página {page} de {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((previous) => previous + 1)}
                    className="flex items-center gap-1 rounded-xl border border-border bg-card px-4 py-2 text-xs font-bold uppercase tracking-wide text-foreground transition-all hover:border-neon-magenta hover:text-neon-magenta disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    Siguiente <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </section>
          </div>
        </div>

        <CategoryGrid
          categories={categories ?? []}
          activeCategoryId={categoryId}
        />

        <ProductModal
          product={selectedProduct}
          isOpen={Boolean(selectedProduct)}
          onClose={() => setSelectedProduct(null)}
          onAddToCart={addItem}
        />
      </main>
    </>
  )
}
