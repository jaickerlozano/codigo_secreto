import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useCartStore } from '../store'

import { CartDrawer } from './CartDrawer'

describe('CartDrawer', () => {
  it('renders empty cart state when open', () => {
    useCartStore.setState({ isOpen: true })

    render(<CartDrawer />)

    expect(
      document.body.contains(screen.getByText('Tu carrito está vacío')),
    ).toBe(true)
  })
})
