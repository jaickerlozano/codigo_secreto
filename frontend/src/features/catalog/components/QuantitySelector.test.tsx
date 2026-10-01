import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { QuantitySelector } from './QuantitySelector'

describe('QuantitySelector', () => {
  it('disables the increase control at the available-stock limit', async () => {
    const onChange = vi.fn()
    render(<QuantitySelector value={3} max={3} onChange={onChange} />)

    const increase = screen.getByRole('button', {
      name: 'Aumentar cantidad (máximo 3)',
    })
    expect(increase).toHaveProperty('disabled', true)

    await userEvent.click(increase)
    expect(onChange).not.toHaveBeenCalled()
  })

  it('keeps quantity controls at least 48px high and wide', () => {
    render(<QuantitySelector value={1} max={2} onChange={vi.fn()} />)

    expect(
      screen.getByRole('button', { name: 'Disminuir cantidad' }).className,
    ).toContain('h-12 w-12')
    expect(
      screen.getByRole('button', {
        name: 'Aumentar cantidad (máximo 2)',
      }).className,
    ).toContain('h-12 w-12')
  })
})
