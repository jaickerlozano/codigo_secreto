import { z } from 'zod'

// Mirrors the backend ContactMessageSerializer contract: name ≤ 120, email
// format, subject ≤ 200, non-empty body.
export const contactFormSchema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio').max(120, 'El nombre no puede superar 120 caracteres'),
  email: z.string().trim().min(1, 'El email es obligatorio').email('Ingresa un email válido'),
  subject: z.string().trim().min(1, 'El asunto es obligatorio').max(200, 'El asunto no puede superar 200 caracteres'),
  body: z.string().trim().min(1, 'El mensaje es obligatorio'),
})

export type ContactFormValues = z.infer<typeof contactFormSchema>
