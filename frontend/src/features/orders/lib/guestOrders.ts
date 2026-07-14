const GUEST_ORDERS_KEY = 'cs-guest-orders'
const MAX_GUEST_ORDERS = 5

export function getGuestOrders(): string[] {
  try {
    const raw = localStorage.getItem(GUEST_ORDERS_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

export function addGuestOrder(orderNumber: string): void {
  try {
    const orders = [
      orderNumber,
      ...getGuestOrders().filter((number) => number !== orderNumber),
    ]
    localStorage.setItem(
      GUEST_ORDERS_KEY,
      JSON.stringify(orders.slice(0, MAX_GUEST_ORDERS)),
    )
  } catch {
    // ignore storage errors
  }
}

export function isGuestOrderAllowed(orderNumber: string): boolean {
  return getGuestOrders().includes(orderNumber)
}
