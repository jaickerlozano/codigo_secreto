import { act, render, waitFor } from '@testing-library/react'
import { createMemoryRouter, Outlet, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useScrollToTopOnNavigate } from './useScrollToTopOnNavigate'

function ScrollHarness() {
  useScrollToTopOnNavigate()
  return <Outlet />
}

function createHarnessRouter(initialEntries = ['/catalog']) {
  return createMemoryRouter(
    [
      {
        path: '/',
        element: <ScrollHarness />,
        children: [
          { path: '*', element: <div>Route content</div> },
        ],
      },
    ],
    { initialEntries },
  )
}

function scrollToMock() {
  return vi.mocked(window.scrollTo)
}

describe('useScrollToTopOnNavigate', () => {
  beforeEach(() => {
    scrollToMock().mockClear()
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  })

  it('scrolls to the top for PUSH and REPLACE navigation, including search changes', async () => {
    const router = createHarnessRouter()
    render(<RouterProvider router={router} />)

    await act(() => router.navigate('/products'))
    await waitFor(() => expect(scrollToMock()).toHaveBeenCalledTimes(1))

    await act(() => router.navigate('/products?search=neon', { replace: true }))
    await waitFor(() => expect(scrollToMock()).toHaveBeenCalledTimes(2))
    expect(scrollToMock()).toHaveBeenLastCalledWith({
      top: 0,
      left: 0,
      behavior: 'smooth',
    })
  })

  it('does not override POP navigation scroll restoration', async () => {
    const router = createHarnessRouter(['/catalog', '/products'])
    render(<RouterProvider router={router} />)

    scrollToMock().mockClear()
    await act(() => router.navigate(-1))

    await waitFor(() => expect(router.state.location.pathname).toBe('/catalog'))
    expect(scrollToMock()).not.toHaveBeenCalled()
  })

  it('leaves a real hash target to native browser navigation', async () => {
    const target = document.createElement('section')
    target.id = 'shipping-details'
    document.body.append(target)
    const router = createHarnessRouter()
    render(<RouterProvider router={router} />)

    await act(() => router.navigate('/products#shipping-details'))

    expect(scrollToMock()).not.toHaveBeenCalled()
    target.remove()
  })

  it('treats an opaque order access fragment as tracking data, not an anchor', async () => {
    const getElementById = vi.spyOn(document, 'getElementById')
    const router = createHarnessRouter()
    render(<RouterProvider router={router} />)

    await act(() =>
      router.navigate('/order/CS-123456#access=private-capability-token'),
    )

    await waitFor(() => expect(scrollToMock()).toHaveBeenCalledTimes(1))
    expect(getElementById).not.toHaveBeenCalled()
    getElementById.mockRestore()
  })

  it('uses instant scrolling when reduced motion is requested', async () => {
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
    const router = createHarnessRouter()
    render(<RouterProvider router={router} />)

    await act(() => router.navigate('/products'))

    await waitFor(() =>
      expect(scrollToMock()).toHaveBeenCalledWith({
        top: 0,
        left: 0,
        behavior: 'auto',
      }),
    )
  })
})
