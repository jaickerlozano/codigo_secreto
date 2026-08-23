import { expect, test, type CDPSession, type Page } from '@playwright/test'

/**
 * Acceptance: "Operate and scroll at runtime" (checkout-address controls). In a
 * constrained viewport with more options than fit, owned scrolling MUST reach
 * the final option via wheel, keyboard, type-ahead and touch, and the chosen
 * value MUST persist/advance. Runs the REAL checkout address step (StepAddress)
 * with the REAL Radix Select in a real Chromium layout — the acceptance jsdom
 * cannot compute. Network/backend mocked at the browser boundary (page.route);
 * no credentials, token storage, manual API types, `any`, or money math.
 */

const CART_KEY = 'cs-cart'

// 16 regions x 48px items exceed the ~490px owned-scroll window.
const REGION_NAMES = [
  'Arica y Parinacota', 'Tarapacá', 'Antofagasta', 'Atacama', 'Coquimbo',
  'Valparaíso', "Libertador General Bernardo O'Higgins", 'Maule', 'Ñuble',
  'Biobío', 'La Araucanía', 'Los Ríos', 'Los Lagos',
  'Aysén del General Carlos Ibáñez del Campo',
  'Magallanes y de la Antártica Chilena', 'Región Metropolitana de Santiago',
]
const REGIONS = REGION_NAMES.map((name, i) => ({
  id: i + 1,
  name,
  ordinal_number: i + 1,
}))
const LAST_REGION = REGIONS[REGIONS.length - 1].name

// 32 comunas: the FINAL option "Tiltil" sits ~1.5k px below the top of the
// listbox, reachable only through Radix owned scrolling.
const COMUNA_NAMES = [
  'Santiago', 'Providencia', 'Las Condes', 'Vitacura', 'Lo Barnechea', 'Ñuñoa',
  'La Reina', 'Macul', 'Peñalolén', 'La Florida', 'Puente Alto', 'San Bernardo',
  'Maipú', 'Cerrillos', 'Estación Central', 'Quinta Normal', 'Lo Prado',
  'Cerro Navia', 'Renca', 'Quilicura', 'Conchalí', 'Independencia', 'Recoleta',
  'Huechuraba', 'La Pintana', 'El Bosque', 'La Granja', 'San Joaquín',
  'San Miguel', 'Lo Espejo', 'Pedro Aguirre Cerda', 'Tiltil',
]
const COMUNAS = COMUNA_NAMES.map((name, index) => ({
  id: 101 + index,
  name,
  shipping_cost: 3500,
  is_active: true,
}))
const LAST_COMUNA = COMUNAS[COMUNAS.length - 1].name

// Guest cart product (frontend Product shape persisted by the real cart store).
const GUEST_PRODUCT = {
  id: 1, name: 'Vibrador E2E', price: 29990, category: 'Vibradores',
  experienceLevel: 'principiante', features: [], description: 'Producto de prueba E2E',
  materials: [], usageInstructions: 'Uso de prueba', icon: '✦',
  gradient: 'from-violet-950 via-purple-900 to-violet-800', sku: 'E2E-1',
  stock: 10, image: null, images: [],
}

async function mockApi(page: Page): Promise<void> {
  // Mock real /api/* paths at the browser boundary; fall through for assets
  // (a glob like **/api/** would also match source modules in auth/api).
  await page.route('**/*', async (route) => {
    const { pathname } = new URL(route.request().url())
    if (!pathname.startsWith('/api/')) return route.fallback()
    const method = route.request().method()
    const respond = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
    if (pathname === '/api/auth/me/' && method === 'GET')
      return respond(401, { detail: 'no session' })
    if (pathname === '/api/shipping/regions/' && method === 'GET')
      return respond(200, { count: REGIONS.length, next: null, previous: null, results: REGIONS })
    if (pathname === '/api/shipping/comunas/' && method === 'GET')
      return respond(200, { count: COMUNAS.length, next: null, previous: null, results: COMUNAS })
    if (pathname === '/api/orders/quote/' && method === 'POST')
      return respond(200, { items: [], subtotal: 29990, shipping_cost: 3500, total: 33490, revision: 'e2e-quote-1' })
    if (pathname === '/api/shipping/dispatch-options/' && method === 'GET')
      return respond(200, { comuna_id: 132, mode: 'santiago', dates: ['2026-09-01', '2026-09-03', '2026-09-08', '2026-09-10'], shipping_option: null })
    return respond(404, { detail: 'not mocked' })
  })
}

/** Seed guest cart + age verification through the app's own localStorage keys. */
async function seedGuestCart(page: Page): Promise<void> {
  await page.addInitScript(
    ([key, product]) => {
      localStorage.setItem('cs-age-verified', 'true')
      localStorage.setItem(
        key,
        JSON.stringify({ state: { items: [{ product, quantity: 1 }], mode: 'guest' }, version: 0 })
      )
    },
    [CART_KEY, GUEST_PRODUCT]
  )
}

/** Walk the real checkout to the address step (contact -> address). */
async function openCheckoutAddress(page: Page): Promise<void> {
  await page.goto('/checkout')
  await page.locator('#contact-name').fill('E2E Usuario')
  await page.locator('#contact-email').fill('e2e@example.com')
  await page.locator('#contact-phone').fill('+56 9 1234 5678')
  await page.getByRole('button', { name: 'Siguiente' }).click()
  await expect(page.getByRole('group', { name: 'Dirección de envío' })).toBeVisible()
}

// Radix Select Viewport (role="presentation") is the owned-scroll scrollport.
const viewportOf = (page: Page) =>
  page.locator('[data-slot="select-content"] > [role="presentation"]')

/** True when the option's box intersects the owned-scroll viewport box. */
async function optionVisibleInList(page: Page, name: string): Promise<boolean> {
  const viewportBox = await viewportOf(page).boundingBox()
  const optionBox = await page.getByRole('option', { name }).boundingBox()
  if (!viewportBox || !optionBox) return false
  return (
    optionBox.y < viewportBox.y + viewportBox.height - 2 &&
    optionBox.y + optionBox.height > viewportBox.y + 2
  )
}

/** The owned-scroll viewport (Radix Select) must overflow the constrained viewport. */
async function expectOwnedScrollOverflow(page: Page): Promise<void> {
  const dims = await viewportOf(page).evaluate((el) => ({
    scrollHeight: el.scrollHeight,
    clientHeight: el.clientHeight,
  }))
  expect(dims.scrollHeight).toBeGreaterThan(dims.clientHeight)
}

/** Radix unmounts closed content only after its close animation. */
const expectSelectClosed = (page: Page) =>
  expect(page.locator('[data-slot="select-content"]')).toHaveCount(0)

async function touchSwipeUp(client: CDPSession, box: { x: number; y: number; width: number; height: number }) {
  const x = box.x + box.width / 2
  const fromY = box.y + box.height - 30
  const toY = box.y + box.height - 230
  await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: fromY }] })
  for (let y = fromY - 20; y > toY; y -= 12) {
    await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y }] })
    await new Promise((resolve) => setTimeout(resolve, 8))
  }
  await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
}

test('wheel scrolls the region listbox to the final option and click selects it', async ({ page }) => {
  await seedGuestCart(page)
  await mockApi(page)
  await openCheckoutAddress(page)

  const trigger = page.locator('#address-region')
  await trigger.click()
  await expect(page.getByRole('listbox')).toBeVisible()
  await expectOwnedScrollOverflow(page)

  // Bounded scrolling: the final region is NOT visible before scrolling.
  expect(await optionVisibleInList(page, LAST_REGION)).toBe(false)

  // Wheel over the listbox reaches the final option.
  const viewportBox = await viewportOf(page).boundingBox()
  if (!viewportBox) throw new Error('listbox viewport has no box')
  await page.mouse.move(viewportBox.x + viewportBox.width / 2, viewportBox.y + viewportBox.height / 2)
  await expect
    .poll(async () => {
      if (await optionVisibleInList(page, LAST_REGION)) return true
      await page.mouse.wheel(0, 300)
      return false
    })
    .toBe(true)

  // The reached final option is selectable and the trigger reflects it.
  await page.getByRole('option', { name: LAST_REGION }).click()
  await expect(trigger).toContainText(LAST_REGION)
  // Dependent comuna control becomes enabled once a region is owned.
  await expect(page.locator('#address-comuna')).toBeEnabled()
  await expectSelectClosed(page)
})

test('keyboard arrows reach the final comuna; selection persists after reopen', async ({ page }) => {
  await seedGuestCart(page)
  await mockApi(page)
  await openCheckoutAddress(page)

  // Own a region first so the comuna cascade is enabled.
  await page.locator('#address-region').click()
  await page.getByRole('option', { name: REGIONS[0].name }).click()
  await expect(page.locator('#address-comuna')).toBeEnabled()
  await expectSelectClosed(page)

  const trigger = page.locator('#address-comuna')
  await trigger.click()
  await expect(page.getByRole('listbox')).toBeVisible()
  await expectOwnedScrollOverflow(page)
  expect(await optionVisibleInList(page, LAST_COMUNA)).toBe(false)

  // Arrow keys drive Radix owned scrolling until the final option is focused.
  for (let i = 0; i < COMUNAS.length + 2; i += 1) {
    const highlighted = await page.getByRole('option', { name: LAST_COMUNA }).getAttribute('data-highlighted')
    if (highlighted !== null) break
    await page.keyboard.press('ArrowDown')
  }
  await expect(page.getByRole('option', { name: LAST_COMUNA })).toHaveAttribute('data-highlighted', '')

  // Enter owns the value; checked state is asserted on reopen after Escape.
  await page.keyboard.press('Enter')
  await expect(trigger).toContainText(LAST_COMUNA)
  await page.keyboard.press('Escape')
  await expect(page.getByRole('listbox')).not.toBeVisible()
  await expect(trigger).toContainText(LAST_COMUNA)
  await expectSelectClosed(page)

  // Reopen: the owned value is still marked selected.
  await trigger.click()
  await expect(page.getByRole('listbox')).toBeVisible()
  await expect(page.getByRole('option', { name: LAST_COMUNA })).toHaveAttribute('data-state', 'checked')
  await page.keyboard.press('Escape')
  await expectSelectClosed(page)

  // Selecting another region clears the dependent comuna (runtime half of
  // "Select and reset address").
  await page.locator('#address-region').click()
  await page.getByRole('option', { name: 'Coquimbo' }).click()
  await expect(trigger).not.toContainText(LAST_COMUNA)
  await expect(trigger).toContainText('Seleccionar...')
  await expectSelectClosed(page)
})

test('type-ahead reaches the final option and the chosen value advances the flow', async ({ page }) => {
  await seedGuestCart(page)
  await mockApi(page)
  await openCheckoutAddress(page)

  await page.locator('#address-region').click()
  await page.getByRole('option', { name: REGIONS[0].name }).click()
  await expect(page.locator('#address-comuna')).toBeEnabled()
  await expectSelectClosed(page)

  // Type-ahead jumps focus to the single option starting with "T" (Tiltil).
  await page.locator('#address-comuna').click()
  await expect(page.getByRole('listbox')).toBeVisible()
  await page.keyboard.type('t', { delay: 0 })
  await expect(page.getByRole('option', { name: LAST_COMUNA })).toHaveAttribute('data-highlighted', '')
  await page.keyboard.press('Enter')
  await expect(page.locator('#address-comuna')).toContainText(LAST_COMUNA)

  // The owned value advances: the Envío step renders the destination and the
  // backend Santiago schedule for the selected comuna.
  await page.locator('#address-street').fill('Av. Siempre Viva 123')
  await page.getByRole('button', { name: 'Siguiente' }).click()
  await expect(page.getByRole('radiogroup', { name: 'Fecha de despacho' })).toBeVisible()
  await expect(page.locator('strong', { hasText: LAST_COMUNA })).toHaveText(LAST_COMUNA)
})

test.describe('touch', () => {
  test.use({ hasTouch: true })

  test('touch swipes reach and select the final region; value persists on reopen', async ({ page }) => {
    await seedGuestCart(page)
    await mockApi(page)
    await openCheckoutAddress(page)

    const trigger = page.locator('#address-region')
    const triggerBox = await trigger.boundingBox()
    if (!triggerBox) throw new Error('region trigger has no box')
    await page.touchscreen.tap(triggerBox.x + triggerBox.width / 2, triggerBox.y + triggerBox.height / 2)
    await expect(page.getByRole('listbox')).toBeVisible()
    await expectOwnedScrollOverflow(page)
    // Final option starts OUTSIDE the owned scrollport.
    expect(await optionVisibleInList(page, LAST_REGION)).toBe(false)

    // Bounded genuine touch swipes (CDP trusted events) drive owned scrolling.
    const client = await page.context().newCDPSession(page)
    const vp = await viewportOf(page).boundingBox()
    if (!vp) throw new Error('listbox viewport has no box')
    await expect
      .poll(async () => {
        if (await optionVisibleInList(page, LAST_REGION)) return true
        await touchSwipeUp(client, vp)
        return false
      })
      .toBe(true)

    // The touched final option is selectable and the trigger reflects it.
    await page.getByRole('option', { name: LAST_REGION }).tap()
    await expect(trigger).toContainText(LAST_REGION)
    await expect(page.locator('#address-comuna')).toBeEnabled()
    await expectSelectClosed(page)

    // Persistence: the owned value is still checked on reopen.
    await trigger.click()
    await expect(page.getByRole('listbox')).toBeVisible()
    await expect(page.getByRole('option', { name: LAST_REGION })).toHaveAttribute('data-state', 'checked')
    await page.keyboard.press('Escape')
    await expectSelectClosed(page)
  })
})