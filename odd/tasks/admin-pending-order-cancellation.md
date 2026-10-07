# Cancel pending orders from Django Admin

## Goal and approved scope
Operator can cancel a pending order directly from its Django Admin detail, after explicit confirmation; the order becomes CANCELLED and its active inventory reservation is released. User selected Admin only and pending only.

## Existing contract
`cancel_pending_order` already guards PENDING inside an atomic locked transition and releases reservations. The customer cancellation API exists but is not for staff. Admin list action `Cancel pending orders` exists, but no visible detail cancellation control exists. Reuse the service; do not edit lifecycle fields directly.

## Boundaries
- Django Admin only; no React admin/customer features or public API/OpenAPI changes.
- PENDING only; PAID, SHIPPED, DELIVERED and CANCELLED cannot be cancelled through this control.
- No refund, physical-stock increase, payment change or new status. Cancellation email is a separately authorized follow-up tracked in `cancelled-order-notification.md`.
- Require staff/object change permission, CSRF-protected explicit confirmation, fresh server-side eligibility and admin audit logging. Handle stale state or repeated submission without duplicate effects.
- Preserve dispatch/delivery controls and the existing bulk action; use clear Spanish labels.
- No live orders/logins/DB operations, migrations, secrets/env reads, Docker/profile/environment cleanup, commit or push without fresh authorization.
- Preserve unrelated bytecode, .codegraph and recovery tasks; maintain already committed checkout fixes in the active worktree.

## Execution and budget
One delegated writer for admin/template/test edits; test-first remains disabled under existing session mode, ordinary deterministic verification required. Forecast 150–300 changed lines, advisory review budget about 400; ask if scope exceeds a cohesive bounded slice. Use standard Django Admin confirmation/view primitives rather than frontend admin UI. An internal admin confirmation route is in scope if needed for safe permission/CSRF handling; no public endpoint.

## Tasks
- [x] AC-1: Map existing cancellation and confirm operator/pending-only scope.
- [x] AC-2: Expose detail cancellation with confirmation, permissions, safe state handling and tests.
- [x] AC-3: Run isolated Django checks/tests and independent verification as assessed; record gaps.
- [ ] AC-4a: Save the authorized local behavior commit; commit identity is recorded in the final session checkpoint.
- [ ] AC-4b: Push/PR/merge only after a future separate authorization.

## Acceptance and verification
- A change-authorized operator sees a clear Cancelar pedido control for PENDING; GET confirmation does not mutate order/reservation.
- Confirmed POST uses the existing cancellation service; database state becomes CANCELLED and ACTIVE reservation becomes RELEASED with CANCELLED reason, with no physical-stock movement.
- Unauthorized users, missing CSRF and ineligible/stale states cannot cancel; repeat submissions remain safe.
- Existing list cancellation and dispatch/delivery work unchanged; no profile/API/payment/pricing modifications.
- Run from backend with existing Windows .venv and `PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=core.settings_local DJANGO_READ_DOTENV=0 PIPENV_DONT_LOAD_ENV=1 LOCAL_TEST_DATABASE=1`, unset LOCAL_ALLOW_WRITES: `python manage.py check`; `python manage.py test apps.orders.tests.test_admin apps.orders.tests.test_inventory_cancellation`; broader `python manage.py test apps.orders` or full suite as practical. SQLite in-memory only; no local PostgreSQL writes. Explicitly record PostgreSQL-only skips and browser/manual gaps; do not claim live or concurrency checks.

## Progress and evidence
- Implemented protected Admin confirmation, Spanish labels, permissions/CSRF, locked cancellation and transactional audit; no change-form field saves. Missing/inconsistent reservation reports a clear error without mutation. Five source/template/test files, 352 changed lines.
- Writer: 11 Django tests and 17 focused pytest tests (plus 11 subtests), Django check and whitespace passed. Independent final candidate: Django check clean, 11 Django tests passed, full backend pytest 713 passed / 4 PostgreSQL-only skips; 3 existing pagination warnings.
- Parent readback of confirmation and Cancelado / Anulado status label; isolated Django check passed. Native ASSESS unavailable due untracked declarations; required independent verification completed, no native receipt claimed.
- Work branch `feat/admin-pending-order-cancellation` based on already published checkout fix `5a98073`, preserving local checkout behavior. Frontend/services/public API unchanged; unrelated local artifacts preserved.

## Local checkpoint authorization
User explicitly authorized local commits only to continue in a new session. The Admin index boundary excludes later reason/email changes; isolated index-projection tests verify the behavior against its actual staged dependencies. Working-tree source stays byte-for-byte unchanged. Fresh index export: isolated `python -m pytest -q apps/orders/tests/test_admin.py apps/orders/tests/test_inventory_cancellation.py` passed 17 tests in 3.99 seconds. Runtime boundary uses Django TestClient confirmation/CSRF/permissions/locked release; no live admin action. Rollback removes only Admin detail/template/test behavior. No push/PR/merge authority follows.

## Next step and limitations
User confirmed local Admin cancellation succeeds; cancellation email is implemented and tracked separately in `cancelled-order-notification.md`. Browser/assistive-technology and real PostgreSQL concurrency checks were not performed by the agent. Existing bulk/customer callers still assume an inventory reservation; graceful missing-reservation handling is detail-route-only. No agent-initiated order/payment actions or commit/push; AC-4 requires fresh authorization. The separately approved follow-up applied only notification-event migrations 0011/0012 to local PostgreSQL.
