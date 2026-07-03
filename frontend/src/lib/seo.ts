export interface SEOConfig {
  title: string
  description: string
  ogImage?: string
  ogType?: 'website' | 'product' | 'article'
  canonical?: string
}

export const defaultSEO = {
  title: 'Código Secreto — Sexshop Chile',
  description:
    'Descubre el placer sin límites. Envío discreto a todo Chile. Productos premium para tu intimidad.',
  ogImage: '/og-image.jpg',
}

export const buildTitle = (pageTitle: string): string => {
  return `${pageTitle} | Código Secreto`
}
