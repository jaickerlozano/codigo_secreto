export type CheckoutStep = 1 | 2 | 3 | 4

export interface ContactData {
  name: string
  email: string
  phone: string
  isGuest: boolean
}

export interface AddressData {
  regionId: number
  regionName?: string
  comunaId: number
  comunaName?: string
  address: string
  apartment?: string
  postalCode?: string
  notes?: string
}

// Shipping carries no user-selected carrier or fee: the backend tariff for
// the destination (guest quote or authenticated cart) is the only source of
// truth, so the step only records its confirmation.
export type ShippingData = Record<string, never>

export type PaymentMethod = 'webpay' | 'flow' | 'mercadopago' | 'transfer'

export interface PaymentData {
  method: PaymentMethod
}

export interface CheckoutData {
  contact: ContactData
  address: AddressData
  shipping: ShippingData
  payment: PaymentData
  termsAccepted: boolean
}

export interface PaymentOption {
  id: PaymentMethod
  name: string
  description: string
  icon?: string
}
