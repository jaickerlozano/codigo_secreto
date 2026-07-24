import type { components } from '@/api/schema.d.ts'
import type { Category, ExperienceLevel, Product } from '../types'
import { getCategoryStyle } from './categoryStyle'

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
  const features = Array.isArray(apiProduct.features)
    ? (apiProduct.features as string[])
    : []

  const rawExperience = (apiProduct as any).experienceLevel || apiProduct.experience_level;
  let finalExperience: ExperienceLevel = 'intermedio';
  
  if (typeof rawExperience === 'string') {
    finalExperience = rawExperience as ExperienceLevel;
  } else if (typeof rawExperience === 'number') {
    const EXPERIENCE_MAP: Record<number, ExperienceLevel> = {
      1: 'principiante',
      2: 'principiante',
      3: 'intermedio',
      4: 'avanzado',
      5: 'avanzado',
    };
    finalExperience = EXPERIENCE_MAP[rawExperience] ?? 'intermedio';
  }

  // Captura el array de imágenes de la API, o un arreglo vacío si el producto no tiene galería
  const apiImages = (apiProduct as any).images 
  const galleryImages = Array.isArray(apiImages) 
    ? apiImages.map((img: any) => ({ id: Number(img.id), image: String(img.image) }))
    : []

  return {
    id: apiProduct.id,
    name: apiProduct.name,
    price: apiProduct.price,
    category: (apiProduct as any).category ?? categoryName ?? 'Sin categoría',
    experienceLevel: finalExperience,
    features,
    description: apiProduct.description ?? '',
    materials: [],
    usageInstructions: '',
    icon: apiProduct.icon ?? '✦',
    gradient:
      apiProduct.gradient ??
      'from-violet-950 via-purple-900 to-violet-800',
    sku: apiProduct.sku ?? null,
    stock: (apiProduct as any).stock ?? apiProduct.current_stock ?? 0,
    image: apiProduct.image ?? null,
    badge: (apiProduct.badge as Product['badge']) ?? undefined,
    images: galleryImages, 
  }
}