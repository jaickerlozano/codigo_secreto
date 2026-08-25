import { describe, expect, it } from 'vitest'

import type { DispatchOptions } from '@/features/shipping/types'

import type { ShippingData } from '../types'

import {
  formatDispatchDate,
  isDispatchSelectionValid,
} from './shipping-selection'

const santiagoOptions: DispatchOptions = {
  comunaId: 1,
  mode: 'santiago',
  dates: ['2026-08-25', '2026-08-27'],
  shippingOption: null,
}

const regionalOptions: DispatchOptions = {
  comunaId: 3,
  mode: 'regional',
  dates: null,
  shippingOption: {
    shippingOptionId: 7,
    key: 'chilexpress',
    carrier: 'Chilexpress',
    minLeadDays: 2,
    maxLeadDays: 4,
  },
}

describe('isDispatchSelectionValid', () => {
  it('accepts a Santiago standard date listed by the backend', () => {
    const selection: ShippingData = {
      deliveryKind: 'standard',
      requestedDispatchDate: '2026-08-25',
    }
    expect(isDispatchSelectionValid(selection, santiagoOptions)).toBe(true)
  })

  it('rejects a date not offered by the backend and any empty selection', () => {
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'standard', requestedDispatchDate: '2026-09-01' },
        santiagoOptions
      )
    ).toBe(false)
    expect(isDispatchSelectionValid({}, santiagoOptions)).toBe(false)
  })

  it('accepts a special future date without a regional option id', () => {
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'special', requestedDispatchDate: '2026-09-01' },
        santiagoOptions
      )
    ).toBe(true)
  })

  it('rejects a regional option id on a Santiago destination', () => {
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'standard', shippingOptionId: 7 },
        santiagoOptions
      )
    ).toBe(false)
  })

  it('requires the exact active regional option and rejects dates or special', () => {
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'standard', shippingOptionId: 7 },
        regionalOptions
      )
    ).toBe(true)
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'standard', shippingOptionId: 8 },
        regionalOptions
      )
    ).toBe(false)
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'special', requestedDispatchDate: '2026-09-01' },
        regionalOptions
      )
    ).toBe(false)
  })

  it('accepts a regional delivery without a unique dispatch profile', () => {
    expect(
      isDispatchSelectionValid(
        { deliveryKind: 'standard' },
        { ...regionalOptions, shippingOption: null }
      )
    ).toBe(true)
  })
})

describe('formatDispatchDate', () => {
  it('formats an ISO date as a Spanish dispatch date', () => {
    expect(formatDispatchDate('2026-08-25')).toBe('martes 25 de agosto')
  })

  it('returns the raw value for malformed input', () => {
    expect(formatDispatchDate('nope')).toBe('nope')
  })
})
