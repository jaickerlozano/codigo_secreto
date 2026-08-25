import { z } from 'zod'

export const chileMobilePhonePattern =
  /^(?:9(?: ?\d{4}) ?\d{4}|\+56 ?9(?: ?\d{4}) ?\d{4})$/

export function normalizeChileanMobilePhone(phone: string): string {
  const localNumber = phone.replace(/\s/g, '').replace(/^\+56/, '')

  return `+56 ${localNumber.slice(0, 1)} ${localNumber.slice(1, 5)} ${localNumber.slice(5)}`
}
export const chileanMobilePhoneSchema = z
  .string()
  .regex(
    chileMobilePhonePattern,
    'Ingresa un teléfono móvil chileno válido (ej. 9 1234 5678)'
  )
  .transform(normalizeChileanMobilePhone)

export function hasValidChileanMobilePhone(phone: string | null | undefined): boolean {
  return chileanMobilePhoneSchema.safeParse(phone).success
}

export const contactSchema = z.object({
  name: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  phone: chileanMobilePhoneSchema,
  isGuest: z.boolean(),
})

export type ContactSchema = z.infer<typeof contactSchema>

export const addressSchema = z.object({
  regionId: z.number().min(1, 'Selecciona una región'),
  regionName: z.string().optional(),
  comunaId: z.number().min(1, 'Selecciona una comuna'),
  comunaName: z.string().optional(),
  address: z.string().min(5, 'La dirección debe tener al menos 5 caracteres'),
  apartment: z.string().optional(),
  postalCode: z.string().optional(),
  notes: z.string().optional(),
})

export type AddressSchema = z.infer<typeof addressSchema>

// Delivery selection mirrors the backend dispatch contract: Santiago records
// a standard date (or a special future date), regional records the option id.
// The backend re-validates authority and amount at create time.
export const shippingSchema = z.object({
  deliveryKind: z.enum(['standard', 'special']).optional(),
  requestedDispatchDate: z.string().date().nullish(),
  shippingOptionId: z.number().int().nullish(),
})

export type ShippingSchema = z.infer<typeof shippingSchema>

export const paymentSchema = z.object({
  method: z.enum(['webpay', 'flow', 'mercadopago', 'transfer']),
})

export type PaymentSchema = z.infer<typeof paymentSchema>

export const checkoutSchema = z.object({
  contact: contactSchema,
  address: addressSchema,
  shipping: shippingSchema,
  payment: paymentSchema,
  termsAccepted: z.literal<boolean>(true),
})

export type CheckoutSchema = z.infer<typeof checkoutSchema>
