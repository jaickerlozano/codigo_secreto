import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AgeGate } from './AgeGate'

describe('AgeGate', () => {
  it('renders age verification modal when not verified', () => {
    render(<AgeGate />)

    expect(screen.getByRole('dialog')).toBeDefined()
    expect(screen.getByRole('heading', { name: /Bienvenido a Código Secreto/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /Soy mayor de 18 años — Entrar/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /No, salir/i })).toBeDefined()
  })
})
