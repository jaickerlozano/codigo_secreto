# Local shipping catalog test policy

## Objective and authorization

Enable every Chilean commune in the local Docker PostgreSQL database for manual mock-checkout testing with one explicitly temporary CLP 3,000 tariff.

- User explicitly approved the temporary local-only policy after the API diagnosis.
- Scope: `shipping_comuna.shipping_cost` only for the 344 currently-zero active rows; Arica already has the approved CLP 3,000 and must remain unchanged.
- Excluded: products, images, Cloudinary, Neon, orders, users, regional metadata, production configuration, and source-code behavior.

## Preserved before-state

- Scoped rows: 345 communes.
- Snapshot SHA-256: `654c44db138216305684f71287c7732e25e84d7c16edc8347368cd5454fb7ccd`.
- Distribution: 344 rows `{shipping_cost: 0, is_active: true}`; 1 row `{shipping_cost: 3000, is_active: true}` (Arica).
- Geography is already complete: 16 regions and 345 communes. The API hid 344 communes because it deliberately returns only active rows with a positive tariff.

## Guarded apply and rollback

1. Recompute the full 345-row hash inside a locked transaction; abort on mismatch.
2. Lock only `shipping_comuna` with a transaction-scoped write-exclusion lock.
3. Change rows only where `shipping_cost = 0` and `is_active = true`; require exactly 344 affected rows.
4. Commit once; verify every region has at least one eligible commune through the live API.

Rollback sets only the 344 recorded temporary rows from CLP 3,000 back to CLP 0, provided they are still active and exactly CLP 3,000. It never changes Arica or any unrelated shipping field.

## Applied outcome (2026-09-27)

The guarded local transaction revalidated the before-state hash, locked only `shipping_comuna`, updated exactly 344 rows, and committed once. Arica was not modified.

- After snapshot SHA-256: `3cc248f53d23725897a4bbe67205ba6e30a6c34cc548d799ce7a3d7fd8cd460e`.
- After distribution: 345 rows `{shipping_cost: 3000, is_active: true}`.
- API verification: all 16 regions return eligible communes; total 345, with at least 4 in every region.
- Frontend proxy verification: `/api/shipping/comunas/?region=2` returns 7 communas.
- Regional dispatch verification: a Tarapacá comuna returns a valid `regional` dispatch payload. Missing optional carrier metadata remains valid; `StepAddress` and `StepShipping` tests pass 21/21.
- No product, image, order, user, Cloudinary, Neon, regional-profile, or source-code data changed.

## Status

- [x] Before-state persisted in this file and Engram observation #1145.
- [x] Guarded local tariff update completed.
- [x] API verifies all 16 regions expose eligible communes.
- [ ] Documentation committed with outcome and rollback evidence.
