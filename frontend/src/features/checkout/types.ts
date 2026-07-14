export type CheckoutStep = 1 | 2 | 3 | 4 | 5

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

export type ShippingCarrier = 'express' | 'chilexpress' | 'bluexpress' | 'pickup'

export interface ShippingData {
  carrier: ShippingCarrier
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

export interface ShippingOption {
  id: ShippingCarrier
  name: string
  description: string
  price: number
  eta: string
}

export interface PaymentOption {
  id: PaymentMethod
  name: string
  description: string
  icon?: string
}
