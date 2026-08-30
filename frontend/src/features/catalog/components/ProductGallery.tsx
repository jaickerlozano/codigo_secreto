import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { motion, AnimatePresence } from 'motion/react'

import { useReducedMotion } from '@/hooks/useReducedMotion'
import type { Product } from '../types'
import { ProductMediaStage } from './ProductMediaStage'

interface ProductGalleryProps {
  product: Product
}

export function ProductGallery({ product }: ProductGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [imgError, setImgError] = useState<Set<number>>(new Set())
  const [fallbackImageIndexes, setFallbackImageIndexes] = useState<Set<number>>(new Set())
  const shouldReduceMotion = useReducedMotion()

  useEffect(() => {
    setSelectedIndex(0)
    setImgError(new Set())
    setFallbackImageIndexes(new Set())
  }, [product.id])

  const images = [
    ...(product.image
      ? [
          {
            url: product.image,
            originalUrl: product.imageOriginal,
            gradient: product.gradient,
            icon: product.icon,
            alt: product.name,
          },
        ]
      : []),
    ...product.images
      .filter((img) => Boolean(img.image))
      .map((img) => ({
        url: img.image,
        originalUrl: img.imageOriginal,
        gradient: product.gradient,
        icon: product.icon,
        alt: `${product.name} - Vista adicional`,
      })),
  ]

  const currentImage = images[selectedIndex] ??
    images[0] ?? {
      url: '',
      originalUrl: null,
      gradient: product.gradient,
      icon: product.icon,
      alt: product.name,
    }

  const isUsingOriginal = fallbackImageIndexes.has(selectedIndex)
  const showPlaceholder = (index: number) =>
    imgError.has(index) || !images[index]?.url

  const imageUrlFor = (index: number) => {
    const image = images[index]
    return (fallbackImageIndexes.has(index) ? image?.originalUrl : image?.url) ?? undefined
  }

  const showImageControls = images.length > 1

  const showPreviousImage = () => {
    setSelectedIndex((previousIndex) =>
      previousIndex === 0 ? images.length - 1 : previousIndex - 1
    )
  }

  const showNextImage = () => {
    setSelectedIndex((previousIndex) =>
      previousIndex === images.length - 1 ? 0 : previousIndex + 1
    )
  }

  const handleImageError = (index: number) => {
    const image = images[index]
    if (
      !fallbackImageIndexes.has(index) &&
      image?.originalUrl &&
      image.originalUrl !== image.url
    ) {
      setFallbackImageIndexes((previous) => new Set(previous).add(index))
      return
    }
    setImgError((previous) => new Set(previous).add(index))
  }

  return (
    <div className="space-y-4">
      <div
        data-testid="product-gallery-stage"
        className="relative mx-auto aspect-[4/5] w-full max-w-[42rem] overflow-hidden rounded-2xl border border-border bg-base-900 max-h-[calc(100dvh-8rem)] sm:aspect-square lg:aspect-[4/5]"
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedIndex}
            initial={{ opacity: 0, scale: shouldReduceMotion ? 1 : 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.25 }}
            className="absolute inset-0"
          >
            <ProductMediaStage
              imageUrl={currentImage.url}
              originalImageUrl={currentImage.originalUrl}
              isUsingOriginal={isUsingOriginal}
              showPlaceholder={showPlaceholder(selectedIndex)}
              icon={currentImage.icon}
              alt={currentImage.alt}
              loading={selectedIndex === 0 ? 'eager' : 'lazy'}
              fetchPriority={selectedIndex === 0 ? 'high' : 'auto'}
              sizes="(min-width: 1024px) 42rem, (min-width: 640px) 50vw, 100vw"
              onImageError={() => handleImageError(selectedIndex)}
              className="h-full w-full"
            />
          </motion.div>
        </AnimatePresence>

        {showImageControls && (
          <>
            <button
              type="button"
              onClick={showPreviousImage}
              aria-label="Ver imagen anterior"
              className="absolute left-3 top-1/2 z-20 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-base-900/80 text-foreground shadow-md backdrop-blur-sm transition-colors hover:border-neon-cyan hover:text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-magenta focus-visible:ring-offset-2 focus-visible:ring-offset-base-900"
            >
              <ChevronLeft size={24} aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={showNextImage}
              aria-label="Ver imagen siguiente"
              className="absolute right-3 top-1/2 z-20 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-base-900/80 text-foreground shadow-md backdrop-blur-sm transition-colors hover:border-neon-cyan hover:text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-magenta focus-visible:ring-offset-2 focus-visible:ring-offset-base-900"
            >
              <ChevronRight size={24} aria-hidden="true" />
            </button>
            <p
              aria-live="polite"
              className="absolute bottom-3 left-1/2 z-20 -translate-x-1/2 rounded-full border border-white/10 bg-base-900/80 px-3 py-1 text-xs font-medium tabular-nums text-foreground backdrop-blur-sm"
            >
              {selectedIndex + 1} / {images.length}
            </p>
          </>
        )}
      </div>

      {showImageControls && (
        <nav aria-label="Galería de imágenes" className="w-full">
          <div
            className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none snap-x"
            style={{ scrollbarWidth: 'none' }}
          >
            {images.map((image, index) => {
              const isSelected = selectedIndex === index
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => setSelectedIndex(index)}
                  aria-label={`Ver imagen ${index + 1} de ${images.length}`}
                  aria-current={isSelected}
                  className={`relative shrink-0 snap-start rounded-xl p-1 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-magenta ${
                    isSelected
                      ? 'ring-2 ring-neon-magenta shadow-[0_0_12px_rgba(255,43,214,0.25)]'
                      : 'opacity-60 hover:opacity-100'
                  }`}
                >
                  <div
                    className={`flex h-16 w-16 items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br ${image.gradient}`}
                  >
                    {showPlaceholder(index) ? (
                      <span
                        className="select-none text-2xl opacity-40"
                        aria-hidden="true"
                      >
                        {image.icon}
                      </span>
                    ) : (
                      <img
                        src={imageUrlFor(index)}
                        alt=""
                        className="h-full w-full object-cover select-none"
                        width={64}
                        height={64}
                        sizes="64px"
                        loading={index === 0 ? 'eager' : 'lazy'}
                        onError={() => handleImageError(index)}
                      />
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </nav>
      )}
    </div>
  )
}
