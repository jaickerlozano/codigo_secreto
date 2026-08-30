import type { CSSProperties } from 'react'

interface ProductMediaStageProps {
  imageUrl: string | null | undefined
  originalImageUrl?: string | null
  isUsingOriginal?: boolean
  showPlaceholder?: boolean
  icon: string
  alt: string
  loading?: 'eager' | 'lazy'
  fetchPriority?: 'high' | 'low' | 'auto'
  sizes?: string
  onImageError?: () => void
  stageTestId?: string
  className?: string
}

export const PRODUCT_MEDIA_STUDIO_CANVAS_STYLE = {
  backgroundColor: '#191329',
  backgroundImage: [
    'radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(8, 5, 18, 0.48) 100%)',
    'radial-gradient(ellipse at 50% 38%, rgba(177, 74, 237, 0.38) 0%, rgba(96, 46, 156, 0.24) 42%, transparent 74%)',
    'linear-gradient(90deg, rgba(0, 102, 128, 0.18) 0%, transparent 22%, transparent 78%, rgba(0, 102, 128, 0.13) 100%)',
  ].join(', '),
} satisfies CSSProperties

export function ProductMediaStage({
  imageUrl,
  originalImageUrl,
  isUsingOriginal = false,
  showPlaceholder = false,
  icon,
  alt,
  loading = 'lazy',
  fetchPriority = 'auto',
  sizes,
  onImageError,
  stageTestId,
  className = '',
}: ProductMediaStageProps) {
  const displayedImageUrl = isUsingOriginal ? originalImageUrl : imageUrl

  return (
    <div
      data-testid={stageTestId}
      className={`flex items-center justify-center ${className}`}
      style={PRODUCT_MEDIA_STUDIO_CANVAS_STYLE}
    >
      {showPlaceholder || !displayedImageUrl ? (
        <div role="img" aria-label={alt}>
          <span
            className="select-none text-7xl opacity-[0.18]"
            aria-hidden="true"
          >
            {icon}
          </span>
          <div
            className="absolute inset-0 opacity-[0.06]"
            style={{ backgroundImage: 'var(--circuit-overlay)' }}
            aria-hidden="true"
          />
        </div>
      ) : (
        <img
          src={displayedImageUrl}
          alt={alt}
          className="relative z-10 h-full w-full object-contain select-none"
          width={1600}
          height={2000}
          sizes={sizes}
          loading={loading}
          fetchPriority={fetchPriority}
          onError={onImageError}
        />
      )}
    </div>
  )
}
