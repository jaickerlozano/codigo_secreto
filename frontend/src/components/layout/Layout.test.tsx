import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { useScrollToTopOnNavigate } from '@/hooks/useScrollToTopOnNavigate'
import { queryClient } from '@/lib/query-client'

import { Layout } from './Layout'

vi.mock('@/hooks/useScrollToTopOnNavigate', () => ({
  useScrollToTopOnNavigate: vi.fn(),
}))

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

describe('Layout', () => {
  beforeEach(() => {
    vi.mocked(useScrollToTopOnNavigate).mockClear()
  })

  it('renders the header, skip link, outlet children and footer', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<div data-testid="outlet-child">Outlet content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
      { wrapper: Wrapper },
    )

    expect(useScrollToTopOnNavigate).toHaveBeenCalledOnce()
    expect(screen.getByRole('button', { name: /Código Secreto — Inicio/i })).toBeDefined()
    expect(screen.getByRole('link', { name: /Saltar al contenido/i })).toBeDefined()
    expect(screen.getByTestId('outlet-child').textContent).toBe('Outlet content')
    expect(screen.getByRole('contentinfo')).toBeDefined()
  })

  it('renders age gate on first visit', () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
      { wrapper: Wrapper },
    )

    expect(screen.getByRole('dialog')).toBeDefined()
  })
})
