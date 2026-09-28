# Guest email tracking link

## Objective

After a guest customer completes a purchase, send a confirmation email containing a secure link that lets that customer track the order without an account.

## Authorization and scope

- The user explicitly authorized this customer-facing feature on 2026-09-28.
- The link must use the existing capability-based guest access model; never expose a lookup by order number alone, credentials, tokens, or personally identifiable data in logs.
- The feature must work after the customer leaves the checkout confirmation page or uses another browser/device.
- Excluded until mapped: any production email provider configuration, remote delivery, `backend/.env`, Cloudinary, Neon, payments, tariff/catalog/image changes, and unrelated frontend work.

## Work items

- [x] GUEST-TRACK-01 — Map the existing order confirmation, notification/email delivery, guest capability, and tracking-route flow.
- [x] GUEST-TRACK-02 — Add a secure tracking URL to the appropriate guest confirmation email without changing account-holder behavior unnecessarily.
- [x] GUEST-TRACK-03 — Add focused backend and frontend/contract tests for generation, delivery, access exchange, and invalid/missing capabilities.
- [x] GUEST-TRACK-04 — Run applicable local verification, document results, and commit the completed work unit.

## Current evidence and constraints

- Existing frontend route: `/order/:orderNumber`; the initial guest capability is handled from a URL fragment (`#access=...`) and is removed after exchange.
- Current tracking statuses are `PAID`, `SHIPPED`, `DELIVERED`, and `CANCELLED`; the page already refreshes order data every 30 seconds.
- Local environment only: never auto-load `backend/.env`. Django commands require `PIPENV_DONT_LOAD_ENV=1`, `DJANGO_READ_DOTENV=0`, `DJANGO_SETTINGS_MODULE=core.settings_local`, and the project virtualenv.
- Branch: `feat/managed-postgresql-runtime`; local orders migration `0009_order_delivered_at` is applied. RDD clone-local mode is off and TDD is disabled by source #144.
- Prior fulfillment work is committed as `dcd69b4`; its local server is running at `127.0.0.1:8000` and the frontend at `127.0.0.1:5173`.
- Verified map: guest checkout creates one opaque 90-day capability and stores only its SHA-256 digest. The raw token cannot be recovered after checkout. Payment approval synchronously schedules confirmation after commit. The frontend exchanges `#access=...` only through `X-Order-Capability`, removes the fragment, and receives the existing Strict HttpOnly access cookie. Opaque capability validation and masked-404 behavior remain unchanged.
- GUEST-TRACK-01 route/trigger: this is a cross-file map and a multi-file implementation. The guest `payment_confirmation` notification is generated in `backend/apps/orders/notifications.py` and triggered after payment approval; the backend header exchange is the only acceptance boundary; the existing frontend tracking route consumes and clears the fragment.
- Email-link constraints: use a separate signed email-channel capability with its own Order version/revocation state; never persist or log its raw ticket, do not rotate opaque guest capability tokens on delivery retries, and use only local/locmem or mocked delivery.

## Session handoff

- Implementation: `Order` now holds a separate email-link version and revocation timestamp. Django timestamp signing uses the purpose-specific `orders.guest-email-access` salt and the existing 90-day guest policy. Only the header exchange action accepts this ticket, then issues the existing Strict HttpOnly cookie; opaque capability behavior is unchanged.
- Delivery: only guest `payment_confirmation` bodies receive `ORDER_TRACKING_PUBLIC_ORIGIN/order/<order-number>#access=<ticket>`. The production value is the already validated HTTPS `FRONTEND_ORIGIN`; the local default is `http://localhost:5173`. Account-holder and dispatch emails remain unchanged. Retry creates a current signed ticket without rotating either version, and ticket-bearing delivery exceptions are redacted from persisted errors and logs.
- Tests: `test_guest_email_tracking.py` covers signed payload creation, guest-only placement, header-only exchange with empty response, masked tampering/expiry/revocation/foreign-ticket failures, version invalidation, retry stability, and error redaction. Existing `frontend/src/features/orders/api/orders.api.test.ts` remains the contract proof that fragment-only values go to `X-Order-Capability`, are removed, and query/path proofs are not exchanged; no frontend source changed.
- Engram mirror: observation `#1150`, topic `odd/guest-email-tracking/tasks`.

## Verification and rollback

- Required command, from `backend/`: `PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local pipenv run python manage.py test apps.orders` — passed process checks but discovered 0 tests because this suite is pytest-based.
- Effective local suite, from `backend/`: `LOCAL_TEST_DATABASE=1 PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local pipenv run pytest apps/orders` — 210 passed, 1 skipped in 12.51s. The `LOCAL_TEST_DATABASE=1` override is required because the local profile otherwise intentionally opens PostgreSQL read-only and pytest cannot create its disposable database.
- Frontend build: N/A; no frontend source or test changed. Narrow frontend test: N/A for the same reason; its existing fragment/header/cleanup contract test remains unchanged.
- Delivery evidence: implementation work-unit commit `4fdf814` contains 254 additions and 16 deletions (270 changed lines) across code, migration, tests, and this tracker. No external delivery occurred; tests used mocks and locmem.
- Rollback boundary: revert `4fdf814` to remove the guest-email tracking-link implementation (model fields, migration `0010`, signing/exchange/notification behavior, tests, and its tracker evidence). This tracker follow-up record can be reverted independently.
