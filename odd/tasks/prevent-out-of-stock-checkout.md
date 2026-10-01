# Prevent Out-of-Stock Checkout

## Goal
Stop customers from entering or progressing through checkout for products whose available inventory is zero, while preserving the backend inventory check as the final authority.

## Scope
- Show an unavailable state in product browsing/detail/cart surfaces that use stock data.
- Disable or block add-to-cart and checkout progression when the current cart contains unavailable items.
- Preserve backend validation during order confirmation for race conditions and concurrent purchases.
- Use existing generated API schemas/hooks; do not calculate stock client-side beyond consuming server-provided availability.

## Non-goals
- Do not change pricing calculations.
- Do not weaken server-side inventory reservation/validation.
- Do not add a custom admin panel.

## Decision
The user selected the complete solution: expose hold-aware availability from the backend and use it across add-to-cart, quantity, cart, and checkout guards. The final reservation at order creation remains authoritative for concurrent changes.

## Tasks
- [x] Map stock data contract and every product/cart/checkout entry point.
- [x] Add a hold-aware availability field to the product API, test it, regenerate the OpenAPI frontend schema, and update generated types.
- [x] Implement truthful unavailable presentation and client-side guards from API availability data.
- [x] Add focused frontend/backend regression tests and run required checks.
- [x] Commit the reviewable work units after explicit user authorization.

## Evidence
- Backend product availability tests: 42 passed, 2 PostgreSQL-only tests skipped.
- OpenAPI validation: passed with 0 errors (22 pre-existing warnings).
- Offline generated-type refresh and schema drift check: passed.
- Focused frontend tests: 80 passed across 16 files.
- Frontend production build: passed (existing bundle-size warning only).
- Independent verification: passed; backend reservation remains the final concurrent-purchase authority.
- Commit evidence: `29d72bc` inventory API/OpenAPI contract; `adce20e` catalog unavailable state; `12177e3` cart guard; `1c61aee` checkout guard.

## Compatibility note
Guest carts persisted before this release may lack the newly generated availability field. The server-side reservation still rejects unavailable stock; a future cart-state migration can refresh or clear those legacy snapshots rather than permitting an optimistic client-side continuation.
