import { useEffect, useMemo, useState } from 'react'

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
  if (products.length === 0) {
    return { min: 0, max: 0 }
  }

  const prices = products.map((product) => product.price)
  return {
    min: Math.min(...prices),
    max: Math.max(...prices),
  }
}

export function useProductFilters({ products }: UseProductFiltersOptions) {
  const [priceRange, setPriceRange] = useState<PriceRange>(
    getInitialPriceRange(products),
  )
  const [sort, setSort] = useState<SortOption>('newest')

  const availableRange = useMemo(
    () => getInitialPriceRange(products),
    [products],
  )

  // useEffect(() => {
  //   setPriceRange(getInitialPriceRange(products))
  // }, [products])

  // useEffect(() => {
  //   if (
  //     products.length > 0 &&
  //     priceRange.min === 0 &&
  //     priceRange.max === 0
  //   ) {
  //     setPriceRange(availableRange)
  //   }
  // }, [products, availableRange, priceRange.min, priceRange.max])

  useEffect(() => {
    if (products.length > 0) {
      const range = getInitialPriceRange(products)
      setPriceRange(range)
    }
  }, [products]) // Dependencia limpia: Solo se ejecuta si cambia el array de productos

  const setMinPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, min: value }))
  }

  const setMaxPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, max: value }))
  }

  const clearFilters = () => {
    setPriceRange(availableRange)
    setSort('newest')
  }

  const filteredProducts = useMemo(() => {
    let result = products.filter((product) => {
      if (
        product.price < priceRange.min ||
        product.price > priceRange.max
      ) {
        return false
      }

      return true
    })

    switch (sort) {
      case 'price-asc':
        result = result.sort((a, b) => a.price - b.price)
        break
      case 'price-desc':
        result = result.sort((a, b) => b.price - a.price)
        break
      case 'name':
        result = result.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'newest':
      default:
        result = result.sort((a, b) => b.id - a.id)
        break
    }

    return result
  }, [priceRange, sort, products])

  return {
    filteredProducts,
    priceRange,
    availableRange,
    setMinPrice,
    setMaxPrice,
    sort,
    setSort,
    clearFilters,
  }
}

export type ProductFilters = ReturnType<typeof useProductFilters>