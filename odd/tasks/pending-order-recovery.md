# Recover and resolve unpaid checkout orders

## Goal and approval
User approved the proposed full flow: customers recover the same unpaid order instead of recreating it; explicit cancellation is self-service; abandoned orders expire without requiring customer contact. Authenticated and guest buyers supported. Pending receipt with secure recovery link; no cancellation email for expiry. Paid cancellations/refunds remain excluded.

## Existing evidence
Confirmation creates a 15-minute ACTIVE inventory hold, not physical-stock deduction. Payment commits physical stock. Availability ignores expired holds, but orders may remain PENDING. Existing payment URL and payment initiation support resume; orders/tracking lack recovery actions and guest navigation lacks discovery. Frontend creation does not use backend checkout_key idempotency. Signed guest_order_access cookie already carries number/version/expiry and covers `/`; guest cart has no backend identity. Guest replay currently rotates capabilities; avoid breaking recovery on retries. Existing Admin cancellation and cancellation-email work is uncommitted; notification choices migrations 0011/0012 are already applied locally.

## Contract and security decisions
- Backend issues a random signed HttpOnly checkout-attempt cookie before creation; no deterministic identity hash of email/cart. Stable for retries/reloads, actor-bound, protected expiry and signature. Neither tokens nor checkout session data go in localStorage/sessionStorage.
- Prepare context via protected `POST /api/orders/checkout-context/` (204, cookie only); reuse valid attempt. Order POST uses validated attempt for idempotency. Keep explicit-header compatibility without allowing unauthorized guest replay/capability rotation. Validate complete frozen contact/address/cart/delivery intent; changed intent cannot silently reuse the wrong order or add another hold.
- Read-only `GET /api/orders/pending/` returns verified owned/guest pending order (200 OrderSerializer) or 204; no public email/order-number guessing. Existing signed guest cookie/email-ticket and validated attempt can establish ownership. Restore valid access cookie without rotating capability on legitimate recovery. No mutation of domain state on GET.
- Expose read-only payment_expires_at and cancellation_reason through serializers/generated schema. Deadline queries use products services, not cross-app model imports. Existing four checkout steps and server-owned totals remain unchanged.
- Explicit PENDING cancellation reuses the existing secure endpoint. Preserve Admin permission/CSRF/audit and manual cancellation emails; assign reason by trusted caller, never request-supplied notification policy.
- Expire only PENDING with a due reservation, locking Order before reservation. State becomes CANCELLED with EXPIRED reason; no physical-stock movement/refund/expiry email. Handle create/replay/payment mutation races and late mock payment safely; never cancel PAID. Do not cancel on page exit, redirect or refresh.
- Add portable expire_pending_orders command for a periodic job/watch mode, no AppConfig threads or machine scheduler/profile changes. Job activation/live orders require separate approval. Availability already excludes due holds even when job not running; command resolves terminal order records.
- Pending receipt is durable, guest/account-aware and after-commit; link uses existing signed guest email access. Send only for newly created orders, no historical backfill or replay duplication. Obsolete pending-notice retries must be skipped truthfully (not marked SENT without sending) after payment/expiry/cancellation. Cancellation on expiry must not schedule cancelled mail.
- Every API contract update precedes frontend usage: export backend/schema.yaml and regenerate frontend/src/api/schema.d.ts offline. No manual API interfaces or any.

## Work units and workload
Strategy: user-selected stacked-to-main; expected new workflow roughly 900–1500 authored/generated diff lines. One honest slicing pass below; keep tests/docs with behavior, never compress or remove coverage for the advisory ~400-line target. If a cohesive slice exceeds it, report the smallest honest size rather than repeated reshaping. Prior Admin/cancelmail slices remain separate. No commit/push/PR/merge authorized now.

| Unit | Behavior | Forecast |
|---|---|---|
| PR-1 | Signed attempt preparation, actor binding and stable idempotent creation/replay | 250–400 |
| PR-2 | Secure pending discovery, pure deadline contract and generated API | 200–350 |
| PR-3 | Explicit cancellation reasons, quiet expiry and portable processing command | 250–400 |
| PR-4 | Buyer recovery notice, same-order resume and protected cancel UI | 250–400 |
| PR-5 | Pending receipt and stale-retry suppression, event migration | 200–350 |
| PR-6 | Focused integration/regression/browser evidence and deployment-job guide | 100–200 |

Dependency: existing checkout/Admin/mail → PR-1 → PR-2 → PR-3 → PR-5 → PR-4; verification accompanies each behavior and final integration. Writer edits single-threaded; parent owns this task and mirrors it. Strict TDD disabled under session mode; ordinary deterministic tests required.

## Tasks
- [x] PR-0: Map contracts, security and approved delivery strategy.
- [x] PR-1: Implement unpredictable server-owned attempt and idempotency, with proof-aware replay tests.
- [x] PR-2: Implement recovery/deadline contracts and regenerate schema/types, with ownership/read-only tests.
- [x] PR-3: Implement reasons/expiry/payment guards and portable command, with race/stock/no-email tests.
- [x] PR-4: Implement guest/auth recovery, resume/cancel/expired UI and accessibility regressions.
- [x] PR-5: Implement pending receipt/recovery link and no obsolete/expiry notices; test recipients/commit/retry/privacy.
- [x] PR-6: Full isolated backend/frontend checks, independent verification and synthetic Chrome behavior checks.
- [x] PR-7a: Apply only authorized local orders 0013/0014 and verify target, exact history additions and a fresh read-only empty plan.
- [ ] PR-7b: Execute/activate expiry processing only after a future exact authorization; user explicitly deferred it.
- [ ] PR-8a: Save freshly authorized local behavior commits and a session checkpoint.
- [ ] PR-8b: Push/PR/merge only after future separate authorization.

## Verification and non-goals
Backend: existing .venv/Scripts/python.exe, PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=core.settings_local DJANGO_READ_DOTENV=0 PIPENV_DONT_LOAD_ENV=1 LOCAL_TEST_DATABASE=1, unset LOCAL_ALLOW_WRITES; locmem/mocked mail, SQLite in-memory. manage.py check/test; focused then full pytest; makemigrations --check --dry-run; schema contract and offline generation. Report Django-TestCase vs pytest counts and PostgreSQL-only skips.
Frontend: LOCAL_NO_DOTENV=1, pnpm tests/build/check:schema with offline schema path; synthetic no-real-order browser only via named fresh Chrome CLI session and verified temporary profile. Preserve palette, 48px controls, keyboard focus, error/loading states and no pricing math. No real login/order/payment/email actions, .env/secret reads, resets/seeds, Docker operations, alias/profile edits or external environment deletion. App credentials remain opaque if separately authorized live migrations use standard Django settings; never print secrets.

## Final verification evidence
Implementation and independent functional verification are complete. Local activation and delivery remain separate, unauthorized steps.

| Check | Observed result |
|---|---|
| Backend full pytest | 796 passed, 4 PostgreSQL-only skips, 3 existing pagination warnings; 62.91 seconds |
| Django native runner | 12 TestCase tests passed; separate from pytest |
| Backend focused workflow/schema/migrations | 149 passed; check and migration drift clean |
| Frontend full independent suite | 391 passed across 74 files, exit 0; 278.78 seconds |
| Frontend focused new/modified behavior | 99 passed across 12 files, no timeouts |
| Frontend build / offline schema | Zero TypeScript errors; schema check exit 0, no diff |
| Synthetic Chrome behavior | Nine case groups passed; mobile 390×844, 50px controls, focus/Escape and zero horizontal overflow |
| Hygiene | Source unchanged by verifiers; whitespace clean; unrelated pyc, CodeGraph and restore tasks preserved |

The field-local read-only `cancellation_reason` contract preserves the runtime blank value: generated `CancellationReasonEnum | BlankEnum`; semantic tests accept blank/BUYER/ADMIN/EXPIRED and reject null/unknown values. Offline schema generation previously reported zero errors and 53 warnings (22 unique); final independent checks did not regenerate the schema. Frontend build retains the existing >500 kB chunk warning. React act warnings and intentional error-boundary test logs are not test failures.

Chrome used only a fresh named temporary session, verified as chrome/nonpersistent/nonattached/userDataDir=null. Mocked APIs exercised guest notice → same payment route, refresh without creation, explicit cancellation, expired/null deadline guards, authenticated order-list actions and guest-ticket fragment clearing. The final successful synthetic run recorded 51 mocked API calls, zero order-creation POSTs, one cancel POST and one access exchange; no real backend calls. These checks do not prove live cookie signatures, SMTP, payment-gateway integration or PostgreSQL concurrency. The four PostgreSQL-only tests remain skipped.

Earlier repeated full frontend runs were inconclusive: a piped command hid progress, a 240-second serial cap was insufficient, and a temporary wrapper's cleanup/encoding path failed. The final direct-node run with two workers and a 300-second hard bound passed completely. Preserve partial logs before cleanup and bound cleanup subprocesses themselves. No causal product-hang claim is made.

A production preview built without `VITE_API_URL` intentionally fails the public-HTTPS guard. The synthetic checks therefore used an owned loopback DEV server with `LOCAL_NO_DOTENV=1`; no guard, profile or dotenv changes. Only the owned Chrome/server were closed. Two newly created CLI snapshots were moved outside the repository to `C:/Users/elyna/AppData/Local/Temp/pending-recovery-cli-artifacts-5m1c2tph`; other artifacts remain in the owned temp folders.

Native ASSESS remains unavailable due untracked declarations. The required independent fallback is complete; no native approval receipt is claimed. Reviewed non-blocking observations: duplicate recovery CTA on `/checkout`, a render-time WeakMap update without a reproduced leak, and brief confirmation lockout during background refetch.

## Honest review slices
Backend new workload approximately 1400 changed lines: PR-1 470, PR-2 375, PR-3 370, PR-5 185. PR-1's cohesive proof/intent/security-test slice exceeds the advisory target after one honest slicing pass.

Frontend PR-4 is 1031 changed lines across 26 source/test files, excluding 98 generated-contract lines belonging with PR-2. One honest behavior split, with tests alongside code:

| Slice | Behavior | Changed lines |
|---|---|---|
| PR-4a | Typed API, domain state, actor-scoped hooks and invalidation | 413 |
| PR-4b | Global recovery notice and accessible cancellation controls | 313 |
| PR-4c | Checkout guard and existing-payment/deadline flow | 217 |
| PR-4d | Order-list/tracking recovery actions | 88 |

PR-4a's cohesive cross-hook contract slice is 13 lines above the advisory target; report it rather than remove coverage or compress code. Preserve stacked-to-main strategy and the prior Admin/cancelmail units. No policy exception label or delivery permission is inferred.

## Local checkpoint staging boundary
User explicitly authorized local commits only. One dependency-aware pass found that checkout proof/full-intent replay, quiet expiry and discovery tests share the same core helpers; separating them into the earlier estimated PR-1/2/3 snapshots would manufacture invalid intermediates. Local backend checkpoints therefore contain Admin detail confirmation, then cancellation notice plus trusted reasons/0012/0013, then the coupled recovery/expiry/receipt core and generated contract/0014. Report the actual core overage rather than compress code or delete coverage. Working-tree source remains unchanged; each backend index is exported outside the repository and verified against its staged dependencies with SQLite/locmem. Fresh full index projection (including tracked compose/runbook dependencies): `python -m pytest -q -rs` passed 796 tests, with 4 PostgreSQL-only skips and 3 existing pagination warnings, in 68.24 seconds. Earlier export omitted those two root fixtures and was corrected without touching tests/source. Runtime boundary is the SQLite/locmem API/service harness; no live orders/mail/job. Core rollback covers only the coupled context/recovery/expiry/receipt behavior and contract, retaining earlier Admin/manual-cancellation units. The actual local core boundary is approximately 1502 changed lines including generated contracts/task evidence; this is not a ≤400-line independent PR claim. No remote publication is authorized.

### Frontend local units (cumulative dependencies, same task evidence)
- A: typed API/context preparation, actor-scoped pending/cancel hooks, deadline/reason mapping and synthetic handlers. API/domain rollback leaves existing views untouched. 413 source diff lines (honest advisory overage); fresh staged index export passed 34 tests/6 files in 48.19 seconds plus TypeScript/Vite build (1160 modules, existing chunk warning). Use direct Node equivalents of `tsc -b && vite build` for junction-backed temporary snapshots: pnpm auto-install preflight refuses a junction before compilation; no dependency/source/guard change was needed.

- B: global discreet pending notice plus accessible inline cancellation (focus/Escape/double-submit/409). Rollback removes only shared notice/actions and Layout wiring. 313 source diff lines; fresh index export passed 18 tests/2 files in 27.17 seconds plus TypeScript/Vite build (1162 modules). TestClient/MSW/browser evidence is synthetic, not live cancellation.

## Next step and live limitations
User freshly authorized only `orders.0013_order_cancellation_reason` (AddField) and `orders.0014_pending_payment_receipt` (two AlterField) on `codigo_secreto`, `127.0.0.1:5432`. The read-only preflight verified the actual database, read-only mode, applied 0011/0012 prerequisites and exact two-migration forward plan. A separate write-enabled process reverified target/plan/operations, applied only those migrations through Django's executor and confirmed that history gained exactly those two entries. The new column is varchar(10), NOT NULL. A fresh read-only connection confirmed both applied and no remaining plan to 0014. No post-migrate domain callbacks, other migrations or customer-data queries were executed.

User then explicitly selected **prepared, without execution** for expiry. `expire_pending_orders` runs one bounded batch by default; `--watch --interval 60 --batch-size 100` is an optional portable foreground process. Either execution can cancel existing due PENDING orders, so still requires a future separate exact approval. It does not cancel PAID orders, move physical stock, send expiry emails or install a machine scheduler. Expired holds already stop counting toward availability; terminal CANCELLED/EXPIRED records require processor execution. No live expiry, backfill or real order/payment/email test occurred.

Work branch `feat/admin-pending-order-cancellation` remains at `5a98073`; no new commits, pushes, PRs or merges. PR-7b activation and PR-8 delivery remain open. For manual testing, start the usual local backend with its existing per-terminal write opt-in and the frontend development server; the owned synthetic test servers were closed.
