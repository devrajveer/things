# Security Specification

The complete security policy. Auth flows, authorization, secret management, hardening, threat model, incident response. **Every code path that touches credentials, user data, or external input must conform.**

> Cross-references: API endpoints in [07_DATA_CONTRACTS §2.1], DB tables in [07_DATA_CONTRACTS §5.1], code rules in [05_CODING_STANDARDS §12].

---

## Table of contents

- §1 Threat model
- §2 Authentication
- §3 Authorization
- §4 Session and token management
- §5 Secret and credential storage
- §6 Network and transport security
- §7 Input validation and output encoding
- §8 Multi-tenancy isolation
- §9 Logging, audit, and PII handling
- §10 Dependency and supply-chain security
- §11 Hardening checklist (per service)
- §12 Vulnerability disclosure and incident response

---

## 1. Threat Model

### 1.1 Trust boundaries

```
INTERNET                 │ DMZ                    │ INTERNAL
                         │                        │
[ Browser ]──TLS─────────│─▶[ Caddy ]─────────────│─▶[ api ]──┐
[ Device  ]──TLS/MQTT────│─▶[ EMQX ]──auth-hook───│──────────┤
[ Webhook ]──HMAC────────│◀─[ worker ]            │           ├─▶[ Postgres ]
                         │                        │           ├─▶[ Redis ]
                         │                        │           ├─▶[ NATS ]
                         │                        │           └─▶[ MinIO ]
```

- **Untrusted:** Browsers, devices, public webhook receivers, NPM/PyPI mirrors, LLM providers.
- **Semi-trusted:** Authenticated users (could be malicious within their own scope).
- **Trusted:** Internal service-to-service traffic (within K3s pod network or VPC).

### 1.2 Top threats and primary mitigations

| Threat | Mitigation (primary) | Mitigation (secondary) |
|---|---|---|
| **Credential stuffing** on user login | Rate limit + account lock (F-102) | Magic link option, 2FA in Phase 2 |
| **Token theft via XSS** | HTTP-only secure cookies for session, no token in localStorage | CSP headers, sanitisation |
| **Token theft via supply-chain JS** | Pin and audit all NPM dependencies; subresource integrity for CDN assets | Subresource freezes, dependabot |
| **CSRF** on state-changing endpoints | SameSite=Strict cookies + Origin header check | Custom header for state changes |
| **Data exfiltration cross-tenant** | `project_id` filter enforced in repository layer; integration tests for every endpoint | Postgres RLS in Phase 3 |
| **SQL injection** | Parameterised queries only (SQLAlchemy params), no string SQL | CI rule banning string interpolation in `.execute()` |
| **Webhook SSRF** | URL validation against deny-list; outbound proxy with allow-list | DNS rebinding protection |
| **MQTT topic spoofing** | Per-device ACL; client_id ↔ topic prefix enforced | EMQX hook callback |
| **Brute-force device tokens** | Long random tokens (256 bits); rate-limit per IP and per device | Token rotation on suspicious patterns |
| **Replay of webhook deliveries** | Timestamp + HMAC signature (5-min window) | Receivers validate per spec |
| **Replay of refresh tokens** | Single-use rotation; replay invalidates all tokens for user | Audit + email notification |
| **Insider threat (founder access)** | All prod access via SSH keys, audited. Critical actions require multi-step confirmation | Audit log integrity (Phase 3: append-only WORM storage) |
| **Compromised LLM provider returning malicious tool calls** | Tool-use response validated against schema before execution | All AI proposals are previewed, never auto-applied |
| **Denial of service via slow MQTT clients** | Connection rate limit, max-inflight cap, idle timeout | Cloudflare in front |
| **Denial of service via expensive queries** | Query time-out, cost-based limits, cached aggregates | Per-key rate limits |
| **Data loss via bad migration** | Migrations require dry-run on staging, never in same release as code that writes new shape | Backups, point-in-time recovery |
| **Secrets in source/logs/errors** | Pre-commit secret scanning, log redaction, structured exception classes | Secrets scanning in CI |

### 1.3 Out of scope (Phase 1)

Documented explicit non-goals so an agent doesn't over-engineer:
- Defending against state-level adversaries.
- Hardware tampering protection on customer devices.
- HSM-backed key custody (cloud KMS in Phase 5).
- Real-time threat intel feeds.

---

## 2. Authentication

### 2.1 User authentication methods (Phase 1)

| Method | When | Notes |
|---|---|---|
| Email + Password | Default sign-in | Argon2id hashing, complexity rules below |
| Magic Link | Passwordless option | 15-min single-use token |
| Refresh Token | After login | Rotated on every use |

Phase 2 adds TOTP 2FA. Phase 4 adds WebAuthn/passkeys. Phase 5 adds SSO (OIDC, SAML).

### 2.2 Password rules

- **Minimum length:** 12 characters.
- **Complexity:** at least 3 of: lowercase, uppercase, digit, symbol.
- **Common-password check:** rejected if in top 100K from `pwned-passwords` k-anonymity API or local list (`packages/sec-data/common-passwords.txt`).
- **Hashing:** Argon2id with `memory=65536, iterations=3, parallelism=4`. Library: `argon2-cffi` (Python).
- **Pepper (optional, on by default):** server-side `PASSWORD_PEPPER` env var (see [11_CONFIGURATION_REFERENCE §3.2]) appended before hash. Rotation requires migration script.
- **Rehash on login:** if argon2 params changed since last hash, rehash on successful auth.

### 2.3 Login rate limit

Per email AND per IP, separately:
- **5 failed attempts in 10 minutes** → lock account/IP for 15 minutes, return `rate_limited`.
- Lock counter stored in Redis (`auth:fail:email:<hash>` and `auth:fail:ip:<ip>`).
- After lock: notification email to user.
- Successful login resets counters.
- Implement constant-time comparison so failures and successes take similar wall-clock time.

### 2.4 Email enumeration prevention

For `signup`, `password-reset`, `magic-link`: response is identical whether or not the email exists. Same status code, similar response time, same body shape.

### 2.5 Email verification

- Required to take certain actions: send invites, upgrade tier, share dashboards.
- Not required to ingest data or use the API (so devs can build immediately).
- Verification email sent once on signup; can be resent up to 1×/60s.

### 2.6 Device authentication

- **MQTT:** username/password basic auth, validated by EMQX HTTP webhook to `api/internal/mqtt/auth`. Result cached 5 min in EMQX.
- **HTTP:** `Authorization: Bearer <http_token>`. Token format: 32 random URL-safe bytes.
- **Validation:** server hashes the presented token (Argon2id) and compares to stored hash. Hashing makes lookup expensive — mitigated by cache (Redis) keyed on the truncated raw token after first validation, TTL 5 min.

### 2.7 API key authentication

- Format: `yp_<env>_<32_random_url_safe_chars>`. `<env>` = `live` or `test`.
- Token stored as Argon2id hash. Plaintext shown once on creation.
- Lookup-friendly prefix: first 12 chars stored separately for cache-key. Hash compared on miss.
- Scopes enforced per-endpoint via decorator/middleware (see [§3.3]).

---

## 3. Authorization

### 3.1 Authorization model (Phase 1)

Single-user-per-org in Phase 1. Authorization simplifies to:
- A user owns an organisation; only the owner has any rights to its resources.
- A user accessing project resources must be the owner of the org that owns the project.

Phase 3 introduces RBAC roles (`owner`, `admin`, `editor`, `viewer`) and team memberships.

### 3.2 Authorization checks — where they live

- **Layer:** Application use cases (NOT in repositories, NOT in interfaces).
- **Pattern:** Each use case takes `actor` and the resource ID. Loads resource. Calls `policy.check(actor, action, resource)` before mutating.
- **Default:** deny. Every check explicit. No "if admin then *" wildcard logic.

```python
# good
class DisableDeviceUseCase:
    async def execute(self, cmd: DisableDeviceCommand) -> None:
        device = await self.repo.get(cmd.project_id, cmd.device_id)
        if device is None:
            raise DeviceNotFound(cmd.device_id)
        await self.policy.assert_can(cmd.actor, "device.disable", device)
        device.disable()
        await self.repo.save(device)
```

### 3.3 API key scopes

| Scope | Allowed endpoints (Phase 1) |
|---|---|
| `read` | All `GET` |
| `write` | All `GET` + `POST /v1/ingest` + `POST /v1/projects/.../devices/.../...` (limited mutations) |
| `admin` | Everything except billing |

In code: each route handler declares `required_scopes`. The auth middleware enforces.

### 3.4 Cross-tenant defense

- Every database query that touches tenant data **must filter by `project_id`**, enforced by repository pattern.
- Linter rule: any SQL/ORM call from `infrastructure/` that omits `project_id` in WHERE on a tenant-scoped table fails CI.
- Integration test suite (`tests/integration/test_cross_tenant_isolation.py`) for every endpoint:
  1. Create two projects in different orgs.
  2. Authenticate as user A.
  3. Try to access project B's resource by ID.
  4. Assert 404 or 403.
- Phase 3 adds Postgres RLS (Row-Level Security) with `app.current_project_id` set on each connection — defense in depth.

### 3.5 Resource ID format check

ID format validated at the route layer (Pydantic regex). Mismatched prefix (e.g., passing a user_id where device_id expected) fails with `invalid_id_format` (422), preventing IDOR attempts that try to brute-force IDs.

---

## 4. Session and Token Management

### 4.1 Access token (JWT)

- **Algorithm:** HS256 with a server-side `JWT_SECRET` (≥256 bits, rotated per [§5.4]).
- **Lifetime:** 15 minutes.
- **Claims:**
  ```json
  {
    "sub": "usr_...",
    "iat": 1736932200,
    "exp": 1736933100,
    "iss": "https://api.<host>",
    "aud": "yp-api",
    "jti": "01H..."
  }
  ```
- **Storage:** sent in `Authorization: Bearer` header by SDK and CLI. Browser stores in HTTP-only secure cookie (preferred) OR memory (in-app). **Never localStorage or sessionStorage.**
- **Validation:** signature, exp, iss, aud on every request. Cached as parsed object for the request lifetime.

### 4.2 Refresh token

- **Format:** opaque, 64 random URL-safe bytes (~344 bits).
- **Lifetime:** 30 days from issue. Sliding: each refresh resets the 30-day clock.
- **Storage:** server stores hashed (Argon2id) in `refresh_tokens` table; client stores in HTTP-only secure cookie or secure storage.
- **Single-use:** every refresh issues a new refresh token and invalidates the old. The previous token is marked `used_at`.
- **Replay detection:** if a refresh token comes in already marked used, **revoke all refresh tokens for the user**, log audit event, send email.
- **Family tracking (Phase 2):** group rotated tokens into a family for full chain invalidation on compromise.

### 4.3 Browser cookie attributes

For session cookies set by web app:
```
Set-Cookie: <name>=<value>;
  HttpOnly;
  Secure;
  SameSite=Lax;
  Path=/;
  Domain=<app-domain>;
  Max-Age=<seconds>
```

`SameSite=Lax` lets links from email work; state-changing endpoints additionally require an `Origin` header check.

### 4.4 Logout

- `/v1/auth/logout`: invalidates the presented refresh token.
- `/v1/auth/logout-all`: invalidates every refresh token for the user.
- Access tokens are not invalidated (short-lived); critical actions can require recent-auth check.

### 4.5 Recent-auth requirement

For sensitive actions (change password, delete account, generate API key):
- Server checks `iat` of access token; if older than 10 minutes, returns `requires_reauth` (custom 401-class code).
- UI prompts for password re-entry, gets fresh tokens, retries.

---

## 5. Secret and Credential Storage

### 5.1 At rest

| Secret type | Storage | Notes |
|---|---|---|
| User password | `users.password_hash` (Argon2id) | Never reversible |
| Refresh token | `refresh_tokens.hashed_token` (Argon2id, low params for speed) | Cached lookup OK |
| Magic link / reset token | `magic_links.hashed_token` (Argon2id) | One-time use |
| Device MQTT password | `device_credentials.mqtt_password_hash` (Argon2id) | Cached after validation |
| Device HTTP token | `device_credentials.http_token_hash` (Argon2id) | Cached after validation |
| API key | `api_keys.hashed_secret` (Argon2id) | Prefix stored plain for lookup |
| Webhook secret | `webhooks.secret_hash` (HMAC key derivation; never re-displayed) | Used to sign outbound payloads |
| LoRa AppKey (P3) | Encrypted (AES-256-GCM) under `LORA_KEY_KEK` | KEK per-environment |
| LoRa AppSKey/NwkSKey (P3) | Encrypted same as AppKey | Re-derived on rejoin |

### 5.2 In environment

- All secrets read via `Settings` Pydantic class from env vars or `.env` (dev only).
- Production: secrets injected via Docker/K3s secrets, never baked into images.
- `.env` files **never committed**: `.gitignore` enforces; `gitleaks` pre-commit catches.

### 5.3 Secret naming

All env var names ending in any of: `_PASSWORD`, `_SECRET`, `_KEY`, `_TOKEN`, `_DSN` are treated as secret. Logger redacts these.

### 5.4 Rotation policies

| Secret | Rotation interval | Procedure |
|---|---|---|
| `JWT_SECRET` | 90 days | Dual-key support: previous and current. New tokens signed with current; both accepted for verification during rollover (24h). |
| `PASSWORD_PEPPER` | Manually, on incident only | Requires re-hashing on next login per user. |
| `LORA_KEY_KEK` | Manually, on incident only | Re-encrypt all rows. |
| TLS certificates | Auto (Caddy/Let's Encrypt, ~60d) | Caddy handles |
| Database passwords | Yearly | Documented procedure in [13_DEVOPS_RUNBOOK §5.3] |
| OAuth/LLM provider keys | Per provider | Stored in env, swap and restart |
| Internal HMAC for queue auth | Yearly | Dual-key support |

### 5.5 Customer secrets that are NEVER displayed twice

- MQTT password (shown only at provisioning/rotation)
- HTTP token (same)
- API key (same)
- LoRa AppKey

These are also never returned by GET endpoints. Only POST creation/rotation responses include them.

### 5.6 Secret in logs

Logger config (Python `structlog`) has a `redact_processor` that:
1. Recursively scans every log record's data.
2. Replaces values whose keys match secret patterns with `<redacted>`.
3. Patterns: `password*`, `*token*`, `*secret*`, `authorization`, `cookie`, `set-cookie`, `*key*` (excluding `*_id` and `*_key` literal column names that aren't sensitive — explicit allow-list overrides).

Webserver request logging excludes `Authorization` and `Cookie` headers.

---

## 6. Network and Transport Security

### 6.1 TLS

- **Minimum:** TLS 1.2. Recommended TLS 1.3.
- **Cipher suites:** Mozilla "intermediate" profile.
- **Cert source:** Let's Encrypt via Caddy automatic HTTPS in prod and staging. Local dev uses self-signed CA (mkcert) or HTTP for localhost only.
- **HSTS:** `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` after 30-day soak.
- **Perfect Forward Secrecy:** required (ECDHE).

### 6.2 HTTP security headers (set by Caddy)

```
Content-Security-Policy: default-src 'self';
  script-src 'self' 'wasm-unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob: https://tile.openstreetmap.org;
  connect-src 'self' wss://<host>;
  font-src 'self' data:;
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
  upgrade-insecure-requests
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-site
```

### 6.3 CORS

- API allows: `https://app.<host>`, `https://docs.<host>` only.
- `Access-Control-Allow-Credentials: true` only for cookie-bearing endpoints (web session).
- API key requests use `Authorization` header → no cookies → CORS less critical, still restrictive.

### 6.4 Service-to-service traffic

- **Inside cluster (K3s/Docker network):** plaintext acceptable in Phase 1; private network isolation provides transport trust.
- **Phase 3 with multi-node:** mTLS via Caddy or service mesh (Linkerd) for cross-node hops.
- **Postgres connections:** TLS required from app to DB when DB is on a separate machine (Tier A hosting).
- **Redis, NATS, MinIO:** auth required even on internal network. Passwords in env vars per service.

### 6.5 Outbound traffic restrictions

For webhooks (and any user-controlled URL):
- **Deny:** `localhost`, `127.0.0.0/8`, `0.0.0.0`, `169.254.0.0/16`, `100.64.0.0/10`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fd00::/8`.
- **Deny:** cloud metadata services: `169.254.169.254`, `metadata.google.internal`.
- **Resolve DNS once**, then use the resolved IP for the request — prevents DNS rebinding.
- **Time-out:** 10 s connect + 10 s read.
- **Max response body:** 1 MB (we ignore it anyway).

---

## 7. Input Validation and Output Encoding

### 7.1 Request validation

- All bodies validated against Pydantic v2 models in interface layer.
- Integer/float ranges declared (e.g., `limit: int = Field(ge=1, le=200)`).
- String lengths bounded.
- Unknown fields rejected: `model_config = ConfigDict(extra="forbid")`.

### 7.2 Telemetry payload validation

- Reserved keys ([04_GLOSSARY §9]) rejected.
- If device profile has a JSON Schema, payload validated against it.
- For numeric streams: NaN, Inf, -Inf rejected (`schema_mismatch`).
- For string streams: max length 1024 chars (configurable per profile).
- Total payload size: 256 KB hard limit per HTTP/MQTT message.

### 7.3 Output encoding

- All HTML rendered through React JSX (auto-escaped). Any `dangerouslySetInnerHTML` requires explicit review and uses `DOMPurify`.
- All JSON responses go through Pydantic serializers; no manual `json.dumps` of unsanitised input.
- File downloads served with `Content-Disposition: attachment; filename=...` and quoted filename to prevent header injection.

### 7.4 File uploads (avatars, dashboard backgrounds — Phase 2)

- Allowed types: `image/png`, `image/jpeg`, `image/webp`. Validated by both extension AND magic bytes (`python-magic`).
- Max size: 5 MB.
- Stored in MinIO under per-project prefix.
- Served via signed URL, never directly from app.
- Avatars resized server-side to fixed dimensions (strips EXIF including GPS).

---

## 8. Multi-Tenancy Isolation

### 8.1 Application-level (mandatory, all phases)

- Repository methods take `project_id` as first arg after self.
- Linter / architecture test: any `select`/`update`/`delete` on a tenant-scoped table without a `project_id` predicate fails CI.
- Integration test sweep: for every endpoint, attempt to access another tenant's resource and assert non-200.

### 8.2 Database-level (Phase 3)

- Postgres Row-Level Security:
  ```sql
  alter table devices enable row level security;
  create policy devices_isolation on devices
    using (project_id = current_setting('app.current_project_id')::text);
  ```
- Connection-pool wrapper sets `app.current_project_id` on every checkout.
- Disabled for internal admin connections (separate role).

### 8.3 Cache key isolation

- Every Redis key includes `project_id` segment: `series:<project_id>:<stream_id>:<bucket>:<from>:<to>`.
- Cache invalidation scoped to project.

### 8.4 NATS subject isolation

Subject pattern includes `project_id`: `telemetry.datapoint.v1.<project_id>`. Consumers in user-facing services subscribe with project filter.

### 8.5 Storage path isolation (MinIO)

Buckets per concern (`avatars`, `exports`, `device-backups`). Within bucket, prefix by `<project_id>/`.

---

## 9. Logging, Audit, and PII Handling

### 9.1 What gets logged

- Every API request: method, path, status, duration, user_id, project_id, ip, user_agent, request_id.
- Every state-changing action: audit event (separate from app log) → `audit_events` table + `audit.event.v1` NATS event.
- Errors with full stack trace + redacted context.
- Every authentication attempt success/failure with email_hash + ip.

### 9.2 What does NOT get logged

- Passwords, tokens, API keys, AppKeys, AppSKeys.
- Full payload bodies for telemetry by default (sampled in dev only).
- Email bodies, dashboard data.
- Authorization headers, cookies.

### 9.3 PII inventory

PII collected and stored:
- Email (always)
- Name (always)
- IP address (logs, audit, kept per retention)
- Timezone, locale (preferences)
- Billing info (Phase 5: stored by Stripe/Polar; we hold subscription_id only)

PII NOT collected: phone, address (until SMS in Phase 2), DOB, government IDs.

### 9.4 PII handling rules

- Never display in logs except hashed email when needed for diagnostics.
- Never share with third parties except billing processors.
- Subject access requests (GDPR, CCPA): documented endpoint `GET /v1/me/export` returns JSON of all user-owned data + `DELETE /v1/me` triggers full erasure (Phase 3 hard requirement).
- PII fields excluded from telemetry data exports.

### 9.5 Audit event integrity

- `audit_events` table is INSERT-only at the application level. No UPDATE/DELETE endpoints.
- Phase 3: append-only WAL archive of `audit_events` to MinIO (write-once).
- Phase 5: optional cryptographic chaining (each event includes hash of previous) for tamper-evidence.

### 9.6 Log retention

| Source | Retention |
|---|---|
| App logs (Loki) | 30 days |
| Audit events (Postgres) | per tier (see [04_GLOSSARY §7]) |
| Web server access logs (Caddy) | 14 days |
| Backup archives | 90 days off-site |

---

## 10. Dependency and Supply-Chain Security

### 10.1 Lockfiles

- Python: `uv.lock` committed, exact versions.
- Node: `pnpm-lock.yaml` committed.
- Docker base images: pinned by digest (`@sha256:...`) in production Dockerfiles.

### 10.2 Vulnerability scanning (CI)

- **Python:** `pip-audit` weekly + on PR.
- **Node:** `pnpm audit` weekly + on PR.
- **Docker images:** Trivy scan on every release tag.
- **Secrets in code:** `gitleaks` pre-commit + CI.
- **OSS license check:** `pip-licenses` and `license-checker` on PR; deny GPL-3 (incompatible w/ AGPL-3 platform), allow MIT/BSD/Apache/MPL/AGPL.

### 10.3 Critical CVE policy

- High/critical CVE in a dependency: triage within 24h, patch within 7 days (or document mitigating control).
- Subscribe to security advisories: GitHub, PyPI, npm.

### 10.4 Update cadence

- Patch updates: weekly automatic via Dependabot (auto-merge on green CI).
- Minor updates: weekly review.
- Major updates: quarterly planned upgrades.

### 10.5 SBOM

- Generated on every release: `cyclonedx-py` for Python, `cyclonedx-node-pnpm` for Node.
- Stored as build artifact; published with release.

---

## 11. Hardening Checklist (Per Service)

### 11.1 `api`, `ingest`, `worker`, `ai-worker`, `scheduler`

- [ ] Run as non-root user in container (`USER 10001`).
- [ ] Read-only root filesystem (`readOnlyRootFilesystem: true`); writable only `/tmp`.
- [ ] Drop all Linux capabilities; add only what's required.
- [ ] No host networking, no privileged.
- [ ] Resource limits set (CPU + memory + ephemeral storage).
- [ ] Health check endpoints (`/healthz`, `/readyz`) on internal port only.
- [ ] Metrics endpoint `/metrics` on internal port, IP-restricted.
- [ ] Image scan green at build time.
- [ ] `gunicorn` (api) limits: max-requests=1000, max-requests-jitter=50, timeout=30, workers=`(2 × cores) + 1`, worker class `uvicorn.workers.UvicornWorker`.

### 11.2 `web`

- [ ] Built with `next build`, runs `next start`.
- [ ] No source maps in production bundles (or hosted at non-public path).
- [ ] All API calls go through generated client; no raw `fetch`.
- [ ] Environment variables prefixed `NEXT_PUBLIC_` only for non-sensitive.

### 11.3 `realtime`

- [ ] Connection limit per user enforced.
- [ ] Per-connection memory cap.
- [ ] Auth re-checked on every subscription (cached 60 s).

### 11.4 `mqtt-broker` (EMQX)

- [ ] Anonymous auth disabled.
- [ ] Default user removed.
- [ ] Auth via HTTP webhook only.
- [ ] ACL via HTTP webhook.
- [ ] TLS enabled on external port.
- [ ] Connection rate limit: 100/sec/IP.
- [ ] Message rate limit: per-client default 100/sec, override via device profile.

### 11.5 `nats`

- [ ] JetStream enabled with auth.
- [ ] User/password per service: `api-user`, `ingest-user`, `worker-user`, etc.
- [ ] Permissions per user: subscribe-only or publish-only as appropriate.
- [ ] TLS for cross-node (Phase 3).

### 11.6 `postgres`

- [ ] Password auth (no trust auth).
- [ ] Listen only on private interface.
- [ ] `pg_hba.conf` restricts source IPs.
- [ ] Per-service user with minimal grants.
- [ ] `log_statement = 'ddl'` (logs schema changes).
- [ ] Backups encrypted at rest (pgBackRest with `repo1-cipher-type=aes-256-cbc`).

### 11.7 `redis`

- [ ] `requirepass` set.
- [ ] `protected-mode yes`.
- [ ] Listen private interface only.
- [ ] Disable dangerous commands: `rename-command FLUSHDB ""`, `FLUSHALL ""`, `KEYS ""`, `CONFIG ""`.

### 11.8 `minio`

- [ ] Per-bucket access keys.
- [ ] Bucket policies restrict cross-bucket access.
- [ ] Server-side encryption enabled.
- [ ] Public buckets explicitly marked; default deny.

### 11.9 `caddy`

- [ ] Run as non-root with capability `NET_BIND_SERVICE`.
- [ ] Admin API listens on `localhost` only.
- [ ] Logs to stdout; redact `Authorization` and `Cookie` request headers.
- [ ] Rate limits per IP for unauthenticated endpoints (login, signup, password reset).

### 11.10 Host/OS

- [ ] OS auto-updates security patches (`unattended-upgrades`).
- [ ] SSH key-only, no passwords. `PermitRootLogin no`.
- [ ] Firewall (`ufw`) default deny inbound; allow only 22, 80, 443, MQTT ports.
- [ ] Fail2ban for SSH.
- [ ] Process limits in `/etc/security/limits.conf`.
- [ ] No swap on DB host (or carefully sized + encrypted).

---

## 12. Vulnerability Disclosure and Incident Response

### 12.1 Disclosure policy

- Public `SECURITY.md` in the repo and `/security` page on the marketing site.
- Email: `security@<host>` and PGP key published.
- Response SLA: acknowledge in 48h, fix critical in 7 days, fix high in 30 days.
- Bug bounty: not offered in Phase 1; statement that reports are appreciated, will be credited if requested.

### 12.2 Incident response — runbook

When an incident is suspected:

1. **Triage (≤15 min):** confirm; classify severity (P0 = active exploit / data loss; P1 = high impact; P2 = limited; P3 = low).
2. **Contain:** revoke compromised credentials; if needed, take system offline (status page update).
3. **Eradicate:** patch root cause.
4. **Recover:** restore from clean state if needed; verify integrity.
5. **Post-mortem (within 7 days):** blameless write-up. Public summary for P0/P1 affecting users.

Specific procedures:

| Incident type | First action |
|---|---|
| Stolen JWT signing key | Rotate `JWT_SECRET`, dual-key decode 1h, then single. All sessions invalidated. |
| Stolen DB credentials | Rotate DB password, restart all services. Audit logs for queries since last known good. |
| Compromised user account | Force logout-all, force password reset, audit the account's actions. |
| Exposed API key | Revoke key. Audit usage. Notify user. |
| Compromised LLM provider response | No persistent damage possible (proposals are previewed); but disable provider, switch to backup. |
| Public S3/MinIO bucket leak | Make private, audit access logs, notify affected users if PII was in scope. |
| Production node compromised (e.g., SSH breach) | Take node out of rotation, snapshot for forensics, rebuild from immutable image. |

### 12.3 Notification

- For breaches involving PII: notify affected users by email within 72h (per GDPR).
- For service outages caused by incidents: status page update within 30 min of confirmation.
- Founder is on-call for incidents Phase 1; rotation in Phase 5.

### 12.4 Backup integrity

- Backups verified by automated weekly restore-to-staging test.
- Backup encryption keys held separately from backup storage.
- Restore drill runbook in [13_DEVOPS_RUNBOOK §6.4].
