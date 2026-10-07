# Notify customers when a pending order is cancelled

## Goal and approved scope
User confirmed local pending-order cancellation works and explicitly requested an email informing the customer. Add a neutral Spanish cancellation notice for each successful PENDING → CANCELLED transition, using the existing durable notification pipeline.

## Decision and contract
Schedule internal event `cancelled` in shared `cancel_pending_order` after status save, inside the transaction. Existing Admin detail/bulk and authorized customer-API callers all reuse this service. `NotificationDelivery` unique(order,event), locking/SENT guard, after-commit sending and retry handling stay authoritative. Add model choice and code migration 0012 following 0011; public API/schema unchanged.

## Email
Subject states the order number was cancelled. Body confirms cancellation and that this order will not be dispatched. Reuse guest_email/account-email recipient selection. No invented reason, refund/payment promise, product/total/address details, tracking link or guest-capability issuance. Do not backfill previously cancelled orders.

## Boundaries
- Preserve pending-only eligibility, inventory release, existing Admin confirmation/permissions/audit and checkout fixes.
- No paid cancellation/refunds, new customer/admin React views, public endpoint/type/schema changes or pricing calculations.
- One durable cancellation event per order; repeated/stale/failed cancellation must not schedule another. Transaction rollback discards row/callback; SMTP failure retains CANCELLED and records retryable failure.
- Missing recipient follows existing failure/retry behavior; never block cancellation or send to an invented address.
- All verification isolated with locmem email and SQLite in-memory. No real emails/orders, live DB migration/application, .env/secret reads, Docker, profile edits, environment cleanup or commit/push without fresh authorization.
- Preserve existing WIP and unrelated bytecode/.codegraph/recovery tasks; parent owns ODD task docs.

## Work units and budget
New email slice forecast 100–250 changed lines, separate from prior Admin cancellation unit (352 source/test lines + task document). Preserve user-selected `stacked-to-main` delivery strategy for future small review slices; no delivery now authorized. Strict TDD remains disabled per session; ordinary deterministic checks mandatory.

## Tasks
- [x] CN-1: Map notification pipeline and specify neutral notice and recipient policy.
- [x] CN-2: Add event/subject/body/service scheduling, migration and focused regression coverage.
- [x] CN-3: Verify with Django runner and pytest, migration drift and independent assessment fallback as required.
- [x] CN-4: Apply explicitly authorized local migrations 0011 (pending prerequisite) and 0012; verify exact target and history.
- [ ] CN-5a: Save the freshly authorized local notification/reason commit.
- [ ] CN-5b: Push/PR/merge only after future separate authorization.

## Verification and acceptance
Tests: successful cancellation for guest/auth recipients, after-commit only, unique event/no repeat, SMTP failure + successful retry, transaction rollback/no emission, ineligible and missing-reservation no emission, no recipient retryability, neutral text/no capabilities, event migration/reversal. Exercise Admin cancellation path plus existing callers using current fixtures; retain all legacy tests. Use existing backend/.venv/Scripts/python.exe with PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=core.settings_local DJANGO_READ_DOTENV=0 PIPENV_DONT_LOAD_ENV=1 LOCAL_TEST_DATABASE=1, unset LOCAL_ALLOW_WRITES. Run manage.py check; manage.py test (TestCase only); python -m pytest relevant modules then full backend; manage.py makemigrations --check --dry-run; targeted whitespace. PostgreSQL-only skips, browser/manual and live-Mailpit gaps explicitly recorded.

## Progress and evidence
- Neutral cancellation notice implemented for guest/account recipients, after domain commit, with existing idempotency/retries; no tracking capability or refund promise. Email slice approximately 273 changed lines, separate from prior Admin unit.
- Writer: 55 focused pytest passed / 1 PostgreSQL-only skip; 12 Django tests passed; checks, migration drift and whitespace clean. Independent final candidate: full backend pytest 727 passed / 4 PostgreSQL-only skips / 3 pre-existing pagination warnings; 12 Django tests passed; check, drift, scope and whitespace passed.
- Parent readback confirms scheduling after status save inside atomic and explicit cancellation subject/body branches. Native ASSESS unavailable due untracked declarations; required independent verifier completed, no native receipt claimed.
- Exact 0012-only plan exposed unapplied 0011 and stopped without mutation. User then explicitly authorized both; only forward 0011/0012 choices migrations applied on local codigo_secreto at 127.0.0.1:5432, migration history verified and target plan empty. No resets/seeds/orders/users/other migrations or retroactive emails.

## Local checkpoint boundary
The user authorized local commits only. This unit includes the trusted BUYER/ADMIN reason field and migration 0013 alongside cancellation event 0012 because the final cancellation regressions verify those reasons. Pending receipt/SKIPPED and expiry/context/recovery stay in the following coupled unit. Rollback boundary: manual cancellation notice/reason policy and its tests/migrations; preserve the Admin confirmation unit. Fresh isolated index projection: `python -m pytest -q apps/orders/tests/test_cancellation_notifications.py apps/orders/tests/test_inventory_cancellation.py apps/orders/tests/test_migrations.py` passed 25 tests in 6.03 seconds. Runtime verification uses locmem and Django/API test clients, never real SMTP/orders.

## Next step and limitations
User tests a new pending-order cancellation and checks local Mailpit at http://localhost:8025. Existing cancelled orders are not backfilled. Agent did not send real emails or cancel orders; tests used locmem. Live SMTP/Mailpit, browser and PostgreSQL concurrency checks remain unperformed. CN-5 commit/push awaits fresh authorization; all prior Admin/checkout and unrelated local WIP preserved.
