import { useEffect } from 'react'
import { useLocation, useNavigationType } from 'react-router'

const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)'
const ACCESS_FRAGMENT_PATTERN = /(?:^|&)access=/

function isOpaqueAccessFragment(hash: string): boolean {
  return ACCESS_FRAGMENT_PATTERN.test(hash.slice(1))
}

function getHashTarget(hash: string): HTMLElement | null {
  if (!hash || isOpaqueAccessFragment(hash)) return null

  try {
    return document.getElementById(decodeURIComponent(hash.slice(1)))
  } catch {
    return null
  }
}

export function scrollToPageTop(): void {
  const prefersReducedMotion = window.matchMedia?.(REDUCED_MOTION_QUERY).matches
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: prefersReducedMotion ? 'auto' : 'smooth',
  })
}

export function useScrollToTopOnNavigate(): void {
  const location = useLocation()
  const navigationType = useNavigationType()

  useEffect(() => {
    if (navigationType === 'POP') return
    if (getHashTarget(location.hash)) return

    scrollToPageTop()
  }, [location.key, location.hash, navigationType])
}
