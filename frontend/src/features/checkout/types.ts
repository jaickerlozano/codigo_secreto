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

export type DeliveryKind = 'standard' | 'special'

// Explicit delivery selection recorded from backend dispatch options: a
// Santiago standard date, a special future date, or the regional option id.
// Amounts are never computed here — the backend is the only pricing authority.
export interface ShippingData {
  deliveryKind?: DeliveryKind
  requestedDispatchDate?: string | null
  shippingOptionId?: number | null
}

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
