import type { paths, components, operations } from '@/api/schema.d.ts'

export type { paths, components, operations }

export type Product = components['schemas']['Product']
export type Category = components['schemas']['Category']
export type Region = components['schemas']['Region']
export type Comuna = components['schemas']['Comuna']
export type Order = components['schemas']['Order']
export type CartItem = components['schemas']['CartItem']
export type Supplier = components['schemas']['Supplier']
export type StockMovement = components['schemas']['StockMovement']

export type PaginatedProductList = components['schemas']['PaginatedProductList']
export type PaginatedCategoryList = components['schemas']['PaginatedCategoryList']
export type PaginatedRegionList = components['schemas']['PaginatedRegionList']
export type PaginatedComunaList = components['schemas']['PaginatedComunaList']
export type PaginatedOrderList = components['schemas']['PaginatedOrderList']
export type PaginatedSupplierList = components['schemas']['PaginatedSupplierList']
export type PaginatedStockMovementList = components['schemas']['PaginatedStockMovementList']

export type ApiResponse<T> = T

// Generic fallback for hooks that abstract over entity-specific paginated
// schema types (e.g. PaginatedProductList, PaginatedOrderList, ...).
export type PaginatedResponse<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type ApiError = {
  detail: string
  code?: string
}

// JSONField from the backend arrives as an unstructured JSON value.
export type ProductFeature = unknown
