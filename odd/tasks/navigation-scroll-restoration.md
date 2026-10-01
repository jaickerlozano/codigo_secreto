# Navigation Scroll Restoration

## Goal
Give customers predictable orientation after navigation: normal product, cart, checkout, and confirmation route changes begin at the top; intentional in-page targets remain visible.

## Scope
- Identify the router and checkout step transition behavior.
- Restore top-of-page position on ordinary navigation.
- Preserve hash/intentional target navigation and make targets visible/focusable when appropriate.
- Respect reduced motion and browser back/forward expectations.

## Non-goals
- Do not change product, cart, or checkout business behavior.
- Do not add scroll-based analytics or persistent session state.

## Decision
Apply the same orientation policy to ordinary route navigation and checkout step changes: move to the top. Preserve browser back/forward restoration. Treat only a fragment that resolves to a DOM element as an intentional target; never interpret order-tracking capability fragments as anchors.

## Tasks
- [x] Map route navigation, checkout steps, search/result target behavior, and current scroll handling.
- [x] Implement accessible scroll restoration with intentional target handling.
- [x] Add focused regression tests and verify the frontend build.
- [x] Commit after explicit user authorization. Evidence: `544d41a` (`feat(navigation): restore scroll position`).

## Evidence
- Focused route/layout/checkout tests: 13 passed across 3 files.
- Frontend build: passed; only the existing large-chunk warning remains.
- Independent verification: passed. Route PUSH/REPLACE scrolls to top, POP is preserved, true anchors are untouched, opaque tracking access fragments are never treated as anchors, and checkout scrolls only after a completed step change.
