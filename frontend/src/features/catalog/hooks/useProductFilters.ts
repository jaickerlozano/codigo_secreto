import { useEffect, useMemo, useState } from 'react'

import type { ExperienceLevel, Product } from '../types'

export type SortOption = 'price-asc' | 'price-desc' | 'name' | 'newest'

interface PriceRange {
  min: number
  max: number
}

interface UseProductFiltersOptions {
  products: Product[]
  initialCategory?: string
}

const EXPERIENCE_LEVELS: ExperienceLevel[] = [
  'principiante',
  'intermedio',
  'avanzado',
]

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

export function useProductFilters({
  products,
  initialCategory,
}: UseProductFiltersOptions) {
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    initialCategory ? [initialCategory] : [],
  )
  const [experience, setExperience] = useState<ExperienceLevel[]>([])
  const [priceRange, setPriceRange] = useState<PriceRange>(
    getInitialPriceRange(products),
  )
  const [sort, setSort] = useState<SortOption>('newest')

  const availableRange = useMemo(
    () => getInitialPriceRange(products),
    [products],
  )

  useEffect(() => {
    setSelectedCategories(initialCategory ? [initialCategory] : [])
    setExperience([])
    setPriceRange(getInitialPriceRange(products))
  }, [initialCategory])

  useEffect(() => {
    if (
      products.length > 0 &&
      priceRange.min === 0 &&
      priceRange.max === 0
    ) {
      setPriceRange(availableRange)
    }
  }, [products, availableRange, priceRange.min, priceRange.max])

  const toggleCategory = (category: string) => {
    setSelectedCategories((previous) =>
      previous.includes(category)
        ? previous.filter((item) => item !== category)
        : [...previous, category],
    )
  }

  const toggleExperience = (level: ExperienceLevel) => {
    setExperience((previous) =>
      previous.includes(level)
        ? previous.filter((item) => item !== level)
        : [...previous, level],
    )
  }

  const setMinPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, min: value }))
  }

  const setMaxPrice = (value: number) => {
    setPriceRange((previous) => ({ ...previous, max: value }))
  }

  const clearFilters = () => {
    setSelectedCategories(initialCategory ? [initialCategory] : [])
    setExperience([])
    setPriceRange(availableRange)
  }

  const filteredProducts = useMemo(() => {
    let result = products.filter((product) => {
      if (
        selectedCategories.length > 0 &&
        !selectedCategories.includes(product.category)
      ) {
        return false
      }

      if (
        experience.length > 0 &&
        !experience.includes(product.experienceLevel)
      ) {
        return false
      }

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
  }, [selectedCategories, experience, priceRange, sort, products])

  return {
    filteredProducts,
    selectedCategories,
    toggleCategory,
    experience,
    toggleExperience,
    experienceLevels: EXPERIENCE_LEVELS,
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
