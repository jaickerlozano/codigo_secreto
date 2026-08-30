export type ExperienceLevel = 'principiante' | 'intermedio' | 'avanzado'

export interface Product {
  id: number
  name: string
  price: number
  originalPrice?: number
  category: string
  experienceLevel: ExperienceLevel
  features: string[]
  description: string
  materials: string[]
  usageInstructions: string
  icon: string
  gradient: string
  isNew?: boolean
  isOnSale?: boolean
  badge?: 'discount' | 'new' | 'popular'
  /** Extended fields preserved from the original Figma Make catalog UI. */
  rating?: number
  reviewCount?: number
  shortDesc?: string
  /** Fields coming from the backend Product model. */
  sku: string | null
  stock: number
  image: string | null
  imageOriginal?: string | null
  /** Gallery images array from ProductImage model. */
  images: Array<{ id: number; image: string; imageOriginal?: string | null }>
}

export interface Category {
  id: number
  name: string
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
