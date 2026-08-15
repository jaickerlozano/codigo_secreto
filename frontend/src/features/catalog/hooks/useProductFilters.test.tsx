import { act, render, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Product } from '../types'
import { useProductFilters } from './useProductFilters'

const product = (id: number, price: number): Product => ({ id, name: `P${id}`, price, category: 'todos', experienceLevel: 'principiante', features: [], description: '', materials: [], usageInstructions: '', icon: '', gradient: '', sku: null, stock: 1, image: null, images: [] })

describe('useProductFilters reset', () => {
  it('does not loop while loading keeps supplying a fresh empty array', async () => {
    let renders = 0
    const captured: { filters: ReturnType<typeof useProductFilters> | null } = { filters: null }
    const Harness = () => { renders += 1; captured.filters = useProductFilters({ products: [] }); return null }
    render(<Harness />)
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(renders).toBe(1)
    expect(captured.filters?.filteredProducts).toEqual([])
    expect(captured.filters?.priceRange).toEqual({ min: 0, max: 0 })
  })

  it('resets stale nonzero bounds when the API legitimately returns an empty list', () => {
    const { result, rerender } = renderHook(({ products }) => useProductFilters({ products }), { initialProps: { products: [product(1, 10000)] } })
    act(() => result.current.setMinPrice(10000))
    expect(result.current.priceRange).toEqual({ min: 10000, max: 0 })
    rerender({ products: [] })
    expect(result.current.priceRange).toEqual({ min: 0, max: 0 })
    expect(result.current.filteredProducts).toEqual([])
  })

  it('resets stale max bounds on empty results and clears manual filters on loaded list changes', () => {
    const { result, rerender } = renderHook(({ products }) => useProductFilters({ products }), { initialProps: { products: [product(1, 1000), product(2, 5000)] } })
    act(() => result.current.setMaxPrice(5000))
    expect(result.current.priceRange).toEqual({ min: 0, max: 5000 })
    rerender({ products: [] })
    expect(result.current.priceRange).toEqual({ min: 0, max: 0 })
    act(() => result.current.setMinPrice(2000))
    rerender({ products: [product(3, 3000)] })
    expect(result.current.priceRange).toEqual({ min: 3000, max: 3000 })
  })
})
