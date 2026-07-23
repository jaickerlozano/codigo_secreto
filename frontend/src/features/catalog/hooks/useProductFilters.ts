import { useMemo, useState, useEffect } from 'react'
import type { Product } from '../types'

export type SortOption = 'price-asc' | 'price-desc' | 'name' | 'newest'

interface PriceRange {
  min: number
  max: number
}

interface UseProductFiltersOptions {
  products: Product[]
}

function getInitialPriceRange(products: Product[]): PriceRange {
  if (!products || products.length === 0) {
    return { min: 0, max: 0 }
  }
  const prices = products.map((product) => product.price)
  return {
    min: Math.min(...prices),
    max: Math.max(...prices),
  }
}

export function useProductFilters({ products }: UseProductFiltersOptions) {
  const [sort, setSort] = useState<SortOption>('newest')

  // 1. Calculamos el rango disponible nativamente cada vez que la API cambie los productos
  const availableRange = useMemo(() => getInitialPriceRange(products), [products])

  // 2. El rango seleccionado por el usuario. Empieza en 0 y solo se aplica si es mayor a 0
  const [priceRange, setPriceRange] = useState<PriceRange>({ min: 0, max: 0 })

  // 3. Reseteamos el filtro manual del usuario cada vez que cambie la lista de productos de la API
  useEffect(() => {
    setPriceRange({ min: 0, max: 0 })
  }, [products])

  const setMinPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, min: value }))
  }

  const setMaxPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, max: value }))
  }

  const clearFilters = () => {
    setPriceRange({ min: 0, max: 0 })
    setSort('newest')
  }

  const filteredProducts = useMemo(() => {
    let result = [...products]

    // 4. Filtrado de rango de precios ultra seguro
    result = result.filter((product) => {
      // Si el usuario no ha movido los filtros (están en 0), se muestran todos
      if (priceRange.min === 0 && priceRange.max === 0) {
        return true
      }
      return product.price >= priceRange.min && product.price <= priceRange.max
    })

    // 5. Ordenamiento
    switch (sort) {
      case 'price-asc':
        result.sort((a, b) => a.price - b.price)
        break
      case 'price-desc':
        result.sort((a, b) => b.price - a.price)
        break
      case 'name':
        result.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'newest':
      default:
        result.sort((a, b) => b.id - a.id)
        break
    }

    return result
  }, [priceRange.min, priceRange.max, sort, products])

  return {
    filteredProducts,
    priceRange: priceRange.min === 0 && priceRange.max === 0 ? availableRange : priceRange,
    availableRange,
    setMinPrice,
    setMaxPrice,
    sort,
    setSort,
    clearFilters,
  }
}

export type ProductFilters = ReturnType<typeof useProductFilters>
