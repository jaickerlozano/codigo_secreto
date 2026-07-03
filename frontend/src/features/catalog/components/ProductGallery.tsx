import { useState } from 'react'
import { motion } from 'motion/react'

import type { Product } from '../types'

interface ProductGalleryProps {
  product: Product
}

export function ProductGallery({ product }: ProductGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)

  // El catálogo mock tiene un placeholder gradiente por producto.
  // La estructura permite extender a múltiples imágenes sin cambiar la API.
  const images = [
    {
      gradient: product.gradient,
      icon: product.icon,
      alt: product.name,
    },
  ]

  const currentImage = images[selectedIndex]

  return (
    <div className="space-y-4">
      <motion.div
        key={selectedIndex}
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className={`relative flex aspect-square items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br ${currentImage.gradient}`}
      >
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
      </motion.div>

      {images.length > 1 && (
        <div className="flex gap-3">
          {images.map((image, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setSelectedIndex(index)}
              aria-label={`Ver imagen ${index + 1} de ${images.length}`}
              aria-current={selectedIndex === index}
              className={`relative rounded-xl p-1 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                selectedIndex === index
                  ? 'ring-2 ring-neon-magenta'
                  : 'opacity-70 hover:opacity-100'
              }`}
            >
              <div
                className={`flex h-16 w-16 items-center justify-center rounded-lg bg-gradient-to-br ${image.gradient}`}
              >
                <span
                  className="select-none text-2xl opacity-40"
                  aria-hidden="true"
                >
                  {image.icon}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
