import { useMemo } from 'react'

import type { Product } from '@/features/catalog/types'

import { useGuestQuote } from './useGuestQuote'
import { mapApiCartItem } from '../lib/mappers'
import { useCartStore } from '../store'
import type { CartItem } from '../types'

import { useAddToCart } from './useAddToCart'
import { useCartItems } from './useCartItems'
import { useRemoveFromCart } from './useRemoveFromCart'
import { useUpdateCartItem } from './useUpdateCartItem'

export interface UseCartResult {
  mode: 'guest' | 'authenticated'
  items: CartItem[]
  isLoading: boolean
  error: Error | null
  retry: () => Promise<void>
  addItem: (product: Product) => void
  addItemWithQuantity: (product: Product, quantity: number) => void
  removeItem: (productId: number) => void
  updateQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  totalItems: number
  subtotal: number | null
  shippingCost: number | null
  total: number | null
  freeShippingProgress: number
  freeShippingThreshold: number
  quote: ReturnType<typeof useGuestQuote>['data'] | null
  quoteInput: Parameters<typeof useGuestQuote>[0]
  quoteIsLoading: boolean
  quoteIsError: boolean
  quoteError: Error | null
  quoteIsStale: boolean
  retryQuote: () => void
}

export function useCart(
  options: { comunaId?: number | null } = {},
): UseCartResult {
  const mode = useCartStore((state) => state.mode)
  const guestItems = useCartStore((state) => state.items)
  const guestAddItem = useCartStore((state) => state.addItem)
  const guestAddItemWithQuantity = useCartStore(
    (state) => state.addItemWithQuantity,
  )
  const guestRemoveItem = useCartStore((state) => state.removeItem)
  const guestUpdateQuantity = useCartStore((state) => state.updateQuantity)
  const guestClearCart = useCartStore((state) => state.clearCart)
  const quoteInput = useMemo(() => ({ items: guestItems.map(({ product, quantity }) => ({ product_id: product.id, quantity })), ...(options.comunaId ? { comuna: options.comunaId } : {}) }), [guestItems, options.comunaId])

  const {
    data: cartData,
    error: cartError,
    isLoading: isCartLoading,
    refetch: refetchCart,
  } = useCartItems({ enabled: mode === 'authenticated' })
  const guestQuote = useGuestQuote(mode === 'guest' ? quoteInput : { items: [] })
  const addToCartMutation = useAddToCart()
  const removeFromCartMutation = useRemoveFromCart()
  const updateCartItemMutation = useUpdateCartItem()

  const authItems = useMemo<CartItem[]>(() => {
    if (!cartData) return []
    return cartData.items.map((apiItem) => mapApiCartItem(apiItem))
  }, [cartData])

  const items = mode === 'authenticated' ? authItems : guestItems

  const totalItems = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity, 0),
    [items],
  )

  const isAuthenticated = mode === 'authenticated'

  const subtotal = isAuthenticated ? (cartData?.subtotal ?? 0) : (guestQuote.data?.subtotal ?? null)
  const shippingCost = isAuthenticated ? (cartData?.shipping_cost ?? 0) : (guestQuote.data?.shipping_cost ?? null)
  const total = isAuthenticated ? (cartData?.total ?? 0) : (guestQuote.data?.total ?? null)
  const freeShippingProgress = isAuthenticated
    ? (cartData?.free_shipping_progress ?? 0)
    : 0
  const freeShippingThreshold = isAuthenticated
    ? (cartData?.free_shipping_threshold ?? 0)
    : 0

  const addItem = (product: Product) => {
    if (mode === 'authenticated') {
      addToCartMutation.mutate({ product_id: product.id, quantity: 1 })
    } else {
      guestAddItem(product)
    }
  }

  const addItemWithQuantity = (product: Product, quantity: number) => {
    if (mode === 'authenticated') {
      addToCartMutation.mutate({ product_id: product.id, quantity })
    } else {
      guestAddItemWithQuantity(product, quantity)
    }
  }

  const removeItem = (productId: number) => {
    if (mode === 'authenticated') {
      const current = authItems.find((item) => item.product.id === productId)
      if (current) {
        removeFromCartMutation.mutate({
          product_id: productId,
          quantity: current.quantity,
        })
      }
    } else {
      guestRemoveItem(productId)
    }
  }

  const updateQuantity = (productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeItem(productId)
      return
    }

    if (mode === 'authenticated') {
      const current = authItems.find((item) => item.product.id === productId)
      if (current) {
        updateCartItemMutation.mutate({
          productId,
          quantity,
          currentQuantity: current.quantity,
        })
      }
    } else {
      guestUpdateQuantity(productId, quantity)
    }
  }

  const clearCart = () => {
    if (mode === 'authenticated') {
      authItems.forEach((item) => {
        removeFromCartMutation.mutate({
          product_id: item.product.id,
          quantity: item.quantity,
        })
      })
    } else {
      guestClearCart()
    }
  }

  return {
    mode,
    items,
    isLoading: isAuthenticated ? isCartLoading : guestQuote.isLoading || guestQuote.isFetching,
    error: isAuthenticated ? cartError : null,
    retry: async () => {
      if (isAuthenticated) await refetchCart()
    },
    addItem,
    addItemWithQuantity,
    removeItem,
    updateQuantity,
    clearCart,
    totalItems,
    subtotal,
    shippingCost,
    total,
    freeShippingProgress,
    freeShippingThreshold,
    quote: isAuthenticated ? null : (guestQuote.data ?? null),
    quoteInput,
    quoteIsLoading: isAuthenticated ? false : guestQuote.isLoading || guestQuote.isFetching,
    quoteIsError: isAuthenticated ? false : guestQuote.isError,
    quoteError: isAuthenticated ? null : guestQuote.error,
    quoteIsStale: isAuthenticated ? false : guestQuote.isStale,
    retryQuote: () => { if (!isAuthenticated) void guestQuote.refetch() },
  }
}
