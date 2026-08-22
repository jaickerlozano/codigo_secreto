import { describe, expect, it } from 'vitest'

import { getDispatchOptions } from './shipping.api'

describe('getDispatchOptions', () => {
  it('maps a Santiago dispatch payload with eligible dates', async () => {
    const options = await getDispatchOptions(1)

    expect(options.comunaId).toBe(1)
    expect(options.mode).toBe('santiago')
    expect(options.dates).toEqual(['2026-08-25', '2026-08-27'])
    expect(options.shippingOption).toBeNull()
  })

  it('maps a regional dispatch payload with the single option', async () => {
    const options = await getDispatchOptions(2)

    expect(options.mode).toBe('regional')
    expect(options.dates).toBeNull()
    expect(options.shippingOption).toEqual({
      shippingOptionId: 7,
      key: 'chilexpress',
      carrier: 'Chilexpress',
      tariff: 4900,
      minLeadDays: 2,
      maxLeadDays: 4,
    })
  })
})
