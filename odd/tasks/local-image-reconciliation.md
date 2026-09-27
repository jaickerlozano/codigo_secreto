# Local image-reference reconciliation

## Objective and authorization

Repair three known-broken local PostgreSQL product image references from the verified SQLite source, preserving the complete scoped before-state before a single guarded transaction.

- User explicitly authorized this local-only update after reviewing the dry-run.
- Scope: exact raw SKUs `101`, `201`, and `712`; replace their three primary references and add eight source gallery references.
- Excluded: Cloudinary upload, deletion, rename, API administration, Neon, remote databases, product/catalog changes, and any other SKU.

## Preserved dry-run state

- Source snapshot SHA-256: `0d409bd010a80184306ae31f2c2e18affa0c51115ff4fd41c8d5c045a4ff537e`
- Target snapshot SHA-256: `bdb85fd0986ea4d0e41fe1f20ed4ed964dfcf6ed1b1cff621562182561cf7657`
- Match key: exact raw SKU only; never IDs, names, normalized text, or position.
- Source: 3 products, 3 primary references, 8 gallery references.
- Target before apply: 3 products, 3 nonempty primary references, 0 gallery references.

| SKU | Target primary before (verified 404) | Source primary (verified 200) |
| --- | --- | --- |
| `101` | `products/sku_101.webp` | `media/products/Screenshot_2026-07-09_153127` |
| `201` | `products/sku_201.webp` | `media/products/Screenshot_2026-07-09_152139` |
| `712` | `products/sku_712.webp` | `media/products/Screenshot_2026-07-08_135718` |

Gallery additions (all publicly verified 200):

- `101`: `media/products/gallery/Screenshot_2026-07-09_153113`, `media/products/gallery/Screenshot_2026-07-09_153139`, `media/products/gallery/Screenshot_2026-07-09_153157`
- `201`: `media/products/gallery/Screenshot_2026-07-09_152226`, `media/products/gallery/Screenshot_2026-07-09_152413`, `media/products/gallery/Screenshot_2026-07-09_152518`
- `712`: `media/products/gallery/Screenshot_2026-07-08_135747`, `media/products/gallery/Screenshot_2026-07-08_135816`

## Apply guard and rollback

1. Recompute both scoped snapshot hashes inside local PostgreSQL/SQLite reads; abort on any difference.
2. Acquire a transaction-scoped write-exclusion lock on product and gallery tables.
3. Recheck each exact target primary before updating it and the absence of every gallery reference before inserting it.
4. Update exactly three primary fields and insert exactly eight gallery rows, then commit once.
5. Record target gallery IDs and after-state. Abort on unexpected row counts.

Rollback restores only the three recorded primary values and deletes only the eight recorded gallery rows, and only when their current values still match the recorded after-state. It never deletes Cloudinary assets.

## Applied outcome (2026-09-27)

The guarded transaction revalidated both before-state hashes, acquired `SHARE ROW EXCLUSIVE` locks on both scoped tables, updated exactly three primary references and inserted exactly eight gallery rows. It committed once; no Django storage API, Cloudinary API, Neon connection, catalog row, or unrelated SKU was touched.

- Target after snapshot SHA-256: `121e739f64e9a3c7379a6cb953420f00e943c548bb3883760363fc798e9a379a`
- Primary updates: `101` target product ID `1`; `201` target product ID `7`; `712` target product ID `34`.
- Inserted gallery IDs: `3`–`5` for `101`, `6`–`8` for `201`, and `9`–`10` for `712`.
- API verification: each primary URL is `https://res.cloudinary.com/dwsjww7yt/image/upload/media/products/...`; `101` exposes 3 galleries, `201` exposes 3, and `712` exposes 2.
- Frontend verification: `http://127.0.0.1:5173/` responds `200`; its `/api/products/` proxy returns `count: 44`.
- Runtime: backend `127.0.0.1:8000` and frontend `127.0.0.1:5173`, both loopback-only; backend has `LOCAL_ALLOW_WRITES=1` for user-driven mock checkout testing.

## Status

- [x] Before-state persisted in this file and Engram observation #1138.
- [x] Guarded local PostgreSQL apply completed.
- [x] Direct API and frontend proxy verify three primary URLs and eight gallery URLs.
- [ ] Documentation committed with outcome and rollback evidence.
