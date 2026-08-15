import { authHandlers } from './auth'
import { cartHandlers } from './cart'
import { catalogHandlers } from './catalog'
import { contactHandlers } from './contact'
import { favoritesHandlers } from './favorites'
import { orderHandlers } from './orders'
import { paymentHandlers } from './payments'
import { shippingHandlers } from './shipping'

export const handlers = [
  ...authHandlers,
  ...catalogHandlers,
  ...cartHandlers,
  ...contactHandlers,
  ...favoritesHandlers,
  ...orderHandlers,
  ...paymentHandlers,
  ...shippingHandlers,
]
