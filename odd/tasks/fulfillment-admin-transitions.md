# Fulfillment admin transitions

Implement the authorized staff fulfillment lifecycle: dispatch may use a persisted Santiago request as its delivery estimate, and shipped orders may be durably marked delivered.

## Authorization and policy

- **FUL-ADMIN-01**: When `requested_dispatch_date` is persisted and staff leaves `estimated_delivery_date` blank, dispatch uses the requested date.
- **FUL-ADMIN-02**: Orders without `requested_dispatch_date` require staff to provide `estimated_delivery_date`; retain the existing Spanish required-date error.
- **FUL-ADMIN-03**: Staff can transition only `SHIPPED` orders to `DELIVERED`, recording `delivered_at`; `Order.status` remains read-only in Django Admin and is never a free-form lifecycle selector.

## Exact source scope

- `backend/apps/orders/models.py`
- `backend/apps/orders/services.py`
- `backend/apps/orders/admin.py`
- `backend/apps/orders/templates/admin/orders/order/change_form.html`
- `backend/apps/orders/tests/test_fulfillment.py`
- `backend/apps/orders/tests/test_migrations.py`
- `backend/apps/orders/migrations/0009_order_delivered_at.py`
- This task record only.

Excluded: payments, inventory, shipping tariffs, catalog and image code, Cloudinary, Neon, frontend/API contract expansion, customer/order test data, `backend/.env`, and every remote system.

## Baseline and constraints

- Branch: `feat/managed-postgresql-runtime`, ahead of `origin/feat/managed-postgresql-runtime` by 8 commits.
- Dirty baseline: clean before this task record was created.
- TDD is disabled by source #144; use ordinary focused and suite checks.
- RDD clone-local mode is off.
- Every Django command uses `PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local LOCAL_TEST_DATABASE=1` with `backend/env/bin/python`; never load `backend/.env` or use catalog/remote data.

## Plan and verification

1. Add nullable `delivered_at` with a generated migration; validate no migration drift.
2. Resolve dispatch dates in the locked dispatch service, retaining carrier and notification behavior.
3. Add a locked neutral delivery transition service and constrained admin change-form/changelist controls.
4. Add focused fulfillment/admin and migration coverage, then run focused orders tests, the ordinary backend suite, `makemigrations --check --dry-run`, and `git diff --check`.

## Rollback

Revert the dedicated work-unit commit to remove the migration, delivery timestamp, service transition, constrained admin controls, tests, and this record together. No business data migration or remote change is included.

## Results

- Added migration `0009_order_delivered_at`; `delivered_at` is nullable and reversible.
- Dispatch uses an explicit staff date first, otherwise the locked order's persisted request; regional orders still receive the existing Spanish required-date error.
- `transition_order_to_delivered` locks the order, permits only `SHIPPED -> DELIVERED`, writes `delivered_at`, and leaves dispatch metadata untouched. It sends no notification.
- Django Admin keeps lifecycle fields read-only and provides status-constrained change-form buttons plus per-order changelist actions. Invalid selections report Spanish errors without stopping valid rows.
- Focused verification: `pytest apps/orders/tests/test_fulfillment.py apps/orders/tests/test_migrations.py -q` — 34 passed in 3.93s.
- Ordinary backend suite: `pytest -q` — 671 passed, 4 skipped, 3 existing pagination warnings in 37.74s.
- `manage.py makemigrations --check --dry-run` reported no changes; `git diff --check` passed.
- Review workload forecast: approximately 350 changed lines, below the 400-line work-unit budget.

## Status

- [x] FUL-ADMIN-01 through FUL-ADMIN-03 authorized and tracked before source changes.
- [x] Implementation and verification complete. Reversible migration tests restore `0009`; their historical pending test row is cancelled so the existing `0008` inventory backfill can safely replay.
- [ ] Commit evidence pending.
