import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { CategoryPage } from './CategoryPage'

// jsdom provides no layout APIs: Radix Slider renders `calc(NaN% + 0px)`
// and throws a CSS parse error. The price-range Slider is UI chrome
// irrelevant to the heading-focus flow under test (same pattern as
// contact.integration.test.tsx), so it is stubbed here.
vi.mock('@/components/ui/slider', () => ({ Slider: () => <div /> }))

function renderPage(path: string) {
  render(
    <QueryClientProvider client={queryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/category/:categoryId" element={<CategoryPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('CategoryPage heading focus', () => {
  it('moves focus to the "todos" catalog heading when the page loads', async () => {
    renderPage('/category/todos')

    const heading = await screen.findByRole('heading', {
      name: 'Todos los productos',
    })

    expect(document.activeElement).toBe(heading)
  })

  it('moves focus to the category-name heading when a category page loads', async () => {
    renderPage('/category/1')

    const heading = await screen.findByRole('heading', {
      name: 'Vibradores',
    })

    expect(document.activeElement).toBe(heading)
  })
})