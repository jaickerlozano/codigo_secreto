---
name: ui-ux-expert
description: "Trigger: diseño UI, UX, componentes, layouts, checkout, ecommerce, sexshop. Expert UX/UI design for Chilean intimate wellness eCommerce with trust-first patterns."
license: MIT
metadata:
  author: "jaicker"
  version: "1.0"
---

## Activation Contract

Load this skill when:
- Designing UI components, layouts, or views for the Código Secreto frontend
- Building checkout flows, product pages, or category navigation
- Creating design tokens, CSS variables, or component libraries
- Implementing accessibility patterns (WCAG AAA)
- Designing micro-interactions, loading states, or animations
- Any frontend work touching user-facing interfaces

## Hard Rules

1. **Dark-first design**: All UIs default to dark backgrounds (`--color-base-900`). Neon accents on dark = modern, confident, breaks taboos.
2. **Neon as accent, not background**: Neon colors (magenta, cyan, violet, lime) are for CTAs, borders, hover states, and highlights. Never use neon as text background or large surface fills.
3. **Trust through modernity**: The neon palette communicates confidence and normalcy. No shame, no hiding. This is a modern wellness store.
4. **WCAG AAA on dark**: White/light text on dark backgrounds must meet 7:1 contrast. Neon accents must meet 3:1 for UI components.
5. **Privacy by default**: Guest checkout frictionless. Data collection minimized. Packaging/shipping labels never reveal product nature.
6. **Chilean payment integration**: Visual patterns for Flow, Webpay, MercadoPago must follow their official brand guidelines (adapted to dark theme).
7. **Discreet shipping UI**: Shipping options clearly state "embalaje discreto" using neon lime badges — positive, not apologetic.
8. **Education over sales**: Product pages prioritize detailed descriptions, usage guides, material safety info over aggressive CTAs.
9. **Social proof**: Reviews and ratings prominent but not sensationalized.
10. **Mobile-first**: 70%+ of intimate wellness purchases happen on mobile. Touch targets minimum 48x48px.
11. **Glow effects**: Use `--glow-*` tokens sparingly on hover/focus states. Never on static elements. Subtle, not disco.

## Decision Gates

| Need | Pattern |
|------|---------|
| Color palette | Use `assets/design-tokens.css` base tokens. Dark backgrounds + neon accents (magenta primary, cyan secondary, violet tertiary, lime highlights). |
| Typography | `assets/design-tokens.css` → Inter for UI, Playfair Display for headlines. White/light text on dark. |
| Checkout flow | Follow `references/user-journey-map.md` → 5-step discrete checkout with neon progress indicator. |
| Product page | Education-first layout: hero → description → materials/safety → reviews → add-to-cart. Neon magenta CTA. |
| Category navigation | Mega-menu with icon + text on dark surface. Max 3 levels deep. Filters: material, experience level, type. |
| Loading states | Skeleton screens with subtle neon pulse, never spinners. Cart updates show slide-in with neon border. |
| Error states | Inline validation with neon red, never modal alerts. Error red: `--color-error-500` (#ff1744). |
| Buttons | Primary: neon magenta with glow on hover. Secondary: cyan border, fills on hover. Ghost: transparent with neon text. |
| Cards | Dark surface (`--color-base-800`), neon border on hover (`--color-neon-magenta-500`). |
| Inputs | Dark background (`--color-base-800`), neon magenta focus ring with glow. |

## Execution Steps

1. Load `assets/design-tokens.css` for base color/spacing/typography tokens.
2. Load `references/user-journey-map.md` to understand the full user flow.
3. Load `references/accessibility-checklist.md` before implementing any interactive component.
4. When building components, use Tailwind CSS with custom theme extending the tokens.
5. For checkout, always show progress indicator (step 1 of 5) and "embalaje discreto garantizado" badge.
6. Product cards: image → name → short description → price → "Ver detalles" (not "Comprar ahora").
7. Cart: slide-in from right, not full-page. Show subtotal, shipping estimate, "checkout discreto" link.
8. Forms: floating labels, inline validation, never disable submit until all fields valid.

## Output Contract

Return:
- Component code using design tokens from `assets/design-tokens.css`
- Tailwind classes extending the custom theme
- Accessibility attributes (aria-labels, focus management, contrast ratios)
- Mobile-responsive breakpoints (sm/md/lg/xl)
- Loading and error states for every data-fetching component

## References

- `assets/design-tokens.css` — CSS custom properties for colors, spacing, typography, shadows
- `references/user-journey-map.md` — Complete user flow from landing to post-purchase
- `references/accessibility-checklist.md` — WCAG AAA compliance checklist
- `references/chilean-payment-patterns.md` — Flow, Webpay, MercadoPago integration UI patterns
- `references/discreet-shipping-ui.md` — Shipping option UI patterns and copy guidelines
