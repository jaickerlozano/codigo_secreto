import type { ShippingOption } from '../types'

export const SHIPPING_OPTIONS: ShippingOption[] = [
  {
    id: 'express',
    name: 'Envío Express',
    description: 'Mismo día (antes 16:00)',
    price: 4990,
    eta: 'Mismo día',
  },
  {
    id: 'chilexpress',
    name: 'Chilexpress / Starken',
    description: 'Entrega rápida a todo Chile',
    price: 3490,
    eta: '2-3 días hábiles',
  },
  {
    id: 'bluexpress',
    name: 'Bluexpress',
    description: 'Envío económico nacional',
    price: 2990,
    eta: '5-7 días hábiles',
  },
  {
    id: 'pickup',
    name: 'Retiro en tienda',
    description: 'Retira tu pedido en nuestra tienda',
    price: 0,
    eta: 'Disponible en 24h',
  },
]
