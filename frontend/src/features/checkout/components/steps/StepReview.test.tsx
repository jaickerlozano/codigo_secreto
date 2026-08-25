import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { CheckoutData } from '../../types'

import { StepReview } from './StepReview'

const data: CheckoutData = { contact: { name: 'Juan Pérez', email: 'juan@example.com', phone: '+56 9 1234 5678', isGuest: true }, address: { regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Av. Siempre Viva 123', apartment: '301' }, shipping: {}, payment: { method: 'webpay' }, termsAccepted: true }

function renderReview(onEditStep = vi.fn()) {
  return render(<StepReview data={data} subtotal={29990} shippingCost={3500} total={33490} quoteReady onEditStep={onEditStep} onTermsChange={vi.fn()} onBack={vi.fn()} onConfirm={vi.fn()} />)
}

describe('StepReview review map (four-step frame)', () => {
  it('maps Contacto and Dirección edits to the Data step (1)', async () => {
    const onEditStep = vi.fn()
    const user = userEvent.setup()
    renderReview(onEditStep)

    await user.click(screen.getAllByRole('button', { name: 'Editar' })[0])
    expect(onEditStep).toHaveBeenLastCalledWith(1)
    await user.click(screen.getAllByRole('button', { name: 'Editar' })[1])
    expect(onEditStep).toHaveBeenLastCalledWith(1)
  })

  it('maps Envío to step 2 and Pago to step 3', async () => {
    const onEditStep = vi.fn()
    const user = userEvent.setup()
    renderReview(onEditStep)

    await user.click(screen.getAllByRole('button', { name: 'Editar' })[2])
    expect(onEditStep).toHaveBeenLastCalledWith(2)
    await user.click(screen.getAllByRole('button', { name: 'Editar' })[3])
    expect(onEditStep).toHaveBeenLastCalledWith(3)
  })

  it('shows the destination-based Envío label instead of a frontend carrier name', () => {
    renderReview()

    expect(screen.getByText('Envío a Santiago, Región Metropolitana')).toBeDefined()
  })

  it('shows the selected dispatch date in the Envío review line', () => {
    render(<StepReview data={{ ...data, shipping: { deliveryKind: 'standard', requestedDispatchDate: '2026-08-25' } }} subtotal={29990} shippingCost={3500} total={33490} quoteReady onEditStep={vi.fn()} onTermsChange={vi.fn()} onBack={vi.fn()} onConfirm={vi.fn()} />)

    expect(screen.getByText('Envío a Santiago, Región Metropolitana — martes 25 de agosto')).toBeDefined()
  })

  it('shows the authenticated account contact instead of checkout form state', () => {
    render(<StepReview data={data} accountContact="María González · maria@example.com" subtotal={29990} shippingCost={3500} total={33490} quoteReady onEditStep={vi.fn()} onTermsChange={vi.fn()} onBack={vi.fn()} onConfirm={vi.fn()} />)

    expect(screen.getByText('María González · maria@example.com')).toBeDefined()
    expect(screen.queryByText('juan@example.com')).toBeNull()
  })
})
