import type { components } from '@/api/schema.d.ts'
import type { Category, ExperienceLevel, Product } from '../types'
import { getCategoryStyle } from './categoryStyle'

// Tipo auxiliar para los campos que vienen del backend pero no están
// correctamente tipados en el schema generado (skipLibCheck=true).
interface RawProduct {
  id: number
  name: string
  price: number
  description: string | null
  image: string | null
  images: Array<{ id: number; image: string }> | null
  gradient: string | null
  icon: string | null
  badge: string | null
  features: string[] | null
  category: string | null
  stock: number | null
  current_stock: number | null
  sku: string | null
  experienceLevel: number | string | null
  experience_level: number | string | null
}

const SCHEMA_FIELDS: ReadonlyArray<keyof RawProduct> = [
  'id', 'name', 'price', 'description', 'image', 'images',
  'gradient', 'icon', 'badge', 'features', 'category',
  'stock', 'current_stock', 'sku', 'experienceLevel', 'experience_level',
]

// Esta función es vital para que carguen las secciones de categorías
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

// Mapeador de productos optimizado para Django Serializer
export function mapApiProduct(
  apiProduct: components['schemas']['Product'],
  categoryName?: string,
): Product {
  const raw = apiProduct as unknown as RawProduct

  const features = Array.isArray(raw.features) ? raw.features : []

  const rawExperience = raw.experienceLevel ?? raw.experience_level
  let finalExperience: ExperienceLevel = 'intermedio'

  if (typeof rawExperience === 'string') {
    finalExperience = rawExperience as ExperienceLevel
  } else if (typeof rawExperience === 'number') {
    const EXPERIENCE_MAP: Record<number, ExperienceLevel> = {
      1: 'principiante',
      2: 'principiante',
      3: 'intermedio',
      4: 'avanzado',
      5: 'avanzado',
    }
    finalExperience = EXPERIENCE_MAP[rawExperience] ?? 'intermedio'
  }

  // Captura el array de imágenes de la API, o un arreglo vacío si el producto no tiene galería
  const apiImages = Array.isArray(raw.images)
    ? raw.images
        .map((img) => ({
          id: Number(img?.id ?? 0),
          image: typeof img?.image === 'string' ? img.image.trim() : '',
        }))
        .filter((img) => Boolean(img.image))
    : []

  const primaryImage =
    typeof raw.image === 'string' && raw.image.trim()
      ? raw.image.trim()
      : apiImages[0]?.image ?? null

  return {
    id: raw.id,
    name: raw.name,
    price: raw.price,
    category: raw.category ?? categoryName ?? 'Sin categoría',
    experienceLevel: finalExperience,
    features,
    description: raw.description ?? '',
    materials: [],
    usageInstructions: '',
    icon: raw.icon ?? '✦',
    gradient: raw.gradient ?? 'from-violet-950 via-purple-900 to-violet-800',
    sku: raw.sku ?? null,
    stock: raw.stock ?? raw.current_stock ?? 0,
    image: primaryImage,
    badge: (raw.badge as Product['badge']) ?? undefined,
    images: apiImages,
  }
}