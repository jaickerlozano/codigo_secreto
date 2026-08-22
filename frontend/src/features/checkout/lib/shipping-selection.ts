import type { DispatchOptions } from '@/features/shipping/types'

import type { ShippingData } from '../types'

const WEEKDAYS = [
  'domingo',
  'lunes',
  'martes',
  'miércoles',
  'jueves',
  'viernes',
  'sábado',
]

const MONTHS = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
]

// A dispatch selection is valid only against the backend-provided options:
// Santiago accepts a listed standard date or a future special date, regional
// accepts exactly the active option id. Amounts are never computed here.
export function isDispatchSelectionValid(
  selection: ShippingData,
  options: DispatchOptions
): boolean {
  if (options.mode === 'regional') {
    return (
      selection.shippingOptionId !== undefined &&
      selection.shippingOptionId !== null &&
      options.shippingOption !== null &&
      selection.shippingOptionId === options.shippingOption.shippingOptionId &&
      selection.requestedDispatchDate == null &&
      selection.deliveryKind !== 'special'
    )
  }
  if (selection.deliveryKind === 'special') {
    return (
      typeof selection.requestedDispatchDate === 'string' &&
      selection.requestedDispatchDate.length > 0 &&
      selection.shippingOptionId == null
    )
  }
  if (selection.deliveryKind === 'standard') {
    return (
      typeof selection.requestedDispatchDate === 'string' &&
      options.dates?.includes(selection.requestedDispatchDate) === true &&
      selection.shippingOptionId == null
    )
  }
  return false
}

// Renders a backend ISO date (YYYY-MM-DD) as a Spanish dispatch label without
// timezone shifts; malformed input is returned unchanged.
export function formatDispatchDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate)
  if (!match) return isoDate
  const [, year, month, day] = match
  const date = new Date(Number(year), Number(month) - 1, Number(day))
  return `${WEEKDAYS[date.getDay()]} ${Number(day)} de ${MONTHS[Number(month) - 1]}`
}
