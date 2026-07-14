import type { components } from '@/api/schema.d.ts'
import type { Category, ExperienceLevel, Product } from '../types'
import { getCategoryStyle } from './categoryStyle'

const EXPERIENCE_MAP: Record<number, ExperienceLevel> = {
  1: 'principiante',
  2: 'principiante',
  3: 'intermedio',
  4: 'avanzado',
  5: 'avanzado',
}

export function mapApiCategory(
  apiCategory: components['schemas']['Category'],
): Category {
  const style = getCategoryStyle(apiCategory.name)

  return {
    id: apiCategory.id,
    name: apiCategory.name,
    icon: style.icon,
    gradient: style.gradient,
  }
}

export function mapApiProduct(
  apiProduct: components['schemas']['Product'],
  categoryName?: string,
): Product {
  const features = Array.isArray(apiProduct.features)
    ? (apiProduct.features as string[])
    : []

  return {
    id: apiProduct.id,
    name: apiProduct.name,
    price: apiProduct.price,
    category: categoryName ?? 'Sin categoría',
    experienceLevel:
      EXPERIENCE_MAP[apiProduct.experience_level ?? 3] ?? 'intermedio',
    features,
    description: apiProduct.description ?? '',
    materials: [],
    usageInstructions: '',
    icon: apiProduct.icon ?? '✦',
    gradient:
      apiProduct.gradient ??
      'from-violet-950 via-purple-900 to-violet-800',
    sku: apiProduct.sku ?? null,
    stock: apiProduct.current_stock ?? 0,
    image: apiProduct.image ?? null,
    badge: (apiProduct.badge as Product['badge']) ?? undefined,
  }
}
