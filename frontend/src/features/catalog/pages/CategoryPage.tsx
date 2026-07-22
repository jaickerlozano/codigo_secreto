import { useMemo, useState, useEffect } from 'react'
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
import { FilterSheet } from '../components/FilterSheet'
import { FilterSidebar } from '../components/FilterSidebar'
import { ProductCard } from '../components/ProductCard'
import { ProductModal } from '../components/ProductModal'
import type { Product } from '../types'

const PAGE_SIZE = 10

// Mapeador para traducir las opciones de la interfaz al formato de ordenamiento que entiende Django
const FRONTEND_TO_DJANGO_SORT: Record<SortOption, string> = {
  'price-asc': 'price',     // ?ordering=price
  'price-desc': '-price',   // ?ordering=-price
  'name': 'name',           // ?ordering=name
  'newest': '-id',          // ?ordering=-id
}

export function CategoryPage() {
  const { categoryId } = useParams<{ categoryId: string }>()
  const isAllView = categoryId === 'todos'
  const numericCategoryId = isAllView ? undefined : Number(categoryId)

  const [page, setPage] = useState(1)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const { addItem } = useCart()

    //  MUDAMOS LOS ESTADOS AQUÍ: Ahora controlan la petición de red directamente
  const [minPrice, setMinPrice] = useState<number | undefined>(undefined)
  const [maxPrice, setMaxPrice] = useState<number | undefined>(undefined)
  const [sort, setSort] = useState<string>('-id') // Formato Django: 'price', '-price', 'name', '-id'

  // Reseteamos estados al cambiar de categoría
  useEffect(() => {
    setPage(1)
    setMinPrice(undefined)
    setMaxPrice(undefined)
    setSort('newest')
  }, [categoryId])

  const {
    data: categories,
    isLoading: categoriesLoading,
    error: categoriesError,
  } = useCategories()

  const currentCategory = useMemo(
    () => categories?.find((category) => category.id === numericCategoryId),
    [categories, numericCategoryId],
  )

  // El hook useProducts ahora reaccionará a CUALQUIER cambio de precio o de orden y le pedirá datos nuevos a Django
  const {
    data: productsData,
    isLoading: productsLoading,
    error: productsError,
  } = useProducts({
    page,
    category: numericCategoryId,
    minPrice,
    maxPrice,
    ordering: FRONTEND_TO_DJANGO_SORT[sort], // Se envía mapeado: 'price', '-price', etc.
  })

  const displayProducts = productsData?.results ?? []

  const filters = useProductFilters({
    products: displayProducts,
  })

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

  //  ASÍ DEBE QUEDAR (Conteo puro del Backend):
  const heading = currentCategory?.name ?? 'Todos los productos'
  const totalCount = productsData?.count ?? 0 // Es el número global que da Django (ej: 3)
  const resultCount = displayProducts.length  // Es lo que se ve en la página actual (máximo 10)
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const categoryDescription = `Explora ${heading.toLowerCase()} en Código Secreto. Envío discreto a todo Chile.`

  return (
    <div key={categoryId || 'todos'} className="contents">
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
            <FilterSidebar
              priceRange={filters.priceRange}
              availableRange={filters.availableRange}
              setMinPrice={filters.setMinPrice}
              setMaxPrice={filters.setMaxPrice}
              clearFilters={filters.clearFilters}
            />

            <section aria-label="Productos filtrados">
              <div className="mb-4 flex items-center justify-between gap-4">
                <FilterSheet
                  priceRange={filters.priceRange}
                  setMinPrice={filters.setMinPrice}
                  setMaxPrice={filters.setMaxPrice}
                  clearFilters={filters.clearFilters}
                />

                <div className="flex items-center gap-2">
                  <label
                    htmlFor="sort-select"
                    className="hidden text-xs text-muted-foreground sm:inline"
                  >
                    Ordenar por
                  </label>
                  <Select
                    value={sort as SortOption}
                    onValueChange={(value) => setSort(value as SortOption)}
                  >
                    <SelectTrigger
                      id="sort-select"
                      className="h-9 w-[170px] border-border bg-card text-xs text-foreground"
                    >
                      <SelectValue placeholder="Ordenar" />
                    </SelectTrigger>
                    <SelectContent className="border-border bg-card">
                      {(
                        [
                          ['price-asc', 'Precio: menor a mayor'],
                          ['price-desc', 'Precio: mayor a menor'],
                          ['name', 'Nombre A-Z'],
                          ['newest', 'Más recientes'],
                        ] as const
                      ).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
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
                  {filters.filteredProducts.map((product, index) => (
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
                    Prueba ajustando el rango de precio.
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
                <nav
                  className="mt-8 flex items-center justify-center gap-2"
                  aria-label="Paginación"
                >
                  {page > 1 && (
                    <button
                      type="button"
                      onClick={() => setPage((p) => p - 1)}
                      className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <ChevronLeft size={16} className="mx-auto" />
                    </button>
                  )}
                  <span className="text-sm text-muted-foreground">
                    Página {page} de {totalPages}
                  </span>
                  {page < totalPages && (
                    <button
                      type="button"
                      onClick={() => setPage((p) => p + 1)}
                      className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <ChevronRight size={16} className="mx-auto" />
                    </button>
                  )}
                </nav>
              )}
            </section>
          </div>
        </div>
      </main>
      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          isOpen
          onClose={() => setSelectedProduct(null)}
          onAddToCart={addItem}
        />
      )}
    </div>
  )
}