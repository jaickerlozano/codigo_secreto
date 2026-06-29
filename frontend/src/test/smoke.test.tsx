import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from '@/App.tsx'

describe('Smoke test', () => {
  it('renders the app greeting', () => {
    render(<App />)

    expect(screen.getByText('Código Secreto')).toBeDefined()
  })
})
