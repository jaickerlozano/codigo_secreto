import { z } from 'zod'

const phoneRegex = /^\+56 9 \d{4} \d{4}$/

export const contactSchema = z.object({
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
  region: z.string().min(1, 'Selecciona una región'),
  comuna: z.string().min(1, 'Selecciona una comuna'),
  address: z.string().min(5, 'La dirección debe tener al menos 5 caracteres'),
  apartment: z.string().optional(),
  postalCode: z.string().optional(),
  notes: z.string().optional(),
})

export type AddressSchema = z.infer<typeof addressSchema>

export const shippingSchema = z.object({
  carrier: z.enum(['express', 'chilexpress', 'bluexpress', 'pickup']),
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
