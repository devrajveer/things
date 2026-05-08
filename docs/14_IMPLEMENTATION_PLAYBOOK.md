# Implementation Playbook

The build order. Sprint-by-sprint, ticket-by-ticket plan to take the project from empty repo to first paying customer.

> **For the AI coding agent**: read this top-to-bottom on first run. Pick the first unfinished ticket. Read its acceptance criteria. Read the referenced sections in [06_PRD], [07_DATA_CONTRACTS], [08_UI_UX_SPEC], [09_SECURITY_SPEC]. Apply [05_CODING_STANDARDS] and [10_TEST_PLAN]. Implement. Verify acceptance criteria with tests. Open PR per [05_CODING_STANDARDS §4]. Move to next ticket. **Never invent ambiguity-resolutions** — if a contradiction or gap appears, stop and surface it.

---

## Table of contents

- §1 How to use this playbook
- §2 Phasing overview
- §3 Definition of Ready / Definition of Done
- §4 Ticket format
- §5 Sprint 0 — Bootstrap
- §6 Sprint 1 — Auth & Users
- §7 Sprint 2 — Organizations & Projects
- §8 Sprint 3 — Devices & Profiles
- §9 Sprint 4 — Ingestion (HTTP + MQTT)
- §10 Sprint 5 — Streams & Queries
- §11 Sprint 6 — Dashboards & Widgets
- §12 Sprint 7 — Rules & Alerts
- §13 Sprint 8 — API Keys, SDKs, CLI
- §14 Sprint 9 — Marketing, Docs, Onboarding, Audit
- §15 Sprint 10 — Hardening & Beta
- §16 Sprint 11 — Launch & Paid GA
- §17 Phase 2 outline
- §18 Risks register

---

## 1. How to use this playbook

1. Each sprint has a **goal**, a **list of tickets**, and an **end-of-sprint demo checklist**.
2. Tickets are ordered by dependency. A ticket can only start if all its `Depends on` tickets are merged to `main`.
3. Within a sprint, tickets without inter-dependencies can be done in parallel by multiple agents (or held serial by a solo dev).
4. Each ticket is sized to be one PR. If a ticket would exceed ~600 lines of changed code, split it into sub-tickets `T-XXXX.1`, `T-XXXX.2`.
5. A sprint completes when **all its tickets are merged**, the demo checklist passes, and the staging environment shows the new functionality working.
6. After every sprint, run the full e2e suite. Anything red blocks the next sprint.

### Agent operating rules (non-negotiable)

- Always read `04_GLOSSARY.md` before naming anything.
- Always run `make lint && make typecheck && make test` before opening a PR.
- When acceptance criteria mention a contract (API endpoint, DB column, event payload), the contract source-of-truth is `07_DATA_CONTRACTS.md`. Generate code from contracts; do not hand-write divergent shapes.
- All code must include tests at the levels mandated by `10_TEST_PLAN`.
- Forbidden: `# TODO` comments left in merged code without a tracking ticket id (`# TODO(T-1234): ...`).
- Forbidden: `console.log`, `print()` for non-test code; use the structured logger per `05_CODING_STANDARDS §10`.
- Forbidden: hardcoded values that must be configurable; use [11_CONFIGURATION_REFERENCE].

---

## 2. Phasing overview

| Phase | Sprints | Outcome | Calendar (solo, full-time) | Calendar (solo, evenings) |
|---|---|---|---|---|
| Phase 1 MVP | S0–S11 | Public beta, first paid customer | ~14 weeks | ~28 weeks |
| Phase 2 Power | S12–S20 | AI features, advanced rules, billing | ~12 weeks | ~24 weeks |
| Phase 3 Scale | S21+ | HA prod, enterprise features | rolling | rolling |

A "sprint" is 1 week full-time or 2 weeks evenings. Adjust to your pace. **Never compress by skipping tests.**

---

## 3. Definition of Ready / Done

### Definition of Ready (a ticket can be picked up)

- `Depends on` tickets are merged.
- All referenced specs exist and are consistent.
- Acceptance criteria are objective and testable.

### Definition of Done (a ticket can be merged)

- Code matches [05_CODING_STANDARDS] (verified by CI lint, format, typecheck).
- Tests at every required level pass (verified by CI).
- Coverage meets thresholds (verified by CI).
- All acceptance criteria demonstrably met (manual or automated).
- New env vars added to [11_CONFIGURATION_REFERENCE] in same PR.
- New API endpoints / events / DB columns reflected in [07_DATA_CONTRACTS] in same PR.
- New UI screens reflected in [08_UI_UX_SPEC] in same PR.
- CHANGELOG entry under "Unreleased".
- PR description references the ticket id and the acceptance criteria item satisfied.
- Self-review checklist (in PR template) ticked.
- CI green.

---

## 4. Ticket format

```
### T-XXXX [Sprint N] Title

Type: feat | fix | refactor | infra | chore | docs | test
Component: api | ingest | realtime | worker | ai-worker | scheduler | web | edge-agent | sdk-py | sdk-js | cli | infra | docs
Estimate: XS | S | M | L (1h, 4h, 1d, 2d)
Depends on: T-XXXX, T-YYYY
References: [06_PRD F-XXX], [07_DATA_CONTRACTS §X.Y], [08_UI_UX_SPEC §X.Y]

**Description**
What and why in 2–4 sentences.

**Files**
- Create: path/to/new_file.py
- Edit: path/to/existing_file.py
- Delete: path/to/old_file.py (if any)

**Acceptance criteria**
- [ ] Objective testable statement 1
- [ ] Objective testable statement 2
- [ ] Test files added at: tests/...
- [ ] Coverage threshold met
```

---

## 5. Sprint 0 — Bootstrap

**Goal**: Empty repo → fully working monorepo skeleton. Every service starts (even if it does nothing), CI is green, observability shows green dots, dev environment runs in one command.

### T-0001 [S0] Initialize monorepo skeleton

Type: infra · Component: infra · Estimate: M · Depends on: — · References: [02_ARCHITECTURE §6]

**Description**: Create the monorepo directory structure exactly as in [02_ARCHITECTURE §6]. Empty placeholder files where needed. Add root README.

**Files**
- Create: directory tree per [02_ARCHITECTURE §6] including `services/`, `apps/`, `packages/`, `infra/`, `docs/`, `scripts/`, `tools/`
- Create: `README.md`, `LICENSE` (AGPL-3.0), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitignore`, `.editorconfig`, `.gitattributes`
- Create: `pnpm-workspace.yaml`, `package.json` (root), `pyproject.toml` (root marker)
- Move: docs from this set into `docs/`

**Acceptance criteria**
- [ ] `tree -L 3` matches the architecture doc layout
- [ ] `git log` shows initial commit signed
- [ ] LICENSE is AGPL-3.0 verbatim
- [ ] README has project pitch (≤ 100 words), one-liner install, link to `docs/00_INDEX.md`

### T-0002 [S0] Pre-commit and linting setup

Type: infra · Component: infra · Estimate: S · Depends on: T-0001 · References: [05_CODING_STANDARDS §3, §4]

**Files**
- Create: `.pre-commit-config.yaml` with hooks: ruff, ruff-format, prettier, eslint, markdownlint, gitleaks, end-of-file-fixer, trailing-whitespace, check-yaml, check-json, check-merge-conflict, no-commit-to-branch (block direct commits to main)
- Create: `.markdownlint.json`, `.prettierrc.json`, `.prettierignore`, `.eslintrc.cjs`, `.eslintignore`
- Create: `pyproject.toml` with `[tool.ruff]`, `[tool.mypy]` settings per `05_CODING_STANDARDS §6.5`
- Create: `tsconfig.base.json` (strict)
- Create: `Makefile` with targets: `setup`, `lint`, `format`, `test`, `typecheck`, `dev`, `migrate`, `seed`, `reset`, `clean`, `ci`

**Acceptance criteria**
- [ ] `pre-commit install` succeeds; `pre-commit run --all-files` green on initial files
- [ ] `make lint` succeeds on empty repo
- [ ] `make format` is idempotent

### T-0003 [S0] CI pipeline scaffolding (GitHub Actions)

Type: infra · Component: infra · Estimate: M · Depends on: T-0002

**Files**
- Create: `.github/workflows/ci.yml` (lint, typecheck, unit tests on every PR)
- Create: `.github/workflows/build.yml` (build container images on every PR; push only on main and tags)
- Create: `.github/workflows/release.yml` (tag-triggered)
- Create: `.github/workflows/codeql.yml` (security scanning)
- Create: `.github/workflows/dependabot-auto-merge.yml`
- Create: `.github/dependabot.yml` (npm + pip + docker updates weekly)
- Create: `.github/PULL_REQUEST_TEMPLATE.md` per [05_CODING_STANDARDS §4]
- Create: `.github/ISSUE_TEMPLATE/*.yml`

**Acceptance criteria**
- [ ] CI runs on a dummy PR and passes
- [ ] Branch protection rules documented in `infra/github/branch-protection.md` (manually applied)

### T-0004 [S0] Local dev docker-compose stack

Type: infra · Component: infra · Estimate: M · References: [13_DEVOPS_RUNBOOK §2]

**Files**
- Create: `docker-compose.yml` with services: postgres (with TimescaleDB+pgvector image), redis (valkey image), nats, emqx, minio, chirpstack, mailhog
- Create: `docker-compose.override.example.yml`
- Create: `.env.example` per [11_CONFIGURATION_REFERENCE §5]
- Create: `infra/local/postgres/init.sql` (creates DB, extensions, roles)
- Create: `infra/local/emqx/emqx.conf` (allow anonymous in dev only)
- Create: `infra/local/nats/nats.conf` (with JetStream enabled)
- Create: `infra/local/chirpstack/chirpstack.toml`
- Create: `scripts/setup.sh` (the `make setup` implementation)
- Create: `scripts/wait-for-it.sh`

**Acceptance criteria**
- [ ] `make setup` on a fresh clone produces a working stack within 15 minutes
- [ ] All URLs in [13_DEVOPS_RUNBOOK §2.4] return 200 (or 401/403 for protected endpoints)
- [ ] `make stop` cleanly stops all containers; `make reset` rebuilds without errors

### T-0005 [S0] Shared Python base package

Type: feat · Component: api · Estimate: M · References: [05_CODING_STANDARDS §6, §10, §12]

**Description**: Create `services/_shared/` Python package with: structured logging setup, Pydantic settings base, common error types, ULID generation utility, time utilities, OpenTelemetry initializer, NATS client wrapper, Postgres async session factory, Redis client factory.

**Files**
- Create: `services/_shared/pyproject.toml`, `src/yp_shared/__init__.py`
- Create: `src/yp_shared/logging.py` (structlog setup with JSON formatter for prod, console for dev)
- Create: `src/yp_shared/settings.py` (`BaseSettings` with shared vars from [11_CONFIGURATION_REFERENCE §2])
- Create: `src/yp_shared/errors.py` (`AppError` base + per-category subclasses matching [04_GLOSSARY §6])
- Create: `src/yp_shared/ids.py` (ULID generation + parsing per [04_GLOSSARY §3])
- Create: `src/yp_shared/time.py` (UTC now, ISO-8601 parsing, validators)
- Create: `src/yp_shared/observability.py` (OTel tracer, meter init)
- Create: `src/yp_shared/nats.py` (typed publish/subscribe wrappers)
- Create: `src/yp_shared/db.py` (async SQLAlchemy session factory, health check)
- Create: `src/yp_shared/redis.py` (factory + health check)
- Create: `src/yp_shared/health.py` (FastAPI/Starlette router for /healthz, /readyz, /metrics)
- Create: `tests/` with unit tests for every util

**Acceptance criteria**
- [ ] Coverage ≥ 95% on this package
- [ ] All public functions typed
- [ ] `from yp_shared import logger; logger.info("hi", extra_field=1)` produces JSON in prod mode
- [ ] ULID parsing rejects malformed and accepts valid; round-trip works

### T-0006 [S0] Shared TypeScript base package

Type: feat · Component: web · Estimate: M

**Description**: Create `packages/shared-ts/` with: time helpers, ULID, branded types, fetch wrapper with auth, error mapping (mirrors Python error codes), zod schemas matching shared types.

**Files**
- Create: `packages/shared-ts/package.json`, `tsconfig.json`, `src/index.ts`
- Create: `src/ids.ts`, `src/time.ts`, `src/errors.ts`, `src/api-client.ts`, `src/types.ts`

**Acceptance criteria**
- [ ] Buildable with `tsc`
- [ ] Tested with vitest
- [ ] Reused by `apps/web` and `packages/sdk-js` later

### T-0007 [S0] Database migration framework

Type: feat · Component: api · Estimate: S

**Files**
- Create: `services/api/migrations/env.py`, `migrations/script.py.mako`, `alembic.ini`
- Create: `services/api/migrations/versions/0001_initial.py` (creates required extensions: timescaledb, pgvector, pgcrypto, citext)

**Acceptance criteria**
- [ ] `make migrate` creates extensions on a fresh DB
- [ ] `make migrate` is idempotent
- [ ] Downgrade of 0001 cleanly drops extensions

### T-0008 [S0] Skeleton FastAPI api service

Type: feat · Component: api · Estimate: S · Depends on: T-0005, T-0007

**Description**: Bootable FastAPI app with `/healthz`, `/readyz`, `/metrics`, no business endpoints yet. Dockerfile, Pydantic settings, OTel, structlog wired.

**Files**
- Create: `services/api/pyproject.toml`, `Dockerfile`, `src/yp_api/main.py`, `src/yp_api/settings.py`, `src/yp_api/app_factory.py`
- Create: `tests/test_health.py`

**Acceptance criteria**
- [ ] `uvicorn yp_api.main:app` starts; `curl /healthz` → 200
- [ ] Container builds and runs
- [ ] OpenAPI at `/docs` renders

### T-0009 [S0] Skeleton ingest, realtime, worker, ai-worker, scheduler services

Type: feat · Component: ingest, realtime, worker, ai-worker, scheduler · Estimate: M · Depends on: T-0005

**Description**: Each service has a "hello world" implementation that boots, connects to its dependencies (NATS, Postgres, Redis as applicable), exposes /healthz, /readyz, /metrics, logs structured. No business logic.

**Files**
- For each: `services/<n>/pyproject.toml`, `Dockerfile`, `src/yp_<n>/main.py`, `tests/test_health.py`
- realtime: Node.js + uWebSockets.js (`services/realtime/package.json`, `tsconfig.json`, `src/main.ts`)

**Acceptance criteria**
- [ ] All six services start in compose
- [ ] All return /healthz=200 within 30s of boot
- [ ] All log a "service started" line in JSON

### T-0010 [S0] Skeleton web app (Next.js)

Type: feat · Component: web · Estimate: M

**Files**
- Create: `apps/web/package.json`, `next.config.mjs`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`
- Create: `apps/web/src/app/layout.tsx`, `app/page.tsx` (placeholder landing), `app/globals.css`
- Create: `apps/web/src/lib/env.ts` (zod-validated client+server env)
- Install: `next@15`, `react@19`, `tailwindcss`, `shadcn/ui` initial set

**Acceptance criteria**
- [ ] `pnpm dev` starts on http://localhost:3000
- [ ] Lighthouse score ≥ 90 for performance on placeholder page
- [ ] Builds with `next build` no errors

### T-0011 [S0] Skeleton CLI

Type: feat · Component: cli · Estimate: S

**Files**
- Create: `apps/cli/pyproject.toml`, `src/yp_cli/__main__.py` with `typer` app, single command `yp version`

**Acceptance criteria**
- [ ] `pip install -e apps/cli && yp version` prints version

### T-0012 [S0] Local observability stack

Type: infra · Component: infra · Estimate: M · References: [13_DEVOPS_RUNBOOK §10]

**Files**
- Create: `infra/local/observability/docker-compose.yml` (Prometheus, Grafana, Loki, Tempo, Alertmanager, GlitchTip)
- Create: `infra/local/observability/prometheus.yml`
- Create: `infra/local/observability/grafana/datasources/`, `grafana/dashboards/` (one stub dashboard "Platform Overview")

**Acceptance criteria**
- [ ] `make obs-up` brings up stack
- [ ] Grafana at http://localhost:3001 shows API, ingest, etc., as scraped targets all green
- [ ] Loki receives logs from all services

### T-0013 [S0] Documentation site (Astro Starlight)

Type: feat · Component: docs · Estimate: M

**Files**
- Create: `apps/docs/package.json`, `astro.config.mjs`
- Create: `apps/docs/src/content/docs/index.mdx`, `getting-started.mdx`, `concepts/architecture.mdx`
- Configure: redirects from /api/* to OpenAPI viewer

**Acceptance criteria**
- [ ] `pnpm --filter docs dev` serves at http://localhost:4321
- [ ] Search works
- [ ] Builds statically

### T-0014 [S0] Sprint 0 demo

End-of-sprint check:
- [ ] Fresh clone → `make setup` → all services green
- [ ] All `/healthz` endpoints return 200
- [ ] Web app loads
- [ ] Docs site loads
- [ ] Grafana shows green
- [ ] CI is green on `main`

---

## 6. Sprint 1 — Auth & Users

**Goal**: A user can sign up, verify email, log in, request password reset, change password, log out, manage sessions, enable 2FA. All token flows working. Org auto-created on signup.

### T-0101 [S1] Users table, password hashing, sessions table

Type: feat · Component: api · Estimate: M · References: [07_DATA_CONTRACTS §11.1], [09_SECURITY_SPEC §3]

**Files**
- Create: migration `0010_users_and_sessions.py` (tables: `users`, `refresh_tokens`, `magic_links`)
- Create: `services/api/src/yp_api/domain/users/` (entities, value objects, repository protocol)
- Create: `services/api/src/yp_api/infrastructure/persistence/users_repo.py`
- Create: `services/api/src/yp_api/application/auth/password_hasher.py` (argon2id per [09_SECURITY_SPEC §2.2])

**Acceptance criteria**
- [ ] Migration applies and rolls back cleanly
- [ ] Argon2id parameters match spec; verify benchmark: hash takes 100–500ms on dev hardware
- [ ] Repository unit tests use in-memory fake; integration tests use real Postgres

### T-0102 [S1] Sign-up endpoint

Type: feat · Component: api · Estimate: M · Depends on: T-0101 · References: [06_PRD F-100], [07_DATA_CONTRACTS §3.1.1], [09_SECURITY_SPEC §3.2]

**Files**
- Create: `services/api/src/yp_api/interfaces/http/v1/auth.py` (router) and `auth/sign_up.py` (handler)
- Create: `application/auth/sign_up_user.py` (use case)
- Email template: `services/api/templates/email/verify_email.html`

**Acceptance criteria**
- [ ] POST /v1/auth/sign-up creates user, sends verification email, returns 201
- [ ] Email already in use → 409 with `email_taken` error code
- [ ] Password validation per [09_SECURITY_SPEC §3.3]
- [ ] On signup, default Personal org auto-created (T-0201 makes this real)
- [ ] Tests: integration test against real DB, snapshot test for email body

### T-0103 [S1] Email verification flow

Type: feat · Component: api · Estimate: S · Depends on: T-0102

**Acceptance criteria**
- [ ] POST /v1/auth/verify-email with token → user.email_verified_at set, token consumed
- [ ] Tokens single-use, 24h TTL
- [ ] Resend endpoint with rate limit (1 per 60s per email)

### T-0104 [S1] Login endpoint with sessions

Type: feat · Component: api · Estimate: M · Depends on: T-0101 · References: [09_SECURITY_SPEC §4]

**Description**: Issue access JWT (15 min) + refresh token (rotating, 30 days, hashed in DB). Return user info.

**Acceptance criteria**
- [ ] POST /v1/auth/login validates email+password, issues tokens
- [ ] Wrong creds → 401, no info leakage about which was wrong
- [ ] After 5 failed attempts → 60s lockout, 10 attempts → 1 hr lockout (rate limited per IP+email)
- [ ] Refresh token stored hashed (`argon2`) in `user_sessions`
- [ ] Sets HttpOnly, Secure, SameSite=Lax refresh cookie

### T-0105 [S1] Refresh token rotation

Type: feat · Component: api · Estimate: S · Depends on: T-0104

**Acceptance criteria**
- [ ] POST /v1/auth/refresh exchanges refresh token for new access + rotates refresh
- [ ] Reuse of an old refresh token detected → invalidate entire session family, alert audit log
- [ ] Per [09_SECURITY_SPEC §4.3]

### T-0106 [S1] Logout (single + all)

Type: feat · Component: api · Estimate: S

**Acceptance criteria**
- [ ] POST /v1/auth/logout invalidates current session
- [ ] POST /v1/auth/logout-all invalidates all user sessions

### T-0107 [S1] Password reset flow

Type: feat · Component: api · Estimate: M

**Acceptance criteria**
- [ ] POST /v1/auth/password-reset/request → always 204 (no enumeration)
- [ ] POST /v1/auth/password-reset/confirm with token → password updated, all sessions invalidated, all reset tokens consumed
- [ ] Tokens single-use, 1h TTL
- [ ] Email template

### T-0108 [S1] 2FA TOTP setup and verify

Type: feat · Component: api · Estimate: M · References: [09_SECURITY_SPEC §3.5]

**Acceptance criteria**
- [ ] POST /v1/auth/2fa/setup generates TOTP secret, returns QR data + recovery codes
- [ ] POST /v1/auth/2fa/verify activates 2FA after one valid code
- [ ] Login flow updated: if user has 2FA, login returns `2fa_required`; second call POST /v1/auth/2fa/login with code + temp token
- [ ] Recovery code can substitute for TOTP, single-use, log audit event

### T-0109 [S1] Get current user, update profile

Type: feat · Component: api · Estimate: S · References: [06_PRD F-110]

**Acceptance criteria**
- [ ] GET /v1/me returns current user
- [ ] PATCH /v1/me updates display_name, locale, timezone
- [ ] PUT /v1/me/password requires current password
- [ ] PUT /v1/me/email requires re-verification of new email

### T-0110 [S1] FastAPI auth middleware

Type: feat · Component: api · Estimate: M · References: [09_SECURITY_SPEC §4.4]

**Description**: Dependency that extracts and verifies JWT, loads user, populates request context (`request.state.user`, `request.state.org_context`). 401 on missing, 401 on invalid, 403 on disabled user.

**Acceptance criteria**
- [ ] `Depends(current_user)` returns user object
- [ ] Tests for: missing header, malformed token, expired token, valid token, revoked session
- [ ] Latency overhead < 5ms p95

### T-0111 [S1] Web: auth pages

Type: feat · Component: web · Estimate: L · References: [08_UI_UX_SPEC §4.1–§4.6]

**Files**
- Create: `apps/web/src/app/(auth)/login/page.tsx`, `signup/page.tsx`, `forgot-password/page.tsx`, `reset-password/page.tsx`, `verify-email/page.tsx`, `2fa/page.tsx`
- Create: `apps/web/src/lib/auth.ts` (client-side auth store, refresh logic)
- Create: `apps/web/src/components/auth/*`

**Acceptance criteria**
- [ ] All flows work end-to-end against local API
- [ ] Form validation matches API rules; errors render inline
- [ ] Layout matches [08_UI_UX_SPEC]
- [ ] Accessibility: keyboard navigable, ARIA labels, contrast AA
- [ ] Playwright test: full signup → verify → login → reset → 2fa journey

### T-0112 [S1] Email sending infrastructure

Type: feat · Component: worker · Estimate: M · References: [11_CONFIGURATION_REFERENCE §3.4]

**Description**: Worker queue `emails` consumes jobs and sends via SMTP. Templates in Jinja2. Dev: Mailhog. Prod: Postmark/AWS SES via SMTP.

**Files**
- Create: `services/worker/src/yp_worker/handlers/send_email.py`
- Create: `services/worker/src/yp_worker/email/render.py`

**Acceptance criteria**
- [ ] Sign-up flow above results in email visible in Mailhog
- [ ] Failed sends retry with exponential backoff (5 attempts, then dead-letter)
- [ ] Bounces logged for later detection (manual cleanup in Phase 1, automated later)

### T-0113 [S1] Sprint 1 demo

- [ ] User can sign up via web UI
- [ ] Receives verification email (Mailhog)
- [ ] Verifies, logs in, sees /me
- [ ] Resets password
- [ ] Enables 2FA, logs in with TOTP
- [ ] Logout works
- [ ] All e2e tests green

---

## 7. Sprint 2 — Organizations & Projects

**Goal**: Multi-tenancy. User can create orgs, invite members, assign roles, create projects within orgs, switch context between orgs/projects.

### T-0201 [S2] Organizations and memberships tables + auto Personal org

Type: feat · Component: api · Estimate: M · References: [07_DATA_CONTRACTS §11.2], [04_GLOSSARY §5.OrgTier]

**Files**
- Migration `0020_orgs.py`: `organizations`, `organization_members`, `organization_invites`
- Update sign-up handler to create Personal org and add user as `owner`

**Acceptance criteria**
- [ ] On signup, user has exactly one org (`is_personal=true`, tier `free`)
- [ ] Constraint: user is in ≥ 1 org always

### T-0202 [S2] Org CRUD endpoints

Type: feat · Component: api · Estimate: M · References: [07_DATA_CONTRACTS §3.3]

**Acceptance criteria**
- [ ] GET /v1/organizations (lists user's orgs)
- [ ] POST /v1/organizations creates a new org, requester becomes owner
- [ ] GET /v1/organizations/{id}, PATCH (owner only), DELETE (owner only, scheduled deletion 7 days; immediate for Personal forbidden)
- [ ] Personal org name and tier cannot be changed

### T-0203 [S2] Member invite, accept, role change, removal

Type: feat · Component: api · Estimate: L · References: [07_DATA_CONTRACTS §3.3.5–§3.3.10], [09_SECURITY_SPEC §6.2]

**Acceptance criteria**
- [ ] POST /v1/organizations/{id}/invites (admin+ only) sends email with token
- [ ] Token-protected accept endpoint
- [ ] PATCH /v1/organizations/{id}/members/{user_id} changes role
- [ ] Last owner cannot be demoted/removed (constraint)
- [ ] Audit events for all changes

### T-0204 [S2] Projects table and CRUD

Type: feat · Component: api · Estimate: M · References: [06_PRD F-120], [07_DATA_CONTRACTS §11.3]

**Acceptance criteria**
- [ ] `projects` table with project_id (ULID prefix `prj_`), org_id, slug, name, description
- [ ] GET, POST, PATCH, DELETE endpoints
- [ ] Slug unique within org; reserved slugs rejected ([04_GLOSSARY §9])
- [ ] On delete: soft-delete with 30-day grace period

### T-0205 [S2] Project-scoped permission system

Type: feat · Component: api · Estimate: M · References: [09_SECURITY_SPEC §6]

**Description**: Implement RBAC matrix per [04_GLOSSARY ProjectRole]. Decorator/dependency `require_role("editor")` works at endpoint level.

**Acceptance criteria**
- [ ] Policy rules in code generated from a single declaration; no scattered checks
- [ ] Tests for every (role, action) combo per permission matrix
- [ ] 403 returns `forbidden` error code with action name

### T-0206 [S2] Web: org switcher and member management UI

Type: feat · Component: web · Estimate: L · References: [08_UI_UX_SPEC §5]

**Acceptance criteria**
- [ ] Top nav shows current org + project; switcher works
- [ ] Settings → Members page lists, invites, edits, removes
- [ ] Pending invites shown
- [ ] Accept-invite landing page

### T-0207 [S2] Web: project CRUD + onboarding

Type: feat · Component: web · Estimate: M · References: [06_PRD F-199], [08_UI_UX_SPEC §6]

**Acceptance criteria**
- [ ] On first login (no projects), wizard prompts to create first project
- [ ] Projects list page, create/edit/delete
- [ ] Project switcher in top nav

### T-0208 [S2] Tier quotas enforcement scaffolding

Type: feat · Component: api · Estimate: M · References: [04_GLOSSARY §8]

**Description**: Quota service that, given (org_id, quota_kind), returns limit and current usage. Endpoints that grow usage (create project, create device) check before commit. 402 on exceed.

**Acceptance criteria**
- [ ] Free tier: max 3 projects per org (test enforces)
- [ ] Quota check is < 1ms (cached in Redis with 30s TTL, invalidated on write)
- [ ] Quota response includes current and limit for client display

### T-0209 [S2] Sprint 2 demo

- [ ] Two users sign up; user A invites user B to their org as editor
- [ ] B accepts, sees A's org in switcher
- [ ] A creates a project in shared org; B can see and edit it
- [ ] Personal org of B is private; A cannot see it
- [ ] Free tier limits enforced

---

## 8. Sprint 3 — Devices & Profiles

**Goal**: Devices and device profiles can be CRUD'd. Credentials issued per device. Streams can be defined per device. UI lists devices, shows status, lets user view/edit/delete.

### T-0301 [S3] Device profiles

Type: feat · Component: api · Estimate: M · References: [06_PRD F-130], [07_DATA_CONTRACTS §11.5]

**Acceptance criteria**
- [ ] `device_profiles` table; `streams_template` JSONB
- [ ] CRUD endpoints (project-scoped)
- [ ] Built-in profiles seeded: "Generic HTTP", "Generic MQTT", "Dragino LHT65" (LoRa)
- [ ] Cannot delete profile if devices use it

### T-0302 [S3] Devices table and CRUD

Type: feat · Component: api · Estimate: L · References: [06_PRD F-131], [07_DATA_CONTRACTS §11.6]

**Acceptance criteria**
- [ ] `devices` table; ULID prefix `dev_`
- [ ] POST /v1/projects/{id}/devices creates device, optionally instantiating streams from profile
- [ ] List with filters: status, profile, tag, search by name/eui
- [ ] PATCH for name, tags, description, profile
- [ ] DELETE soft-deletes with 30-day grace
- [ ] Quota: free tier max 5 devices/project (config-driven)

### T-0303 [S3] Device credentials

Type: feat · Component: api · Estimate: M · References: [09_SECURITY_SPEC §6.4]

**Description**: Each device has one or more credential rows. Types: `mqtt_password` (random secret hashed), `http_token` (long-lived bearer hashed), `lorawan_keys` (DevEUI/AppEUI/AppKey).

**Acceptance criteria**
- [ ] POST /v1/devices/{id}/credentials issues new credential of given type
- [ ] Plaintext returned exactly once at creation; subsequent GETs only show last 4 chars
- [ ] DELETE revokes (sets revoked_at)
- [ ] LoRa: AppKey shown once, AppEUI/DevEUI editable

### T-0304 [S3] Streams table and CRUD

Type: feat · Component: api · Estimate: M · References: [06_PRD F-142], [07_DATA_CONTRACTS §11.7]

**Acceptance criteria**
- [ ] `streams` table; ULID prefix `str_`
- [ ] One stream per (device_id, key)
- [ ] Type: numeric, boolean, string, json, geo
- [ ] Auto-created from profile on device creation; can add/remove on a device
- [ ] Unit, display name, color (for charts)

### T-0305 [S3] Device state tracking

Type: feat · Component: api · Estimate: M

**Description**: `device_state` view aggregates last-seen, last datapoint timestamp per stream, online/offline based on heartbeat profile. Computed lazily on request, cached 30s.

**Acceptance criteria**
- [ ] Device list returns status field
- [ ] Online if any uplink within profile's expected interval × 2 (default 1h)

### T-0306 [S3] Web: devices list, detail, create

Type: feat · Component: web · Estimate: L · References: [08_UI_UX_SPEC §7]

**Acceptance criteria**
- [ ] Devices index with table, filters, search, bulk actions
- [ ] Create dialog with profile picker
- [ ] Device detail: tabs for Overview, Streams, Credentials, Settings
- [ ] Online status indicator, last seen timestamp

### T-0307 [S3] Web: device profiles management

Type: feat · Component: web · Estimate: M

**Acceptance criteria**
- [ ] Profiles list, create, edit, view JSON template
- [ ] Validation of stream template structure

### T-0308 [S3] Sprint 3 demo

- [ ] Create profile "Soil Sensor" with streams temp+moisture+battery
- [ ] Create device using profile; streams auto-created
- [ ] Issue MQTT password; copy plaintext
- [ ] Status shows offline (no data yet)

---

## 9. Sprint 4 — Ingestion (HTTP + MQTT)

**Goal**: Devices can publish data via HTTP and MQTT. Data is persisted to TimescaleDB. Backpressure handled. NATS event emitted for downstream consumers.

### T-0401 [S4] Telemetry hypertable

Type: feat · Component: api · Estimate: M · References: [07_DATA_CONTRACTS §11.10]

**Files**
- Migration creating `telemetry_data` hypertable, indexes, retention policy (default 30 days for free, configurable)
- Continuous aggregates `telemetry_data_5m`, `telemetry_data_1h`, `telemetry_data_1d`
- Compression policy (compress chunks > 7 days)

**Acceptance criteria**
- [ ] Migration applies; `\d+ telemetry_data` shows hypertable
- [ ] Continuous aggregates created with refresh policy
- [ ] Insert benchmark: 10k rows < 500ms on dev hardware

### T-0402 [S4] HTTP ingest endpoint

Type: feat · Component: api · Estimate: M · References: [06_PRD F-140], [07_DATA_CONTRACTS §3.6]

**Acceptance criteria**
- [ ] POST /v1/ingest accepts single point or batch
- [ ] Auth via device HTTP token (header `X-Device-Token`) or API key
- [ ] Validates payload schema; rejects malformed (400)
- [ ] Publishes to NATS `ingest.raw.v1.<project_id>` (subject per [04_GLOSSARY §7])
- [ ] Returns 202 with accepted count
- [ ] Rate limit per device per [09_SECURITY_SPEC §8]

### T-0403 [S4] Ingest service: NATS consumer + DB writer

Type: feat · Component: ingest · Estimate: L · References: [02_ARCHITECTURE §7]

**Description**: Ingest service consumes `ingest.raw.v1.>`, decodes if codec defined, validates against stream definitions, writes batch to TimescaleDB, publishes `telemetry.datapoint.v1.<project_id>.<device_id>` and `devices.state.v1.<project_id>.<device_id>` events.

**Acceptance criteria**
- [ ] Configurable batch size (default 1000) and flush interval (default 250ms)
- [ ] At-least-once with NATS JetStream ack after successful write
- [ ] Dead-letter subject for poisonous messages
- [ ] Per-stream type coercion (numeric → float, etc.) per [07_DATA_CONTRACTS §11.10]
- [ ] Throughput: 5000 datapoints/sec on dev hardware

### T-0404 [S4] EMQX integration: auth via API + ACL

Type: feat · Component: api, ingest · Estimate: L · References: [02_ARCHITECTURE §7], [07_DATA_CONTRACTS §15]

**Description**: Configure EMQX with HTTP auth pointing at API endpoint. Topic ACL enforced server-side.

**Files**
- `infra/local/emqx/auth_http.conf` configured to call `http://api:8000/internal/mqtt/auth` and `/acl`
- `services/api/src/yp_api/interfaces/http/internal/mqtt.py` (auth + acl handlers)

**Acceptance criteria**
- [ ] Connect with valid device creds → success; topics restricted to `v1/<project_id>/<device_id>/up` for publish
- [ ] Wrong creds → connection refused
- [ ] Topic outside ACL → publish rejected, audit logged
- [ ] Auth latency p95 < 10ms (Redis cache for verified credentials, 60s TTL)

### T-0405 [S4] MQTT bridge: EMQX → NATS

Type: feat · Component: ingest · Estimate: M

**Description**: ingest subscribes to MQTT broker (admin user) on `v1/+/+/up`, republishes payload to NATS `ingest.raw.v1.<project_id>` with metadata.

**Acceptance criteria**
- [ ] Message published via mosquitto_pub appears in NATS within 100ms
- [ ] Loss-free across ingest restart (uses MQTT QoS 1 with durable session)

### T-0406 [S4] Codec system

Type: feat · Component: ingest · Estimate: L · References: [02_ARCHITECTURE §7], [07_DATA_CONTRACTS §11.5]

**Description**: Decoder runs untrusted JS in isolated VM (e.g., `quickjs` via py-mini-racer or wasm). Profile carries `decoder_js`. Function signature: `decode(input: { fport, payload_b64, recv_time }) -> { streams: { key: value } }`. Timeout 200ms, memory 16MB.

**Files**
- `services/ingest/src/yp_ingest/codecs/runtime.py`
- `packages/codecs/dragino/lht65.js` (built-in example)

**Acceptance criteria**
- [ ] Decoder failure does not crash service; raw payload archived for replay
- [ ] CPU/memory limits enforced
- [ ] Built-in codecs library: at least 3 device types

### T-0407 [S4] LoRa: ChirpStack bridge

Type: feat · Component: ingest · Estimate: M · References: [02_ARCHITECTURE §7]

**Description**: ingest subscribes to ChirpStack's MQTT (`application/+/device/+/event/up`), maps ChirpStack DevEUI to platform device_id (lookup table), republishes to NATS as if from MQTT.

**Acceptance criteria**
- [ ] LoRa device registered in ChirpStack via API; uplink simulated with chirpstack-simulator; appears in telemetry within 1s
- [ ] Downlink: POST /v1/devices/{id}/downlink queues via ChirpStack API; documented limitations (next uplink window)

### T-0408 [S4] Web: live telemetry view (basic)

Type: feat · Component: web · Estimate: M

**Acceptance criteria**
- [ ] Device detail → "Live" tab streams datapoints in real time (uses realtime service from T-0501)

### T-0409 [S4] Sprint 4 demo

- [ ] Send HTTP POST → datapoint visible in DB and live view within 500ms
- [ ] Connect mosquitto_pub with device creds → datapoint visible
- [ ] LoRa simulator uplink → datapoint visible
- [ ] Ingest 1000 msg/sec for 5 min sustained without drops

---

## 10. Sprint 5 — Streams, Queries, Realtime

**Goal**: Telemetry can be queried (raw, aggregated). Realtime WebSocket pushes new datapoints to subscribed clients. Aggregates work across timeframes.

### T-0501 [S5] Realtime service: WebSocket subscribe

Type: feat · Component: realtime · Estimate: L · References: [02_ARCHITECTURE §7], [07_DATA_CONTRACTS §3.7]

**Description**: Node + uWebSockets.js. Client connects with JWT or API key. Subscribes to streams via JSON messages. Server consumes NATS `telemetry.datapoint.v1.>` filtered by subscription. Rate limits per connection.

**Acceptance criteria**
- [ ] WS endpoint at `wss://realtime/ws`
- [ ] Authn checked per [09_SECURITY_SPEC §4.5]
- [ ] Subscribe message: `{ "action": "subscribe", "streams": ["str_..."] }`
- [ ] 10k concurrent connections on dev hardware
- [ ] Heartbeat per spec; client idle disconnect after 5 min

### T-0502 [S5] Query: raw telemetry

Type: feat · Component: api · Estimate: M · References: [06_PRD F-143], [07_DATA_CONTRACTS §3.6.5]

**Acceptance criteria**
- [ ] GET /v1/streams/{id}/data?from=...&to=...&limit=... returns up to 10000 points sorted by time desc
- [ ] Pagination via cursor (timestamp, id)
- [ ] Permission: project read role required

### T-0503 [S5] Query: aggregated telemetry

Type: feat · Component: api · Estimate: M · References: [06_PRD F-144], [07_DATA_CONTRACTS §3.6.6]

**Acceptance criteria**
- [ ] GET /v1/streams/{id}/aggregate?from=...&to=...&interval=5m&fn=avg returns time-bucketed aggregates
- [ ] Functions: avg, min, max, sum, count, first, last
- [ ] Routes to appropriate continuous aggregate when interval matches; falls back to runtime aggregation
- [ ] Max time range: 1 year (free), 5 years (paid); enforce

### T-0504 [S5] Query: multi-stream query

Type: feat · Component: api · Estimate: M · References: [06_PRD F-145]

**Acceptance criteria**
- [ ] POST /v1/queries with body: { streams: [...], from, to, interval, fn }
- [ ] Returns aligned time series for all requested streams
- [ ] Up to 20 streams per request

### T-0505 [S5] CSV / JSON export

Type: feat · Component: worker · Estimate: M · References: [06_PRD F-146]

**Description**: Long-running export jobs via worker. Writes to MinIO, signed URL emailed.

**Acceptance criteria**
- [ ] POST /v1/streams/{id}/export starts job, returns job id
- [ ] Job consumes from `exports` queue, streams CSV to MinIO
- [ ] Email with link when done
- [ ] Limits: 10M rows per export (free 1M)

### T-0506 [S5] Web: line chart on stream detail

Type: feat · Component: web · Estimate: M

**Acceptance criteria**
- [ ] Stream detail page shows chart (recharts or similar)
- [ ] Time range picker: 1h, 24h, 7d, 30d, custom
- [ ] Aggregation auto-selected based on range
- [ ] Live mode toggle (uses WS)

### T-0507 [S5] Sprint 5 demo

- [ ] Push data, see it on chart in real time
- [ ] Query last 7 days as 1h aggregates
- [ ] Export 100k rows as CSV; receive email link

---

## 11. Sprint 6 — Dashboards & Widgets

**Goal**: User can build dashboards with multiple widgets, share them publicly (read-only).

### T-0601 [S6] Dashboards table and CRUD

Type: feat · Component: api · Estimate: M · References: [06_PRD F-150], [07_DATA_CONTRACTS §11.8]

**Acceptance criteria**
- [ ] `dashboards` table; `definition` JSONB schema-validated against [07_DATA_CONTRACTS §11.8.2]
- [ ] CRUD endpoints
- [ ] Public sharing: `is_public` flag + slug

### T-0602 [S6] Widget types implementation

Type: feat · Component: api, web · Estimate: L · References: [04_GLOSSARY §5.WidgetType], [06_PRD F-151–F-156]

**Description**: Backend validates widget config; frontend renders. Types: line_chart, bar_chart, gauge, single_value, table, map.

**Acceptance criteria**
- [ ] All six widget types render correctly
- [ ] Each has a config form in the dashboard editor
- [ ] Server-side validation rejects invalid widget configs

### T-0603 [S6] Web: dashboard view (read mode)

Type: feat · Component: web · Estimate: M

**Acceptance criteria**
- [ ] Dashboard URL `/p/{project}/d/{slug}` renders all widgets
- [ ] Live updates via WS (auto-subscribe to all streams used)
- [ ] Time range picker affects all widgets
- [ ] Public mode (no auth) works for `is_public` dashboards

### T-0604 [S6] Web: dashboard editor (drag, drop, configure)

Type: feat · Component: web · Estimate: L · References: [08_UI_UX_SPEC §10]

**Acceptance criteria**
- [ ] Grid layout with resizable widgets (react-grid-layout)
- [ ] Add widget palette
- [ ] Per-widget config dialog
- [ ] Save/discard
- [ ] Undo last change

### T-0605 [S6] Dashboard templates

Type: feat · Component: api, web · Estimate: M · References: [06_PRD F-157]

**Acceptance criteria**
- [ ] 3 built-in templates: "Single Device Overview", "Multi-Device Comparison", "Aggregate Health"
- [ ] "Create from template" path uses current project's devices

### T-0606 [S6] Sprint 6 demo

- [ ] Build a 4-widget dashboard live
- [ ] Toggle public, share link, see it without login
- [ ] Live data updates without refresh

---

## 12. Sprint 7 — Rules & Alerts

**Goal**: User can define rules that trigger on telemetry conditions, generating alerts that fire to channels (email, webhook, MQTT downlink).

### T-0701 [S7] Rules table and CRUD

Type: feat · Component: api · Estimate: M · References: [06_PRD F-160], [07_DATA_CONTRACTS §10]

**Acceptance criteria**
- [ ] `rules` table; `spec` JSONB validated against rule schema [07_DATA_CONTRACTS §10.2]
- [ ] CRUD endpoints
- [ ] Rule trigger types: threshold, condition_expression, schedule, no_data, geofence

### T-0702 [S7] Rule evaluator (worker)

Type: feat · Component: worker · Estimate: L

**Description**: Worker subscribes to `telemetry.datapoint.v1.>` and `rules.changed.v1.>`. Maintains in-memory rule registry per project. Evaluates rules on each datapoint. State machine (per [04_GLOSSARY AlertState]) transitions, debounce/cooldown handling.

**Acceptance criteria**
- [ ] Threshold rule fires when crossed; resolves when uncrossed; cooldown respected
- [ ] No-data rule fires when no datapoint within window (scheduled check)
- [ ] Multiple replicas: each handles a partition by project_id (consistent hash)
- [ ] Latency from datapoint to alert event < 1s p95

### T-0703 [S7] Alerts table and channels

Type: feat · Component: api, worker · Estimate: M · References: [06_PRD F-163–F-165]

**Acceptance criteria**
- [ ] `alerts` table records every fire/resolve
- [ ] Channels (email, webhook, SMS-Phase 2, MQTT downlink): handler per type
- [ ] Email channel: via worker email queue
- [ ] Webhook channel: signed POST per [07_DATA_CONTRACTS §14], retry policy
- [ ] MQTT downlink channel: publishes to `v1/<project>/<device>/down`

### T-0704 [S7] Alert acknowledgement and resolution UI

Type: feat · Component: api, web · Estimate: M

**Acceptance criteria**
- [ ] POST /v1/alerts/{id}/acknowledge
- [ ] POST /v1/alerts/{id}/resolve
- [ ] Web: alerts inbox; filter by state, severity, device
- [ ] Bell badge in nav; live updates via WS

### T-0705 [S7] Web: rule editor

Type: feat · Component: web · Estimate: L · References: [08_UI_UX_SPEC §12]

**Acceptance criteria**
- [ ] Visual builder for threshold rules
- [ ] Advanced mode: JSON editor with schema validation
- [ ] Test mode: replay last 24h of data, show would-be alerts
- [ ] Channel configuration

### T-0706 [S7] Sprint 7 demo

- [ ] Define rule "temp > 30 for 5min"
- [ ] Push synthetic data crossing threshold
- [ ] Email arrives within 1 min
- [ ] Webhook receives signed POST
- [ ] Acknowledge alert in UI

---

## 13. Sprint 8 — API Keys, SDKs, CLI

**Goal**: Developers can build on the platform. API keys with scopes, Python and JS SDKs, CLI for ops.

### T-0801 [S8] API key management

Type: feat · Component: api · Estimate: M · References: [06_PRD F-170], [07_DATA_CONTRACTS §3.10], [09_SECURITY_SPEC §6.4]

**Acceptance criteria**
- [ ] POST /v1/projects/{id}/api-keys creates key (returns plaintext once)
- [ ] Scopes per [04_GLOSSARY §5.APIKeyScope]
- [ ] List, revoke endpoints
- [ ] Key prefix `yp_pk_` and `yp_sk_` (publishable/secret) for visual differentiation
- [ ] Verified at API auth middleware; 1ms p95 (cache)

### T-0802 [S8] Python SDK

Type: feat · Component: sdk-py · Estimate: L · References: [12_CLIENT_INTERFACES_SPEC §2]

**Files**
- `packages/sdk-py/pyproject.toml`, `src/yourplatform/__init__.py`, `client.py`, `models.py`, `exceptions.py`, `mqtt.py`

**Acceptance criteria**
- [ ] Client init via `Client(api_key=..., base_url=...)`
- [ ] Methods cover: send_telemetry, get_telemetry, query, list_devices, create_device, etc., per spec
- [ ] Auto-retries with backoff per [09_SECURITY_SPEC §8.3]
- [ ] Async (`AsyncClient`) and sync versions
- [ ] Generated from OpenAPI where possible; hand-curated ergonomic layer on top
- [ ] PyPI publish workflow (test on pre-release, real on tag)

### T-0803 [S8] JavaScript SDK

Type: feat · Component: sdk-js · Estimate: L · References: [12_CLIENT_INTERFACES_SPEC §3]

**Acceptance criteria**
- [ ] Works in Node 22+ and modern browsers (ES2022)
- [ ] TypeScript types
- [ ] Tree-shakeable
- [ ] Same method coverage as Python SDK
- [ ] WebSocket subscribe helper
- [ ] npm publish workflow

### T-0804 [S8] Arduino library

Type: feat · Component: sdk-arduino · Estimate: M · References: [12_CLIENT_INTERFACES_SPEC §4]

**Acceptance criteria**
- [ ] Header-only or single .cpp
- [ ] ESP32 + ESP8266 + Arduino MKR support
- [ ] Connects MQTT with TLS, publishes telemetry, subscribes downlink
- [ ] Example sketches: temperature sensor, GPS tracker
- [ ] Arduino Library Manager submission

### T-0805 [S8] CLI feature complete

Type: feat · Component: cli · Estimate: M · References: [12_CLIENT_INTERFACES_SPEC §5]

**Acceptance criteria**
- [ ] `yp login`, `yp logout`, `yp config`
- [ ] `yp project list/create/use`
- [ ] `yp device list/create/show/delete`
- [ ] `yp send <device> <stream> <value>`
- [ ] `yp tail <stream>` (live)
- [ ] `yp export <stream> --from --to --out`
- [ ] `yp dashboard list/import/export`
- [ ] Self-update: `yp update`

### T-0806 [S8] Sprint 8 demo

- [ ] Create API key
- [ ] Python script: send 100 datapoints
- [ ] JS script in browser console: subscribe live
- [ ] CLI: `yp tail` shows them

---

## 14. Sprint 9 — Marketing, Docs, Onboarding, Audit

**Goal**: Anonymous visitor → signed-up user → first telemetry within 10 min. Audit log captures everything.

### T-0901 [S9] Marketing site

Type: feat · Component: web · Estimate: L · References: [06_PRD F-191], [08_UI_UX_SPEC §14]

**Acceptance criteria**
- [ ] Pages: home, features, pricing, docs link, blog stub, contact, about, oss
- [ ] Lighthouse ≥ 95 perf, ≥ 95 accessibility
- [ ] OG tags, sitemap.xml, robots.txt
- [ ] Pricing reflects [01_STRATEGIC_BLUEPRINT]

### T-0902 [S9] Docs content (Phase 1)

Type: docs · Component: docs · Estimate: L

**Acceptance criteria**
- [ ] Getting Started (5 min quickstart)
- [ ] Concepts: project, device, stream, dashboard, rule
- [ ] How-to guides: connect ESP32, connect Raspberry Pi, build a dashboard, set up alerts
- [ ] API reference (auto from OpenAPI)
- [ ] SDK references (auto from typedoc/sphinx)
- [ ] Self-host guide

### T-0903 [S9] Onboarding wizard

Type: feat · Component: web · Estimate: M · References: [06_PRD F-199]

**Acceptance criteria**
- [ ] After first login: 4-step wizard (create project → create device → send first datapoint via curl → see it on a one-widget dashboard)
- [ ] Skippable; resumable
- [ ] Telemetry: track step completion (anonymous if user opted in)

### T-0904 [S9] Audit log

Type: feat · Component: api · Estimate: M · References: [06_PRD F-198], [07_DATA_CONTRACTS §11.13], [04_GLOSSARY §5.AuditAction]

**Acceptance criteria**
- [ ] All mutating endpoints emit audit event via NATS
- [ ] Persisted to `audit_events` (TimescaleDB hypertable)
- [ ] GET /v1/organizations/{id}/audit with filters
- [ ] Owners only; tier gated (free: 7d retention, paid: 1y)

### T-0905 [S9] Self-host distribution

Type: infra · Component: infra · Estimate: M · References: [06_PRD F-195]

**Acceptance criteria**
- [ ] `docker-compose.production.yml` with sane defaults for self-hosters
- [ ] One-line install script: `curl -fsSL https://get.yourplatform.io | bash`
- [ ] Helm chart in `infra/helm/` for Kubernetes self-hosters
- [ ] Self-host docs covering: TLS setup, backups, upgrade

### T-0906 [S9] Status page wiring

Type: infra · Component: infra · Estimate: S · References: [13_DEVOPS_RUNBOOK §10.6]

**Acceptance criteria**
- [ ] Status page deployed at separate provider
- [ ] Uptime Kuma probes set up
- [ ] Linked from web app footer

### T-0907 [S9] Sprint 9 demo

- [ ] Anonymous user lands on marketing → docs → quickstart
- [ ] Signs up; onboarding completes in < 10 min including curl-test
- [ ] Audit log shows all their actions
- [ ] Status page green

---

## 15. Sprint 10 — Hardening & Beta

**Goal**: Production-ready. Load tested. Security reviewed. Backup drill passed. Beta sign-ups invited.

### T-1001 [S10] Provision production infrastructure

Type: infra · Component: infra · Estimate: L · References: [13_DEVOPS_RUNBOOK §7]

**Acceptance criteria**
- [ ] Hetzner Tier A live
- [ ] All Ansible playbooks idempotent
- [ ] Caddy auto-HTTPS verified
- [ ] Secrets via age, rotated keys generated

### T-1002 [S10] Production deploy pipeline

Type: infra · Component: infra · Estimate: M · References: [13_DEVOPS_RUNBOOK §8]

**Acceptance criteria**
- [ ] GitHub Actions workflow `deploy-prod.yml` with manual approval gate
- [ ] Zero-downtime rolling per spec
- [ ] Tested on synthetic version bump

### T-1003 [S10] Backup setup and restore drill

Type: infra · Component: infra · Estimate: M · References: [13_DEVOPS_RUNBOOK §9]

**Acceptance criteria**
- [ ] pgBackRest configured to Storage Box and B2
- [ ] First full backup verified
- [ ] Restore drill performed; documented in `runbook/drill-log.md` with timing
- [ ] Verify-backup script running weekly

### T-1004 [S10] Load test

Type: test · Component: infra · Estimate: M · References: [10_TEST_PLAN §9]

**Acceptance criteria**
- [ ] Tool: k6 or Locust
- [ ] Scenarios: 1000 devices each pushing 1 msg/min for 1 hour; 10k WS subscribers; 100 dashboards loading concurrently
- [ ] All SLOs met or fix-tickets opened

### T-1005 [S10] Security review

Type: chore · Component: infra · Estimate: M · References: [09_SECURITY_SPEC §15]

**Acceptance criteria**
- [ ] OWASP ASVS Level 1 self-assessment passed
- [ ] Security headers verified via securityheaders.com (A+)
- [ ] CSP, HSTS, COOP, COEP, X-Frame-Options set
- [ ] DAST scan with OWASP ZAP, no high/critical findings
- [ ] Dependency audit: no high/critical CVEs unfixed
- [ ] Secret scan on git history (gitleaks); clean

### T-1006 [S10] Observability dashboards live

Type: infra · Component: infra · Estimate: M · References: [13_DEVOPS_RUNBOOK §10]

**Acceptance criteria**
- [ ] All dashboards from §10.3 deployed
- [ ] All alerts from §10.4 active
- [ ] Founder receives push notifications on test critical alert

### T-1007 [S10] Beta program

Type: chore · Component: marketing · Estimate: S

**Acceptance criteria**
- [ ] Closed beta sign-up form on marketing site
- [ ] Invite code system: free Pro tier for 6 months for beta users
- [ ] Onboard 10 beta users; collect feedback weekly
- [ ] Beta exit criteria: 5 customers ran for 2 weeks without P0

### T-1008 [S10] Sprint 10 demo

- [ ] Production live at app.<domain>
- [ ] Backups verified
- [ ] Load test passing
- [ ] Status page accurate
- [ ] First beta user onboarded

---

## 16. Sprint 11 — Launch & Paid GA

**Goal**: Move from beta to general availability. Take payment. Public launch.

### T-1101 [S11] Stripe billing integration

Type: feat · Component: api · Estimate: L · References: [06_PRD F-220 from Phase 2 outline]

Note: Even though "billing" is technically Phase 2 in the PRD outline, GA without billing is wishful thinking. Pull the basic Stripe Checkout integration into Sprint 11.

**Acceptance criteria**
- [ ] Stripe customer per org
- [ ] Subscription per tier
- [ ] Checkout session for upgrade
- [ ] Webhook handler for invoice events; updates `subscriptions` table
- [ ] Tier change applies immediately
- [ ] Failed payment grace period: 7 days, then downgrade to free
- [ ] No PHI/no PCI: cards via Stripe Checkout (we never see them)

### T-1102 [S11] Pricing page live

Type: feat · Component: web · Estimate: S

**Acceptance criteria**
- [ ] Pricing page reflects [01_STRATEGIC_BLUEPRINT]
- [ ] CTA → Stripe Checkout for paid tiers
- [ ] FAQ covers refunds, downgrades, self-host

### T-1103 [S11] Legal: terms, privacy, DPA

Type: docs · Component: web · Estimate: M

**Acceptance criteria**
- [ ] Terms of Service
- [ ] Privacy Policy (GDPR-compliant)
- [ ] Data Processing Agreement (B2B template)
- [ ] Cookie consent banner (lawful)
- [ ] Sub-processors list

### T-1104 [S11] Launch readiness checklist

Type: chore · Estimate: S

**Acceptance criteria**
- [ ] All P0 bugs fixed
- [ ] Product Hunt assets prepared
- [ ] Hacker News "Show HN" draft
- [ ] Twitter/X, LinkedIn, Reddit posts queued
- [ ] First customer testimonials drafted
- [ ] Support inbox routed; SLAs documented
- [ ] On-call rotation defined (founder solo: 24h response committed only)

### T-1105 [S11] Take first payment

- [ ] First paying customer onboarded
- [ ] Confirm Stripe payment, dunning works on test card

---

## 17. Phase 2 outline (post-MVP, sketched only)

These are tickets to be detailed when Phase 1 stabilizes.

| Sprint | Theme | Major tickets |
|---|---|---|
| S12–S13 | AI-native I (Insights) | NL-to-query (text → SQL/aggregation), anomaly detection per stream, AI-generated dashboard from a sentence |
| S14–S15 | AI-native II (Agents) | Rule auto-suggester ("based on past data, suggest 3 rules"), root-cause analyzer (alert → "likely cause: …"), generated codecs from PDF datasheet |
| S16 | Advanced rules | Rule chains, time-of-day windows, multi-stream conditions, ML-based anomaly trigger |
| S17 | SMS alerts + on-call rotation | Twilio integration, schedules, escalation policies |
| S18 | Edge computing | Edge-agent v1 (run rules locally on Raspberry Pi, sync deltas), offline buffering |
| S19 | Marketplace | Codec marketplace (community contributions, signed), template marketplace |
| S20 | Enterprise readiness | SSO (SAML), SCIM provisioning, on-prem support, advanced RBAC |

Phase 3+ adds HA, multi-region, federated query, white-label.

---

## 18. Risks register

Track these continuously. Update PR description when a ticket touches a risk.

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Solo dev burnout | High | Severe | Strict 5-day cadence; weekly retrospective with self; cap commitments |
| First customer hits scale we haven't tested | Medium | High | Aggressive load testing pre-launch; tier limits enforce caps |
| LoRaWAN integration complexity underestimated | Medium | Medium | ChirpStack handles 95%; we just bridge. Buy a real gateway for testing early |
| AI features become must-have before we ship them | Medium | Medium | MVP works without AI; it's a differentiator not a dependency |
| Self-host customers report security issues we have to fix in prod simultaneously | Medium | High | Coordinated disclosure policy in [09_SECURITY_SPEC §14]; security advisories via GitHub |
| Postgres becomes bottleneck before Phase 3 | Low | High | TimescaleDB compression + continuous aggregates buy a long runway. Vertical scale path documented in [13_DEVOPS_RUNBOOK §14.3] |
| Stripe webhook downtime causes billing drift | Low | Medium | Reconciliation job runs nightly, compares Stripe truth to local |
| Cloudflare account loss | Low | Catastrophic | Hardware 2FA, recovery codes in fire safe, second admin (per [13_DEVOPS_RUNBOOK §15.3]) |
| Competitor copies feature set | High | Low | Speed of execution is the moat; AGPL prevents vendoring |
| Hetzner outage at launch | Low | High | Status page + transparent comms + tested DR plan |

---

## Appendix: Sprint cadence template

Every sprint:

**Monday**
- Read prior sprint retro
- Pick top tickets from this sprint
- Update CHANGELOG.md "Unreleased" with planned items

**Tuesday–Thursday**
- Build, PR, merge
- Deploy to staging on merge
- 30-min daily standup-with-self: what shipped, what's blocked

**Friday**
- Verify all tickets in sprint merged
- Run end-of-sprint demo checklist
- Update playbook ticket statuses (mark done in this doc via PR)
- Retro: what worked, what slowed me down, what to change next sprint
- If staging green and demo passes: tag and deploy to prod

**Weekend** (if working)
- Documentation only. No new features. Code touched on weekends has 2× bug rate.

---

## Closing principle

> The playbook is the contract between past-you (the planner) and future-you (the implementer). Every ambiguity in the playbook is a future bug. When in doubt, **stop and clarify the spec, don't make a judgment call**. The whole point is to reduce decisions at build time.
