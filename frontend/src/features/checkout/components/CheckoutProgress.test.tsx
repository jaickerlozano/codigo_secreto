import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CheckoutProgress } from './CheckoutProgress'

describe('CheckoutProgress (four-step frame)', () => {
  it('renders the Data/Shipping/Payment/Confirm labels in order', () => {
    render(<CheckoutProgress currentStep={1} />)
    expect(screen.getAllByText(/Datos|Envío|Pago|Confirmar/).map((el) => el.textContent)).toEqual(['Datos', 'Envío', 'Pago', 'Confirmar'])
    expect(screen.queryByText('Contacto')).toBeNull()
    expect(screen.queryByText('Revisar')).toBeNull()
  })

  it('marks only the current step with aria-current', () => {
    render(<CheckoutProgress currentStep={2} />)
    expect(screen.getByText('2', { selector: '[aria-current="step"]' })).toBeDefined()
    for (const n of ['1', '3', '4']) {
      expect(screen.queryByText(n, { selector: '[aria-current="step"]' })).toBeNull()
    }
  })

  it('marks the last step as current at the end of the frame', () => {
    render(<CheckoutProgress currentStep={4} />)
    expect(screen.getByText('4', { selector: '[aria-current="step"]' })).toBeDefined()
    expect(screen.getByText('Confirmar')).toBeDefined()
  })
})
