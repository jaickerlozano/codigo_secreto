import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { PersistStorage, StorageValue } from 'zustand/middleware'

import type { Product } from '@/features/catalog/types'

import type { CartItem, CartMode } from '../types'

interface CartState {
  items: CartItem[]
  isOpen: boolean
  mode: CartMode

  // Actions
  addItem: (product: Product) => void
  addItemWithQuantity: (product: Product, quantity: number) => void
  removeItem: (productId: number) => void
  updateQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  setMode: (mode: CartMode) => void
  openCart: () => void
  closeCart: () => void
  toggleCart: () => void

  // Selectors
  getTotalItems: () => number
}

type CartPersistedState = Pick<CartState, 'items' | 'mode'>

const STORAGE_KEY = 'cs-cart'

const conditionalStorage: PersistStorage<CartPersistedState> = {
  getItem: (name) => {
    try {
      const value = localStorage.getItem(name)
      return value ? (JSON.parse(value) as StorageValue<CartState>) : null
    } catch {
      return null
    }
  },
  setItem: (name, value) => {
    try {
      if (value.state.mode === 'guest') {
        localStorage.setItem(name, JSON.stringify(value))
      } else {
        localStorage.removeItem(name)
      }
    } catch {
      localStorage.setItem(name, JSON.stringify(value))
    }
  },
  removeItem: (name) => {
    try {
      localStorage.removeItem(name)
    } catch {
      // ignore
    }
  },
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,
      mode: 'guest',

      addItem: (product) => {
        const items = get().items
        const existing = items.find(
          (item) => item.product.id === product.id,
        )

        if (existing) {
          const quantity = existing.quantity + 1
          set({
            items: items.map((item) =>
              item.product.id === product.id
                ? { ...item, quantity, subtotal: product.price * quantity }
                : item,
            ),
            isOpen: true,
          })
        } else {
          set({
            items: [...items, { product, quantity: 1, subtotal: product.price }],
            isOpen: true,
          })
        }
      },

      addItemWithQuantity: (product, quantity) => {
        const items = get().items
        const existing = items.find(
          (item) => item.product.id === product.id,
        )

        if (existing) {
          const newQuantity = existing.quantity + quantity
          set({
            items: items.map((item) =>
              item.product.id === product.id
                ? {
                    ...item,
                    quantity: newQuantity,
                    subtotal: product.price * newQuantity,
                  }
                : item,
            ),
            isOpen: true,
          })
        } else {
          set({
            items: [...items, { product, quantity, subtotal: product.price * quantity }],
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
              ? { ...item, quantity, subtotal: item.product.price * quantity }
              : item,
          ),
        })
      },

      clearCart: () => set({ items: [] }),
      setMode: (mode) => set({ mode }),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),
      toggleCart: () => set({ isOpen: !get().isOpen }),

      getTotalItems: () =>
        get().items.reduce((sum, item) => sum + item.quantity, 0),
    }),
    {
      name: STORAGE_KEY,
      storage: conditionalStorage,
      partialize: (state): CartPersistedState => ({
        items: state.items,
        mode: state.mode,
      }),
    },
  ),
)

export type { CartItem, CartMode }
