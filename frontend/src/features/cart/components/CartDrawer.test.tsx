import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CartDrawer } from './CartDrawer'

describe('CartDrawer', () => {
  it('renders empty cart state when closed', () => {
    render(<CartDrawer />)
    expect(
      document.body.contains(screen.getByText('Tu carrito está vacío')),
    ).toBe(true)
  })
})
