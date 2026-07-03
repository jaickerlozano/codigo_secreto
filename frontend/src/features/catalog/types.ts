export type ExperienceLevel = 'principiante' | 'intermedio' | 'avanzado'

export interface Product {
  id: string
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
  /** Extended fields preserved from the original Figma Make catalog UI. */
  rating?: number
  reviewCount?: number
  shortDesc?: string
}

export interface Category {
  id: string
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
