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
export type PaginatedOrderList = components['schemas']['PaginatedOrderList']
export type PaginatedSupplierList = components['schemas']['PaginatedSupplierList']
export type PaginatedStockMovementList = components['schemas']['PaginatedStockMovementList']

export type ApiResponse<T> = T

// JSONField from the backend arrives as an unstructured JSON value.
export type ProductFeature = unknown
