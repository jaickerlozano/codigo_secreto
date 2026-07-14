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
