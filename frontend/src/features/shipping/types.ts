export interface Region {
  id: number
  name: string
  ordinalNumber: number
}

export interface Comuna {
  id: number
  name: string
  shippingCost?: number
  isActive?: boolean
}

export type DispatchMode = 'santiago' | 'regional'

export interface RegionalDispatchOption {
  shippingOptionId: number
  key: string
  carrier: string
  tariff: number
  minLeadDays: number
  maxLeadDays: number
}

export interface DispatchOptions {
  comunaId: number
  mode: DispatchMode
  dates: string[] | null
  shippingOption: RegionalDispatchOption | null
}
