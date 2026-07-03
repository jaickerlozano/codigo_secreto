import { useEffect } from 'react'

import { buildTitle, defaultSEO, type SEOConfig } from '@/lib/seo'

interface SEOProps extends Partial<SEOConfig> {
  pageTitle?: string
}

export function SEO({
  pageTitle,
  title = defaultSEO.title,
  description = defaultSEO.description,
  ogImage = defaultSEO.ogImage,
  ogType = 'website',
}: SEOProps) {
  const documentTitle = pageTitle ? buildTitle(pageTitle) : title

  useEffect(() => {
    document.title = documentTitle

    const setMeta = (name: string, content: string) => {
      let element = document.querySelector(
        `meta[name="${name}"], meta[property="${name}"]`,
      ) as HTMLMetaElement | null
      if (!element) {
        element = document.createElement('meta')
        if (name.startsWith('og:')) {
          element.setAttribute('property', name)
        } else {
          element.setAttribute('name', name)
        }
        document.head.appendChild(element)
      }
      element.setAttribute('content', content)
    }

    setMeta('description', description)
    setMeta('og:title', documentTitle)
    setMeta('og:description', description)
    setMeta('og:type', ogType)
    setMeta('og:image', ogImage)
  }, [documentTitle, description, ogImage, ogType])

  return null
}
