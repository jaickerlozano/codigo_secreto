import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'

import type { Product } from '../types'

interface ProductGalleryProps {
  product: Product
}

export function ProductGallery({ product }: ProductGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [imgError, setImgError] = useState<Set<number>>(new Set())

  useEffect(() => {
    setSelectedIndex(0)
    setImgError(new Set())
  }, [product.id])

  const images = [
    ...(product.image
      ? [
          {
            url: product.image,
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
        gradient: product.gradient,
        icon: product.icon,
        alt: `${product.name} - Vista adicional`,
      })),
  ]

  const showPlaceholder = (index: number) => imgError.has(index) || !images[index]?.url

  const currentImage =
    images[selectedIndex] ??
    images[0] ?? {
      url: '',
      gradient: product.gradient,
      icon: product.icon,
      alt: product.name,
    }

  return (
    <div className="space-y-4">
      {/* ─── CONTENEDOR PRINCIPAL DE LA IMAGEN ─── */}
      <div className="relative w-full overflow-hidden rounded-2xl border border-border aspect-[3/4] max-h-[70dvh] lg:aspect-[4/5] lg:max-h-[75dvh]">
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedIndex}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className={`absolute inset-0 flex items-center justify-center bg-gradient-to-br ${currentImage.gradient}`}
          >
            {showPlaceholder(selectedIndex) ? (
              <>
                <span
                  className="select-none text-9xl opacity-[0.18]"
                  aria-hidden="true"
                >
                  {currentImage.icon}
                </span>
                <div
                  className="absolute inset-0 opacity-[0.05]"
                  style={{
                    backgroundImage: 'var(--circuit-overlay)',
                  }}
                  aria-hidden="true"
                />
              </>
            ) : (
              <img
                src={currentImage.url}
                alt={currentImage.alt}
                className="h-full w-full object-cover select-none"
                onError={() =>
                  setImgError((prev) => new Set(prev).add(selectedIndex))
                }
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ─── CARRUSEL DE MINIATURAS INTERACTIVAS (THUMBNAILS) ─── */}
      {images.length > 1 && (
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
                        src={image.url}
                        alt=""
                        className="h-full w-full object-cover select-none"
                        loading="lazy"
                        onError={() =>
                          setImgError((prev) => new Set(prev).add(index))
                        }
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
