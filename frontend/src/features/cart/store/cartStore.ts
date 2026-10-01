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

function getAvailableStock(product: Product): number {
  return Number.isFinite(product.availableStock)
    ? Math.max(0, product.availableStock)
    : 0
}

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
        const availableStock = getAvailableStock(product)
        if (availableStock === 0) return

        const items = get().items
        const existing = items.find(
          (item) => item.product.id === product.id,
        )

        if (existing) {
          const quantity = Math.min(existing.quantity + 1, availableStock)
          set({
            items: items.map((item) =>
              item.product.id === product.id
                ? { ...item, product, quantity }
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

      addItemWithQuantity: (product, quantity) => {
        const availableStock = getAvailableStock(product)
        const requestedQuantity = Math.max(0, quantity)
        if (availableStock === 0 || requestedQuantity === 0) return

        const items = get().items
        const existing = items.find(
          (item) => item.product.id === product.id,
        )

        if (existing) {
          const newQuantity = Math.min(
            existing.quantity + requestedQuantity,
            availableStock,
          )
          set({
            items: items.map((item) =>
              item.product.id === product.id
                ? {
                    ...item,
                    product,
                    quantity: newQuantity,
                  }
                : item,
            ),
            isOpen: true,
          })
        } else {
          set({
            items: [
              ...items,
              { product, quantity: Math.min(requestedQuantity, availableStock) },
            ],
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

        const items = get().items
        const current = items.find((item) => item.product.id === productId)
        if (!current) return

        const availableStock = getAvailableStock(current.product)
        if (availableStock === 0) return

        set({
          items: items.map((item) =>
            item.product.id === productId
              ? { ...item, quantity: Math.min(quantity, availableStock) }
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
