import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { StepShipping } from './StepShipping'

function renderShipping(overrides: Partial<Parameters<typeof StepShipping>[0]> = {}) {
  const props = { destinationName: 'Providencia', destinationRegion: 'Región Metropolitana', tariff: 3500, isLoading: false, errorMessage: null, onRetry: vi.fn(), onSubmit: vi.fn(), onBack: vi.fn(), ...overrides }
  const user = userEvent.setup()
  render(<StepShipping {...props} />)
  return { user }
}

const continueButton = () => screen.getByRole('button', { name: /Siguiente/ })
const byExactText = (text: string) => (_: string, node: Element | null) => node?.tagName === 'P' && node.textContent === text

describe('StepShipping (backend tariff)', () => {
  it('renders the backend tariff and destination context truthfully', () => {
    renderShipping()
    expect(screen.getByRole('group', { name: 'Envío' })).toBeDefined()
    expect(screen.getByText(byExactText('Envío a Providencia, Región Metropolitana'))).toBeDefined()
    expect(screen.getByText('$3.500')).toBeDefined()
    expect(screen.getByText('Calculada por Código Secreto')).toBeDefined()
  })

  it('shows Gratis for a zero backend tariff and keeps continue enabled', () => {
    renderShipping({ tariff: 0 })
    expect(screen.getByText('Gratis')).toBeDefined()
    expect(continueButton().hasAttribute('disabled')).toBe(false)
  })

  it('shows a loading status and blocks continue while the tariff is loading', () => {
    renderShipping({ isLoading: true })
    expect(screen.getByRole('status').textContent).toContain('Calculando el costo de envío…')
    expect(continueButton().hasAttribute('disabled')).toBe(true)
    expect(screen.queryByText('$3.500')).toBeNull()
  })

  it('shows the tariff error with retry and blocks continue', async () => {
    const onRetry = vi.fn()
    const { user } = renderShipping({ errorMessage: 'No pudimos calcular el costo de envío.', onRetry })
    expect(screen.getByRole('alert').textContent).toContain('No pudimos calcular el costo de envío.')
    expect(continueButton().hasAttribute('disabled')).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('blocks continue while no tariff is available', () => {
    renderShipping({ tariff: null, isLoading: false, errorMessage: null })
    expect(continueButton().hasAttribute('disabled')).toBe(true)
  })

  it('confirms the step via Siguiente and returns via Atrás', async () => {
    const onSubmit = vi.fn()
    const onBack = vi.fn()
    const { user } = renderShipping({ onSubmit, onBack })
    await user.click(continueButton())
    expect(onSubmit).toHaveBeenCalledOnce()
    await user.click(screen.getByRole('button', { name: 'Atrás' }))
    expect(onBack).toHaveBeenCalledOnce()
  })
})
