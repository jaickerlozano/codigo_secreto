import { z } from 'zod'

const phoneRegex = /^\+56 9 \d{4} \d{4}$/

export const contactSchema = z.object({
  name: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  phone: z
    .string()
    .regex(
      phoneRegex,
      'Teléfono inválido. Usa el formato +56 9 XXXX XXXX',
    ),
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
