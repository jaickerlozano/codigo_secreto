import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Footer } from './Footer'

describe('Footer', () => {
  it('renders brand, links, payment badges and copyright', () => {
    render(<Footer />)

    expect(screen.getByRole('contentinfo')).toBeDefined()
    expect(screen.getByText('Código Secreto')).toBeDefined()
    expect(screen.getByText('Categorías')).toBeDefined()
    expect(screen.getByText('Ayuda')).toBeDefined()
    expect(screen.getByText('Contacto')).toBeDefined()
    expect(screen.getByRole('link', { name: /WhatsApp/i })).toBeDefined()
    expect(screen.getByText('Webpay')).toBeDefined()
    expect(screen.getByText('Flow')).toBeDefined()
    expect(screen.getByText('MercadoPago')).toBeDefined()
    expect(screen.getByText('Transferencia')).toBeDefined()
    expect(screen.getByText(/© 2024 Código Secreto/i)).toBeDefined()
  })
})
