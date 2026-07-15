import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CheckoutStep } from '../types'

import { useCheckout } from './useCheckout'

const testContact = {
  name: 'Juan Pérez',
  email: 'juan@example.com',
  phone: '56912345678',
  isGuest: true,
}

const testAddress = {
  regionId: 1,
  regionName: 'Metropolitana',
  comunaId: 2,
  comunaName: 'Santiago',
  address: 'Av. Siempre Viva 123',
  apartment: '301',
  postalCode: '8320000',
  notes: 'Tocar timbre',
}

const testShipping = {
  carrier: 'chilexpress' as const,
}

describe('useCheckout', () => {
  it('starts at step 1 with empty initial data', () => {
    const { result } = renderHook(() => useCheckout())

    expect(result.current.currentStep).toBe(1)
    expect(result.current.data.contact).toEqual({
      name: '',
      email: '',
      phone: '',
      isGuest: true,
    })
    expect(result.current.data.address).toEqual({
      regionId: 0,
      regionName: '',
      comunaId: 0,
      comunaName: '',
      address: '',
      apartment: '',
      postalCode: '',
      notes: '',
    })
    expect(result.current.data.shipping).toEqual({ carrier: 'chilexpress' })
    expect(result.current.data.payment).toEqual({ method: 'webpay' })
    expect(result.current.data.termsAccepted).toBe(false)
  })

  it('updates contact data', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.setContact(testContact)
    })

    expect(result.current.data.contact).toEqual(testContact)
  })

  it('updates address data', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.setAddress(testAddress)
    })

    expect(result.current.data.address).toEqual(testAddress)
  })

  it('updates shipping and payment methods', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.setShipping({ carrier: 'bluexpress' })
      result.current.setPayment({ method: 'mercadopago' })
    })

    expect(result.current.data.shipping).toEqual({ carrier: 'bluexpress' })
    expect(result.current.data.payment).toEqual({ method: 'mercadopago' })
  })

  it('toggles terms acceptance', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.setTermsAccepted(true)
    })

    expect(result.current.data.termsAccepted).toBe(true)
  })

  it('navigates forward and backward between steps', () => {
    const { result } = renderHook(() => useCheckout())

    expect(result.current.currentStep).toBe(1)

    act(() => {
      result.current.nextStep()
    })
    expect(result.current.currentStep).toBe(2)

    act(() => {
      result.current.nextStep()
      result.current.nextStep()
      result.current.nextStep()
    })
    expect(result.current.currentStep).toBe(5)

    act(() => {
      result.current.nextStep()
    })
    expect(result.current.currentStep).toBe(5)

    act(() => {
      result.current.prevStep()
    })
    expect(result.current.currentStep).toBe(4)

    act(() => {
      result.current.goToStep(2)
    })
    expect(result.current.currentStep).toBe(2)
  })

  it('ignores steps outside the valid range', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.goToStep(0 as unknown as CheckoutStep)
      result.current.goToStep(6 as unknown as CheckoutStep)
    })

    expect(result.current.currentStep).toBe(1)
  })

  it('preserves previous data when updating a single section', () => {
    const { result } = renderHook(() => useCheckout())

    act(() => {
      result.current.setContact(testContact)
      result.current.setAddress(testAddress)
    })

    act(() => {
      result.current.setShipping(testShipping)
    })

    expect(result.current.data.contact).toEqual(testContact)
    expect(result.current.data.address).toEqual(testAddress)
    expect(result.current.data.shipping).toEqual(testShipping)
  })
})
