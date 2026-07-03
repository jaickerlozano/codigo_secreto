import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { Product } from '@/features/catalog/types'

export interface CartItem {
  product: Product
  quantity: number
}

interface CartState {
  items: CartItem[]
  isOpen: boolean

  // Actions
  addItem: (product: Product) => void
  removeItem: (productId: string) => void
  updateQuantity: (productId: string, quantity: number) => void
  clearCart: () => void
  openCart: () => void
  closeCart: () => void
  toggleCart: () => void

  // Selectors
  getTotalItems: () => number
  getSubtotal: () => number
  getShippingCost: () => number
  getTotal: () => number
  getFreeShippingProgress: () => number // 0-100 percentage
}

const FREE_SHIPPING_THRESHOLD = 30000 // $30,000 CLP
const FLAT_SHIPPING_RATE = 3990 // $3,990 CLP

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,

      addItem: (product) => {
        const items = get().items
        const existing = items.find(
          (item) => item.product.id === product.id,
        )

        if (existing) {
          set({
            items: items.map((item) =>
              item.product.id === product.id
                ? { ...item, quantity: item.quantity + 1 }
                : item,
            ),
            isOpen: true,
          })
        } else {
          set({
            items: [...items, { product, quantity: 1 }],
            isOpen: true,
          })
        }
      },

      removeItem: (productId) => {
        set({
          items: get().items.filter(
            (item) => item.product.id !== productId,
          ),
        })
      },

      updateQuantity: (productId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(productId)
          return
        }
        set({
          items: get().items.map((item) =>
            item.product.id === productId
              ? { ...item, quantity }
              : item,
          ),
        })
      },

      clearCart: () => set({ items: [] }),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),
      toggleCart: () => set({ isOpen: !get().isOpen }),

      getTotalItems: () =>
        get().items.reduce((sum, item) => sum + item.quantity, 0),
      getSubtotal: () =>
        get().items.reduce(
          (sum, item) => sum + item.product.price * item.quantity,
          0,
        ),
      getShippingCost: () => {
        const subtotal = get().getSubtotal()
        return subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : FLAT_SHIPPING_RATE
      },
      getTotal: () => get().getSubtotal() + get().getShippingCost(),
      getFreeShippingProgress: () => {
        const subtotal = get().getSubtotal()
        return Math.min(
          (subtotal / FREE_SHIPPING_THRESHOLD) * 100,
          100,
        )
      },
    }),
    {
      name: 'cs-cart', // localStorage key
      partialize: (state) => ({ items: state.items }), // only persist items, not isOpen
    },
  ),
)
