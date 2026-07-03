import type { PaymentOption } from '../types'

export const PAYMENT_OPTIONS: PaymentOption[] = [
  {
    id: 'webpay',
    name: 'Webpay',
    description: 'Visa, Mastercard, Redcompra, Amex',
    icon: 'credit-card',
  },
  {
    id: 'flow',
    name: 'Flow',
    description: 'Tarjetas + transferencia + más',
    icon: 'wallet',
  },
  {
    id: 'mercadopago',
    name: 'MercadoPago',
    description: 'Hasta 12 cuotas sin interés',
    icon: 'qr-code',
  },
  {
    id: 'transfer',
    name: 'Transferencia Bancaria',
    description: 'Pago manual — confirmación 24-48h',
    icon: 'building-2',
  },
]
