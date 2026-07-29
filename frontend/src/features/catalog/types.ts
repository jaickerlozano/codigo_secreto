import type { components } from '@/api/schema.d.ts'

type ApiProduct = components['schemas']['Product']
type ApiCategory = components['schemas']['Category']

export type ExperienceLevel = 'principiante' | 'intermedio' | 'avanzado'

export interface Product extends
  Omit<ApiProduct, 'features' | 'description' | 'image' | 'badge' | 'experienceLevel' | 'current_stock' | 'minimum_stock' | 'supplier' | 'created_at' | 'updated_at'> {
  originalPrice?: number
  features: string[]
  description: string
  image: string | null
  badge?: 'discount' | 'new' | 'popular'
  experienceLevel: ExperienceLevel
  materials: string[]
  usageInstructions: string
  isNew?: boolean
  isOnSale?: boolean
  /** Extended fields preserved from the original Figma Make catalog UI. */
  rating?: number
  reviewCount?: number
  shortDesc?: string
}

export interface Category extends Pick<ApiCategory, 'id' | 'name'> {
  icon: string
  gradient: string
  count?: number
}

export interface Review {
  id: string
  name: string
  rating: number
  text: string
  avatar?: string
  date?: string
}
