import { describe, expect, it } from 'vitest'

import type { Comuna, Region } from '@/features/shipping/types'

import { reconcileShippingDestination } from './shipping-destination'

const regions: Region[] = [
  { id: 1, name: 'Metropolitana de Santiago', ordinalNumber: 13 },
  { id: 2, name: 'Valparaíso', ordinalNumber: 5 },
]

const santiago: Comuna[] = [{ id: 83, name: 'Santiago' }]
const valparaiso: Comuna[] = [{ id: 51, name: 'Viña del Mar' }]

const address = {
  address: 'Av. Principal 123',
  regionId: 1,
  regionName: 'Valparaíso',
  comunaId: 83,
  comunaName: 'Viña del Mar',
}

describe('reconcileShippingDestination', () => {
  it('derives Santiago labels from authoritative IDs instead of stale checkout labels', () => {
    expect(reconcileShippingDestination(address, regions, santiago)).toEqual({
      status: 'valid',
      destination: {
        comunaId: 83,
        comunaName: 'Santiago',
        regionName: 'Metropolitana de Santiago',
      },
    })
  })

  it('preserves a valid Valparaíso and Viña del Mar selection', () => {
    expect(
      reconcileShippingDestination(
        { ...address, regionId: 2, comunaId: 51 },
        regions,
        valparaiso
      )
    ).toEqual({
      status: 'valid',
      destination: {
        comunaId: 51,
        comunaName: 'Viña del Mar',
        regionName: 'Valparaíso',
      },
    })
  })

  it('preserves a valid Santiago selection', () => {
    expect(
      reconcileShippingDestination(address, regions, santiago)
    ).toMatchObject({
      status: 'valid',
      destination: { comunaId: 83 },
    })
  })

  it('marks missing or invalid selections for recovery without dispatch', () => {
    expect(
      reconcileShippingDestination(
        { ...address, comunaId: 0 },
        regions,
        santiago
      )
    ).toEqual({ status: 'invalid' })
    expect(
      reconcileShippingDestination(
        { ...address, regionId: 99 },
        regions,
        santiago
      )
    ).toEqual({ status: 'invalid' })
    expect(reconcileShippingDestination(address, regions, [])).toEqual({
      status: 'invalid',
    })
  })
})
