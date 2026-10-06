import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'
import type { UserMe } from '@/features/auth/types'

import type { AddressData, ContactData } from '../../types'

import { StepData } from './StepData'

const contact: ContactData = { name: '', email: '', phone: '', isGuest: true }
const address: AddressData = { regionId: 0, regionName: '', comunaId: 0, comunaName: '', address: '', apartment: '', postalCode: '', notes: '' }

function renderStepData(onSubmit = vi.fn()) {
  const user = userEvent.setup()
  render(<QueryClientProvider client={queryClient()}><StepData defaultValues={{ contact, address }} onSubmit={onSubmit} /></QueryClientProvider>)
  return { user, onSubmit }
}

const authenticatedUser: UserMe = {
  id: 1,
  first_name: 'María',
  last_name: 'González',
  email: 'maria@example.com',
  rut: null,
  phone: '+56 9 1234 5678',
  is_admin: false,
}
async function fillContact(user: ReturnType<typeof userEvent.setup>, phone = '+56 9 1234 5678') {
  await user.type(screen.getByLabelText(/Nombre completo/), 'Juan Pérez')
  await user.type(screen.getByLabelText(/Email/), 'juan@example.com')
  await user.type(screen.getByLabelText(/Teléfono/), phone)
  await user.click(screen.getByRole('button', { name: /Siguiente/ }))
}

describe('StepData (composed Data step)', () => {
  it('starts at the contact form before the address form', () => {
    renderStepData()

    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(screen.queryByRole('group', { name: 'Dirección de envío' })).toBeNull()
  })

  it('blocks invalid contact data without advancing or submitting', async () => {
    const { user, onSubmit } = renderStepData()

    await user.type(screen.getByLabelText(/Nombre completo/), 'A')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    expect(await screen.findByText('El nombre debe tener al menos 2 caracteres')).toBeDefined()
    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('advances to the address form after valid contact data', async () => {
    const { user } = renderStepData()

    await fillContact(user)

    expect(await screen.findByRole('group', { name: 'Dirección de envío' })).toBeDefined()
  })

  it('submits contact and address together after both are valid', async () => {
    const { user, onSubmit } = renderStepData()

    await fillContact(user)
    await user.click(await screen.findByLabelText(/Región/))
    await user.click(
      await screen.findByRole('option', { name: 'Región Metropolitana' })
    )
    const comunaTrigger = screen.getByLabelText(/Comuna/)
    await waitFor(() =>
      expect(comunaTrigger.hasAttribute('disabled')).toBe(false)
    )
    await user.click(comunaTrigger)
    await user.click(await screen.findByRole('option', { name: 'Santiago' }))
    await user.type(screen.getByLabelText(/Calle y número/), 'Av. Siempre Viva 123')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit).toHaveBeenCalledWith({
      contact: { name: 'Juan Pérez', email: 'juan@example.com', phone: '+56 9 1234 5678', isGuest: true },
      address: expect.objectContaining({ regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Av. Siempre Viva 123' }),
    })
  })

  it('returns from the address form to the contact form via Atrás', async () => {
    const { user } = renderStepData()

    await fillContact(user, '912345678')
    await screen.findByRole('group', { name: 'Dirección de envío' })
    await user.click(screen.getByRole('button', { name: 'Atrás' }))

    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect((screen.getByLabelText(/Nombre completo/) as HTMLInputElement).value).toBe('Juan Pérez')
    expect((screen.getByLabelText(/Teléfono/) as HTMLInputElement).value).toBe('+56 9 1234 5678')
  })

  it('starts authenticated checkout at the address without guest or contact controls', () => {
    render(<QueryClientProvider client={queryClient()}><StepData defaultValues={{ contact, address }} authenticatedUser={authenticatedUser} onSubmit={vi.fn()} onCompleteProfilePhone={vi.fn()} /></QueryClientProvider>)

    expect(screen.getByRole('group', { name: 'Dirección de envío' })).toBeDefined()
    expect(screen.queryByText('Continuar como invitado')).toBeNull()
    expect(screen.queryByLabelText(/Nombre completo/)).toBeNull()
    expect(screen.queryByLabelText(/Email/)).toBeNull()
    expect(screen.queryByLabelText(/Teléfono/)).toBeNull()
  })

  it.each(['contact', 'address'] as const)('opens guest %s edit with retained values and accessible focus', async (initialSection) => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    const savedContact = { name: 'Juan Pérez', email: 'juan@example.com', phone: '+56 9 1234 5678', isGuest: true }
    const savedAddress = { ...address, regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Calle 123', apartment: '301', postalCode: '1234567', notes: 'Portería' }
    render(<QueryClientProvider client={queryClient()}><StepData initialSection={initialSection} defaultValues={{ contact: savedContact, address: savedAddress }} onSubmit={onSubmit} /></QueryClientProvider>)

    const input = screen.getByLabelText(initialSection === 'contact' ? /Nombre completo/ : /Calle y número/)
    expect(document.activeElement).toBe(input)
    expect(input).toHaveProperty('value', initialSection === 'contact' ? savedContact.name : savedAddress.address)
    if (initialSection === 'contact') {
      expect(screen.getByLabelText(/Email/)).toHaveProperty('value', savedContact.email)
      expect(screen.getByLabelText(/Teléfono/)).toHaveProperty('value', savedContact.phone)
      await user.click(screen.getByRole('button', { name: /Siguiente/ }))
    }
    expect(screen.getByLabelText(/Calle y número/)).toHaveProperty('value', savedAddress.address)
    expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
    await user.type(screen.getByLabelText(/Calle y número/), ' A')
    await user.click(screen.getByRole('button', { name: 'Atrás' }))
    expect(document.activeElement).toBe(screen.getByLabelText(/Nombre completo/))
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))
    expect(screen.getByLabelText(/Calle y número/)).toHaveProperty('value', 'Calle 123 A')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ contact: savedContact, address: { ...savedAddress, address: 'Calle 123 A' } }))
  })

  it('opens authenticated Contact as focused read-only account information without updates', async () => {
    const user = userEvent.setup()
    const onCompleteProfilePhone = vi.fn()
    render(<QueryClientProvider client={queryClient()}><StepData initialSection="contact" defaultValues={{ contact, address }} authenticatedUser={authenticatedUser} onSubmit={vi.fn()} onCompleteProfilePhone={onCompleteProfilePhone} /></QueryClientProvider>)

    expect(document.activeElement).toBe(screen.getByRole('group', { name: 'Datos de contacto' }))
    expect(screen.getByText('María González')).toBeDefined()
    expect(screen.getByText(authenticatedUser.email)).toBeDefined()
    expect(screen.getByText(authenticatedUser.phone!)).toBeDefined()
    expect(screen.queryByRole('textbox')).toBeNull()
    expect(screen.queryByText('Continuar como invitado')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(screen.getByRole('group', { name: 'Dirección de envío' })).toBeDefined()
    expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
    expect(onCompleteProfilePhone).not.toHaveBeenCalled()
  })

  it('opens authenticated Address directly and submits account contact, not stale guest values', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    const onCompleteProfilePhone = vi.fn()
    const savedAddress = { ...address, regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Calle 123' }
    render(<QueryClientProvider client={queryClient()}><StepData initialSection="address" defaultValues={{ contact, address: savedAddress }} authenticatedUser={authenticatedUser} onSubmit={onSubmit} onCompleteProfilePhone={onCompleteProfilePhone} /></QueryClientProvider>)

    expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
    expect(screen.queryByRole('button', { name: 'Atrás' })).toBeNull()
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ contact: { name: 'María González', email: authenticatedUser.email, phone: authenticatedUser.phone, isGuest: false }, address: savedAddress }))
    expect(onCompleteProfilePhone).not.toHaveBeenCalled()
  })

  it.each(['contact', 'address'] as const)('does not bypass missing profile phone on %s edit', (initialSection) => {
    render(<QueryClientProvider client={queryClient()}><StepData initialSection={initialSection} defaultValues={{ contact, address }} authenticatedUser={{ ...authenticatedUser, phone: null }} onSubmit={vi.fn()} onCompleteProfilePhone={vi.fn()} /></QueryClientProvider>)

    expect(document.activeElement).toBe(screen.getByLabelText(/Teléfono/))
    expect(screen.queryByLabelText(/Nombre completo/)).toBeNull()
    expect(screen.queryByRole('group', { name: 'Dirección de envío' })).toBeNull()
  })

  it('collects only a missing authenticated phone then continues to the address', async () => {
    const user = userEvent.setup()
    const onCompleteProfilePhone = vi.fn().mockResolvedValue({ ...authenticatedUser, phone: '+56 9 1234 5678' })
    render(<QueryClientProvider client={queryClient()}><StepData defaultValues={{ contact, address }} authenticatedUser={{ ...authenticatedUser, phone: null }} onSubmit={vi.fn()} onCompleteProfilePhone={onCompleteProfilePhone} /></QueryClientProvider>)

    expect(screen.getByLabelText(/Teléfono/)).toBeDefined()
    expect(screen.queryByText('Continuar como invitado')).toBeNull()
    expect(screen.queryByLabelText(/Nombre completo/)).toBeNull()
    expect(screen.queryByLabelText(/Email/)).toBeNull()

    await user.type(screen.getByLabelText(/Teléfono/), '912345678')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onCompleteProfilePhone).toHaveBeenCalledWith('+56 9 1234 5678'))
    expect(await screen.findByRole('group', { name: 'Dirección de envío' })).toBeDefined()
  })
})
