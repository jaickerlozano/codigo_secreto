import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { AuthProvider } from '@/features/auth/context/AuthContext'

import { LoginForm } from './LoginForm'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

describe('LoginForm', () => {
  it('shows validation errors for invalid input', async () => {
    const router = createMemoryRouter([{ path: '/login', element: <LoginForm /> }], {
      initialEntries: ['/login'],
    })

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    const emailInput = screen.getByLabelText('Correo electrónico')
    const passwordInput = screen.getByLabelText('Contraseña')
    const submitButton = screen.getByRole('button', { name: 'Iniciar sesión' })

    await userEvent.type(emailInput, 'not-an-email')
    await userEvent.type(passwordInput, 'short')
    await userEvent.click(submitButton)

    expect(await screen.findByText('Ingresa un correo válido')).toBeDefined()
    expect(screen.getByText('La contraseña debe tener al menos 8 caracteres')).toBeDefined()
  })
})
