import type { components } from '@/api/schema.d.ts'
import { describe, expect, it } from 'vitest'

import { mapApiProduct } from './mappers'

describe('mapApiProduct', () => {
  it('maps the generated numeric experience-level contract', () => {
    expect(mapApiProduct({ experience_level: 4 } as components['schemas']['Product']).experienceLevel).toBe('avanzado')
  })
})
