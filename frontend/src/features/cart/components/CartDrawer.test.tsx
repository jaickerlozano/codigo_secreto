import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useCartStore } from '../store'

import { CartDrawer } from './CartDrawer'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('CartDrawer', () => {
  it('renders empty cart state when open', () => {
    useCartStore.setState({ isOpen: true })

    render(<CartDrawer />, { wrapper: Wrapper })

    expect(
      document.body.contains(screen.getByText('Tu carrito está vacío')),
    ).toBe(true)
  })
})
