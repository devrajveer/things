# Product Requirements Document (PRD)

What gets built, in what order, and what "done" means for each piece. **Phase 1 (MVP) is fully specified. Phase 2+ is outlined.**

> Definitions and IDs from [04_GLOSSARY]. API/DB/event contracts in [07_DATA_CONTRACTS]. UI in [08_UI_UX_SPEC].

---

## How to read this document

Each feature has:
- **F-XXX**: a stable feature ID
- **User story**: who/what/why
- **Acceptance criteria**: testable bullets, each numbered
- **Out of scope**: explicit non-goals
- **Dependencies**: other features required first
- **Phase**: which phase it ships in

An AI agent should treat acceptance criteria as the test specification. If a criterion is ambiguous, surface the ambiguity rather than guess.

---

## Table of contents

- §1 Personas
- §2 Non-functional requirements (performance, scale, accessibility)
- §3 Phase 1 — MVP features (F-100 to F-199)
- §4 Phase 2 — AI Differentiation features (F-200 to F-299)
- §5 Phase 3 — LoRaWAN & Multi-tenant features (F-300 to F-399)
- §6 Phase 4 — Edge & Advanced features (F-400 to F-499)
- §7 Phase 5 — Monetization features (F-500 to F-599)

---

## 1. Personas

### P1 — Hobbyist Hero
Solo maker, ESP32 builder, weekend projects. Wants free, fast, OSS, hates complexity.
Success: ESP32 to live chart in <10 minutes.

### P2 — Indie Hardware Founder
1–10 person startup shipping consumer IoT. Wants reliability, scalability, predictable pricing, room to grow.
Success: Self-hosts MVP, migrates to cloud when scale demands.

### P3 — Industrial Monitoring Consultant
Sets up monitoring for SMB factories. Wants LoRaWAN, anomaly detection, white-label.
Success: Onboards a 100-sensor cold-storage client in a weekend.

### P4 — AgriTech Co-op Tech Lead
Manages a network of LoRa moisture sensors across farms. Wants gateway monitoring, codec library, low complexity.
Success: Replaces TTN+homemade-dashboard stack with one platform.

### P5 — Platform Admin
You. Operates the cloud, supports users, monitors health.
Success: Diagnoses any incident in <15 min from Grafana.

---

## 2. Non-Functional Requirements

These apply to every feature unless explicitly waived.

### NFR-1 Performance budgets

| Operation | Target (p95) | Hard ceiling (p99) |
|---|---|---|
| Page load (TTI, dashboard with 5 widgets) | 2.0 s | 4.0 s |
| API GET (list, 50 items) | 200 ms | 500 ms |
| API POST (create resource) | 300 ms | 800 ms |
| Telemetry ingest → DB write | 1.5 s | 3.0 s |
| Telemetry ingest → WebSocket fan-out | 500 ms | 1.5 s |
| Rule evaluation latency (per datapoint) | 50 ms | 200 ms |
| Alert delivery (email) | 10 s | 60 s |
| Alert delivery (webhook) | 5 s | 30 s |
| AI dashboard generation (P2) | 8 s | 30 s |
| AI insight chat token-time-to-first-token (P2) | 2 s | 8 s |

### NFR-2 Scale targets (per region, by phase)

| Metric | Phase 1 (MVP) | Phase 3 (post-LoRa) | Phase 5 |
|---|---|---|---|
| Concurrent MQTT connections | 5,000 | 50,000 | 500,000 |
| Telemetry msgs/sec sustained | 500 | 5,000 | 50,000 |
| Concurrent WebSocket clients | 1,000 | 10,000 | 100,000 |
| Active projects | 1,000 | 10,000 | 100,000 |
| API req/sec sustained | 200 | 2,000 | 20,000 |

### NFR-3 Availability

- Phase 1: best-effort, no SLA. Target 99.0% (~7h downtime/month).
- Phase 3: 99.5% (~3.5h/month).
- Phase 5: 99.9% (~45min/month).
- Status page on independent infra.

### NFR-4 Data durability

- Telemetry: nightly full backups + continuous WAL archiving from Phase 1. RPO < 5 minutes.
- All other data: same.
- Restore drill: monthly from Phase 3.

### NFR-5 Browser support

- Last 2 versions of Chrome, Firefox, Safari, Edge.
- No IE.
- Mobile Safari + Chrome on Android — responsive but not feature-parity.

### NFR-6 Accessibility

- WCAG 2.1 AA target by Phase 3.
- Keyboard navigation works on all interactive elements from Phase 1.
- Color contrast ≥ 4.5:1 for text from Phase 1.
- All form fields have labels.
- All images have alt text.

### NFR-7 Internationalization

- English-only Phase 1.
- All user-visible strings via i18n keys from Phase 2 (prepare in Phase 1, no translations yet).
- Time zone-aware display (user picks tz in profile).
- Number formatting locale-aware (uses browser locale).

### NFR-8 Self-hosting

- Single-command bring-up: `docker compose up` works on a fresh Linux box (Ubuntu 22.04+, 8 GB RAM).
- All services healthy in <2 minutes.
- No external dependency required to be functional (LLM is optional).
- Documented at [13_DEVOPS_RUNBOOK §3].

---

## 3. Phase 1 — MVP Features

Goal: a developer can take an ESP32 from box to live chart in under 10 minutes following the quickstart.

### Bounded contexts in scope
- Identity (users, sessions)
- Projects (single-user only in MVP)
- Devices (registry + credentials)
- Ingest (HTTP + MQTT)
- Telemetry (storage, query)
- Dashboards (5 widget types)
- Rules (threshold-only)
- Alerts (email + webhook)
- SDKs (Python, JS, Arduino)
- CLI

### Explicitly out of scope (Phase 1)
- Organizations, teams, multi-user projects (Phase 3)
- LoRaWAN (Phase 3)
- AI features (Phase 2)
- Mobile app (Phase 4)
- Marketplace / templates (Phase 5)
- Custom domains (Phase 3)
- Billing (Phase 5)
- Audit log (basic only — full search Phase 3)
- 2FA (Phase 2)
- SSO (Phase 4)

---

### F-100: Sign Up

**User story:** As P1/P2, I want to create an account so that I can use the platform.

**Acceptance criteria:**
1. `POST /v1/auth/signup` accepts `{email, password, name}`.
2. Email validated against RFC 5322; rejected with `validation_failed` if malformed.
3. Password minimum 12 characters, must contain at least 3 of: lowercase, uppercase, digit, symbol. Common passwords (top 100k list) rejected.
4. Password hashed with Argon2id (memory=64MB, iterations=3, parallelism=4).
5. Email uniqueness enforced; duplicate returns `already_exists` (409).
6. On signup: a default `Organization` (tier=`free`) is created, the user is its owner, and a default `Project` named "My Project" is created in it.
7. A verification email is sent via Postal containing a magic link valid for 1 hour.
8. User is logged in immediately (returns access + refresh tokens) but `email_verified` is false until they click the link.
9. Until email verified, certain actions are blocked (sending invites, upgrading tier). Telemetry ingestion still works.
10. UI: signup page at `/signup`, redirects to `/projects/<id>` on success.
11. Audit event `member.invited` (with kind=self) recorded.

**Dependencies:** none.

---

### F-101: Email Verification

**User story:** Confirm email ownership.

**Acceptance criteria:**
1. Verification link format: `https://<host>/verify-email?token=<token>`.
2. Token is single-use, opaque, 32 bytes URL-safe base64.
3. On click: marks `users.email_verified_at = now()`, redirects to `/projects/<id>?verified=1`.
4. Expired or already-used token shows error page with "Resend verification" button.
5. Resend: rate-limited to once per 60 seconds per email.

---

### F-102: Login (Email + Password)

**User story:** Existing user signs in.

**Acceptance criteria:**
1. `POST /v1/auth/login` with `{email, password}`.
2. Returns `{access_token, refresh_token, expires_in, user}` on success.
3. Access token is JWT, signed HS256, 15 min lifetime.
4. Refresh token is opaque, 64 bytes base64, persisted hashed in `refresh_tokens` table, 30 day lifetime, single-use (rotated on each refresh).
5. Failed login: returns `invalid_credentials`, 401. Same response time as success (constant-time check) to prevent enumeration.
6. After 5 failed attempts in 10 minutes for the same email: account locked for 15 min, returns `rate_limited`. User notified by email.
7. UI: login page at `/login`. Includes "Forgot password" link.
8. On successful login: audit event `user.logged_in`.

---

### F-103: Magic Link Login

**User story:** Passwordless login.

**Acceptance criteria:**
1. `POST /v1/auth/magic-link` with `{email}`.
2. Always returns 200 (no email enumeration). Sends email if account exists.
3. Email contains link `https://<host>/auth/magic?token=<token>`, valid 15 min, single-use.
4. Click → returns same token pair as password login.
5. UI: option on `/login` page.

---

### F-104: Password Reset

**User story:** Forgotten password.

**Acceptance criteria:**
1. `POST /v1/auth/password-reset/request` with `{email}`. Always returns 200.
2. Email with reset link `https://<host>/auth/reset?token=<token>`, valid 1 hour, single-use.
3. Reset page form: new password (with same complexity rules as F-100) + confirm.
4. `POST /v1/auth/password-reset/confirm` with `{token, new_password}`.
5. On success: invalidates all existing refresh tokens, sends "password changed" notification email.
6. UI: `/forgot-password` page accessible from `/login`.

---

### F-105: Token Refresh

**Acceptance criteria:**
1. `POST /v1/auth/refresh` with `{refresh_token}`.
2. Returns new `{access_token, refresh_token, expires_in}`.
3. Old refresh token invalidated immediately.
4. If presented refresh token is already used (replay attack): all tokens for that user invalidated, audit event recorded, user emailed.

---

### F-106: Logout

**Acceptance criteria:**
1. `POST /v1/auth/logout` with current refresh token.
2. Refresh token invalidated. Access token expires naturally.
3. UI: clears local storage, redirects to `/`.
4. Optionally: `POST /v1/auth/logout-all` invalidates all refresh tokens for user.

---

### F-110: User Profile

**Acceptance criteria:**
1. `GET /v1/me` → user details (id, email, name, email_verified, created_at, timezone).
2. `PATCH /v1/me` accepts `{name?, timezone?}`. Email change requires re-verification (separate endpoint).
3. `POST /v1/me/email-change` with `{new_email}` → sends confirmation to new email.
4. UI: settings page `/settings/profile`.

---

### F-120: Project — View Default

**Note:** In Phase 1, each user has exactly one organization with one default project. UI for creating additional projects is hidden behind a feature flag.

**Acceptance criteria:**
1. After login, user lands on `/projects/<default_project_id>` overview.
2. Project overview shows: device count, datapoints last 24h, recent alerts, quick action buttons.
3. `GET /v1/projects/{id}` returns project metadata.

---

### F-130: Device — Create

**User story:** Register a new device, get credentials.

**Acceptance criteria:**
1. `POST /v1/projects/{id}/devices` with body `{name, profile_id?, labels?, description?}`.
2. `name` required, 1-64 chars, unique within project (case-insensitive).
3. `profile_id` optional. If absent, uses a "default JSON" profile.
4. Returns the created device + a one-time-display object containing:
   - `device_id`
   - `mqtt_username`
   - `mqtt_password` (random 32 bytes URL-safe, shown only here)
   - `http_token` (random 32 bytes URL-safe, shown only here)
   - `mqtt_topics` object with `up`, `down`, `state`, `event`, `ack`
   - `http_endpoint` URL
5. Credentials are hashed (argon2id) before persistence; never retrievable in plaintext after this response.
6. Quota check: returns `quota_exceeded` if device limit hit for tier.
7. UI: "Add Device" button on devices page → modal with form. After submit, shows credentials in a copy-friendly format with a clear "save this now, it won't be shown again" warning. Generates code snippets for each SDK with the credentials filled in.
8. Audit event `device.created`.

---

### F-131: Device — List

**Acceptance criteria:**
1. `GET /v1/projects/{id}/devices` with query `?status=&label=&search=&limit=&cursor=`.
2. Returns paginated list with: id, name, status, last_seen_at, profile_id, labels, datapoint count (last 24h).
3. Sortable: `?sort=name|created_at|last_seen_at`, default `last_seen_at desc`.
4. UI: table view at `/devices`. Filters: status dropdown, label search, free-text search.

---

### F-132: Device — Detail

**Acceptance criteria:**
1. `GET /v1/projects/{id}/devices/{device_id}`.
2. Returns full device + list of streams (key, value_type, last_value, last_value_at).
3. UI: page `/devices/<id>` with tabs: Overview, Streams, Settings, Recent Activity.

---

### F-133: Device — Update

**Acceptance criteria:**
1. `PATCH /v1/projects/{id}/devices/{device_id}` accepts `{name?, profile_id?, labels?, description?}`.
2. UI: editable on settings tab.
3. Audit event `device.updated`.

---

### F-134: Device — Disable / Enable

**Acceptance criteria:**
1. `POST /v1/projects/{id}/devices/{device_id}/disable` and `/enable`.
2. Disabled device: ingestion rejected with `device_disabled`. MQTT broker disconnects existing session within 30 s.
3. Status transitions per [04_GLOSSARY §10].
4. UI: toggle in device settings. Confirmation modal explains effect.
5. Audit events `device.disabled`, `device.enabled`.

---

### F-135: Device — Rotate Credentials

**Acceptance criteria:**
1. `POST /v1/projects/{id}/devices/{device_id}/credentials/rotate`.
2. Returns new credentials (one-time display), invalidates old ones immediately.
3. UI: button in device settings, requires text confirmation ("ROTATE").
4. Audit event `device.token_rotated`.

---

### F-136: Device — Delete

**Acceptance criteria:**
1. `DELETE /v1/projects/{id}/devices/{device_id}` → soft delete (`status='deleted'`).
2. Telemetry retained per project retention policy.
3. Hard delete possible after 30 days (not exposed in MVP UI).
4. UI: button in device settings, requires text confirmation (typing device name).
5. Audit event `device.deleted`.

---

### F-140: Telemetry Ingest — HTTP

**Acceptance criteria:**
1. `POST /v1/ingest` with `Authorization: Bearer <http_token>` and JSON body.
2. Body shapes accepted:
   - Single value: `{"key": "temperature", "value": 23.5, "ts"?: "2025-01-15T10:30:00Z"}`
   - Multi-key: `{"values": {"temperature": 23.5, "humidity": 58}, "ts"?: "..."}`
   - Array of multi-key: `{"batch": [{"values": {...}, "ts": "..."}, ...]}` — max 100 items per request.
3. `ts` optional; if absent, server uses now().
4. Schema validation: each value must conform to device profile schema (if profile defined).
5. Reserved keys ([04_GLOSSARY §9]) rejected with `validation_failed`.
6. Returns 202 Accepted with `{accepted: <count>, request_id: "..."}` on success.
7. Returns 4xx with error details if validation failed (no partial accept; whole request rejected).
8. Quota check: `quota_exceeded` if monthly message limit reached.
9. Rate limit: per device, configurable, default 10 msg/s.
10. Datapoint persisted to NATS within 50 ms of HTTP response.

---

### F-141: Telemetry Ingest — MQTT

**Acceptance criteria:**
1. EMQX broker accepts MQTT 3.1.1 and 5.0 connections on ports 1883 (plain), 8883 (TLS), 8083/8084 (WS/WSS).
2. Authentication: HTTP webhook to `api` service `/internal/mqtt/auth` on every connection, cached 5 min.
3. ACL: device can publish only to its own `up`, `state`, `event`, `ack` topics. Subscribe only to its own `down` topic.
4. Payload format: JSON by default; CBOR and CayenneLPP supported via device profile.
5. QoS 0 and 1 supported. QoS 2 supported but discouraged (perf).
6. Retain flag: respected on `state` topic only.
7. Will message: optional, used to flag offline status.
8. Same validation rules as HTTP ingest.
9. Ingestion latency p95 < 1.5 s from publish to NATS.

---

### F-142: Stream Auto-Discovery

**Acceptance criteria:**
1. First time a `(device_id, key)` is seen, a `Stream` row is created.
2. Stream attributes inferred: `value_type` from first value, `unit` blank (user can set later), `display_name` = key.
3. Subsequent datapoints update `last_value` and `last_value_at` on the stream row.
4. Type mismatch (e.g., string sent to a number stream) → datapoint rejected with `schema_mismatch`. Log event for user visibility.
5. UI: streams list under device detail; user can edit `display_name`, `unit`, `value_type` (with warning if changing).

---

### F-143: Telemetry Query — Series

**Acceptance criteria:**
1. `GET /v1/projects/{id}/streams/{stream_id}/series` with query:
   - `from` (ISO-8601, required)
   - `to` (ISO-8601, default now)
   - `agg` (one of: `avg`, `min`, `max`, `sum`, `count`, `last`; default `avg`)
   - `bucket` (ISO-8601 duration, optional; if absent, server picks based on range)
   - `limit` (max 10,000 points, default 1,000)
2. Server picks the smallest continuous aggregate satisfying requested bucket (e.g., `bucket=PT1M` uses `telemetry_1m`, `PT1H` uses `telemetry_1h`).
3. Returns `{stream_id, bucket, agg, points: [{t, v}, ...]}`.
4. Time range > retention is allowed but returns empty for excluded portions.
5. Response cached in Redis (10 s TTL) keyed on full query.
6. Authorization: requester must have access to project.

---

### F-144: Telemetry Query — Latest

**Acceptance criteria:**
1. `GET /v1/projects/{id}/devices/{device_id}/latest` returns latest value per stream for the device.
2. `GET /v1/projects/{id}/streams/{stream_id}/latest` for a single stream.
3. Cached aggressively (1 s TTL).

---

### F-145: Live Telemetry — WebSocket

**User story:** Dashboards update in real time as new data arrives.

**Acceptance criteria:**
1. Endpoint: `wss://<host>/v1/realtime` with auth via `?token=<access_token>` query param.
2. After connect, client sends subscribe message:
   ```json
   {"type": "subscribe", "id": "sub_xxx", "filter": {"project_id": "prj_...", "stream_ids": ["str_...", ...]}}
   ```
3. Server pushes events:
   ```json
   {"type": "datapoint", "subscription_id": "sub_xxx", "stream_id": "str_...", "t": "2025-01-15T10:30:00.123Z", "v": 23.5}
   ```
4. Multiple subscriptions per connection allowed.
5. `unsubscribe` message removes a subscription.
6. Heartbeat: server sends `{"type":"ping"}` every 30 s; client echoes `{"type":"pong"}`.
7. Authorization re-checked at subscription time; cached on connection.
8. Backpressure: if client buffer full > 1 s, drop oldest datapoints, send `{"type": "warning", "code": "backpressure_drop"}`.
9. Connection limit per user: 10 concurrent (configurable).

---

### F-150: Dashboards — Create

**Acceptance criteria:**
1. `POST /v1/projects/{id}/dashboards` with `{name, description?}`.
2. Returns dashboard with empty layout.
3. UI: "New Dashboard" button → modal → redirects to dashboard editor.
4. Quota check.
5. Audit event `dashboard.created`.

---

### F-151: Dashboards — List

**Acceptance criteria:**
1. `GET /v1/projects/{id}/dashboards` returns list with name, description, widget_count, updated_at.
2. UI: dashboards page with grid of cards.

---

### F-152: Dashboards — Edit Layout

**Acceptance criteria:**
1. Dashboard editor allows: add widget, remove widget, drag to reorder, resize widget.
2. Layout grid: 12 columns wide, rows auto-flow. Each widget has `{x, y, w, h}`.
3. `PUT /v1/projects/{id}/dashboards/{dashboard_id}/layout` saves the full layout JSON.
4. Auto-save: debounced 1 s after last change.
5. Undo: client-side, last 20 edits.

---

### F-153: Dashboard Widget — Line Chart

**Acceptance criteria:**
1. Configurable: streams (1-N), time range (relative or absolute), aggregation, bucket, show legend, y-axis min/max/auto.
2. Renders with Apache ECharts.
3. Live updates from F-145 — appends new points without re-fetching history.
4. Hover tooltip shows time + values.
5. Time range presets: Last 15m, 1h, 6h, 24h, 7d, 30d, custom.
6. Empty state when no data.

### F-154: Dashboard Widget — Gauge
1. Configurable: stream (1), min, max, thresholds (color zones).
2. Shows latest value with needle.
3. Updates live.

### F-155: Dashboard Widget — Single Value
1. Configurable: stream, label, unit, decimal places, color thresholds.
2. Shows latest value, optionally with sparkline of last hour.

### F-156: Dashboard Widget — Table
1. Configurable: streams (multi), columns to show, page size.
2. Each row = one datapoint.
3. Sortable by time.

### F-157: Dashboard Widget — Map
1. Configurable: stream of type `location` or two streams (lat, lng).
2. Shows latest position(s) on MapLibre + OpenStreetMap.
3. Optional: trail showing last N positions.

---

### F-160: Rules — Create (Threshold)

**User story:** Get alerted when a sensor crosses a value.

**Acceptance criteria:**
1. `POST /v1/projects/{id}/rules` with body conforming to rule schema ([07_DATA_CONTRACTS §4]).
2. MVP supports only `trigger.type = "threshold"`.
3. Schema:
   ```json
   {
     "name": "Cold storage breach",
     "scope": {"device_ids": ["dev_..."], "stream_keys": ["temperature"]},
     "trigger": {
       "type": "threshold",
       "comparator": ">",     // one of >, >=, <, <=, ==, !=
       "value": -15.0,
       "window_s": 600,        // 0 = single datapoint
       "aggregation": "all"     // all | any | avg
     },
     "actions": [
       {"type": "email", "to": "ops@example.com"},
       {"type": "webhook", "url": "https://...", "secret": "..."}
     ],
     "debounce_s": 1800,
     "enabled": true
   }
   ```
4. Validates: device_ids exist in project, scope.stream_keys non-empty, value numeric for threshold, debounce ≥ 60 s.
5. UI: rule builder form with field-by-field guidance and a live preview pane showing recent matching datapoints.
6. Quota check.
7. Audit event `rule.created`.

---

### F-161: Rules — List, Detail, Update, Delete, Enable/Disable

Standard CRUD endpoints. Each generates corresponding audit events.

---

### F-162: Rule Engine — Evaluation

**Acceptance criteria:**
1. The `worker` service has a `rule-engine` consumer subscribed to `telemetry.datapoint.v1.>`.
2. For each incoming datapoint, finds rules whose scope matches.
3. Applies trigger: for `window_s = 0`, evaluates against single datapoint. Otherwise: queries history within window from cache (Redis) or DB.
4. If condition met, checks debounce (last fired time per rule). If not debounced, fires.
5. Firing publishes `alerts.fired.v1.<project>` event.
6. Latency target: 50ms p95 from datapoint receipt to alert fired.
7. Rule changes (enable/disable/edit) reflected within 5 seconds (cache TTL).

---

### F-163: Alert — Notification Email

**Acceptance criteria:**
1. Worker subscribes to `alerts.fired.v1.>`.
2. For each `email` action, sends via Postal SMTP relay.
3. Email contains: rule name, fired time, triggering values, link to alert detail page, link to "snooze" (one-click).
4. Delivery state tracked in `alert_deliveries` table.
5. Retries: 3 attempts with exponential backoff (1m, 5m, 15m). After 3 failures, marked `abandoned`.

---

### F-164: Alert — Notification Webhook

**Acceptance criteria:**
1. POST to user-provided URL with body conforming to webhook payload schema.
2. Headers include:
   - `User-Agent: yourplatform-webhook/1.0`
   - `X-YP-Event: alert.fired`
   - `X-YP-Delivery: <delivery_id>`
   - `X-YP-Signature: <hmac_sha256_hex>` (signed with `secret` from rule action)
   - `Content-Type: application/json`
3. Timeout: 10 s.
4. Retries same as email (3 attempts).
5. Webhook URL validation: must be https (http allowed only for localhost in dev), no link-local, no metadata IPs (169.254.0.0/16, 100.64.0.0/10), no AWS/GCP/Azure metadata service hostnames.

---

### F-165: Alert — List, Detail, Acknowledge, Resolve, Snooze

**Acceptance criteria:**
1. `GET /v1/projects/{id}/alerts` with filters: state, rule_id, from, to.
2. `GET /v1/projects/{id}/alerts/{alert_id}` returns full detail including triggering datapoints.
3. `POST /v1/projects/{id}/alerts/{alert_id}/acknowledge` → state → `acknowledged`.
4. `POST /v1/projects/{id}/alerts/{alert_id}/resolve` → state → `resolved`.
5. `POST /v1/projects/{id}/alerts/{alert_id}/snooze` with `{duration_s}` → state → `snoozed`. After duration, returns to `firing` if condition still true.
6. UI: alerts page at `/alerts` with table + detail drawer.

---

### F-170: API Keys — Create

**Acceptance criteria:**
1. `POST /v1/projects/{id}/api-keys` with `{name, scopes}` where scopes are from [04_GLOSSARY §3].
2. Returns the key once: `{id, key, name, scopes, expires_at}`.
3. Key format: `yp_<env>_<32_random_chars>` (e.g., `yp_live_AbCdEf123...`).
4. Key hashed (argon2id) before storage.
5. UI: settings page lists keys (showing only first 8 chars + last 4); revoke button per row.

### F-171: API Keys — List, Revoke
Standard. Revoking invalidates immediately (cache TTL 60 s).

---

### F-180: SDK — Python

**Acceptance criteria:**
1. Package name on PyPI: `yourplatform`.
2. Public API per [12_CLIENT_INTERFACES_SPEC §2].
3. Supports both HTTP and MQTT transports.
4. Quickstart works copy-paste:
   ```python
   from yourplatform import Client
   client = Client(token="...")
   client.publish({"temperature": 23.5})
   ```
5. Examples folder with: basic publish, batched publish, subscribe to commands, MQTT, HTTP.
6. Installable via `pip install yourplatform`.
7. Type-hinted, mypy-clean.

### F-181: SDK — JavaScript / Node
Per [12_CLIENT_INTERFACES_SPEC §3]. Browser + Node compatible. ESM + CJS.

### F-182: SDK — Arduino
Per [12_CLIENT_INTERFACES_SPEC §4]. ESP32, ESP8266, RP2040.

### F-183: CLI
Per [12_CLIENT_INTERFACES_SPEC §5].

---

### F-190: Documentation Site

**Acceptance criteria:**
1. Public site at `https://docs.<host>`.
2. Sections: Introduction, Quickstarts (per language), Concepts, Guides, API Reference, SDK Reference, Self-hosting.
3. API Reference auto-generated from OpenAPI spec at build time.
4. Search functional (Pagefind or Meilisearch).
5. Code examples runnable / copy-paste-able.
6. Dark mode default.
7. Mobile-responsive.

---

### F-191: Marketing Site
**Acceptance criteria:**
1. Pages: Home, Features, Pricing, Blog, Self-host, About.
2. Sign-up CTA above the fold.
3. Lighthouse score ≥ 95 on all categories.

---

### F-195: Self-Host Quickstart
1. `docker compose -f docker-compose.prod.yml up` brings up complete platform.
2. First-run wizard at port 80 walks through admin user creation, SMTP config, branding.
3. Single binary alternative documented but not built in MVP.
4. Documented at [13_DEVOPS_RUNBOOK §3].

---

### F-198: Audit Log (Basic)

**Acceptance criteria:**
1. Every state-changing action recorded in `audit_events` table.
2. UI: `/settings/audit` shows last 100 events for the user's projects.
3. Filterable by action, actor, date.
4. Search/export — Phase 3.

---

### F-199: Onboarding Tour

**Acceptance criteria:**
1. After first login, guided tour: Add Device → see credentials → connect from quickstart → see first data → create dashboard widget → set up alert.
2. Skippable. Re-runnable from settings.
3. Progress saved per user.

---

## 4. Phase 2 — AI Differentiation Features (Outline)

Goal: ship the wedge — make this the AI-native platform.

### F-200: Natural-Language Dashboard Builder
- LangGraph agent generates a dashboard JSON spec from a user prompt.
- Tools: `list_devices`, `list_streams`, `get_sample_data`, `propose_widget`.
- Always preview, never auto-apply.
- Streaming UI shows agent's tool calls + reasoning + preview.

### F-201: AI-Generated Rules
- Same pattern as F-200 but for rule JSON specs.
- "Explain in English" reverse mode for existing rules.

### F-202: Anomaly Detection per Stream
- For streams with > 1000 datapoints: train River HoeffdingAdaptive online + nightly Prophet forecast model.
- Anomaly score is a derived stream, suffix `_anomaly`.
- Rule trigger type `anomaly` becomes available.

### F-203: Insight Console (Chat with Data)
- Conversation pane on every project with "Insight Console".
- Tools: `query_series`, `recent_alerts`, `device_metadata`, `summarize_period`.
- RAG over: device descriptions, recent alerts, user notes.

### F-204: Embedding-Based Device Search
- Index device names + descriptions + tags + recent values into pgvector.
- Search bar with semantic search ("sensors near loading dock").

### F-205: Bring-Your-Own LLM Key
- Settings page to provide OpenRouter / OpenAI / Anthropic / local Ollama URL key.
- Self-hosters can run with no AI (graceful degrade).

### F-210: 2FA (TOTP)
- `pyotp` integration. QR code setup. Backup codes.
- Required for `admin` API keys.

### F-220: Audit Log — Search & Export
- Indexed in Meilisearch. Full-text search. CSV export.

### F-230: Bar Chart, Heatmap, Status Indicator widgets

---

## 5. Phase 3 — LoRaWAN & Multi-tenant Features (Outline)

### F-300: ChirpStack Integration
- ChirpStack runs as embedded service.
- Admin API proxied behind platform auth.

### F-301: LoRa Device Registration
- UI to add LoRa device by DevEUI/AppEUI/AppKey.
- Auto-creates ChirpStack-side records.

### F-302: LoRa Gateway Monitoring
- Auto-discovered when packets arrive.
- Status page: last seen, RSSI heatmap, connected devices.

### F-303: Codec Library
- Curated decoders for top 30 LoRa device models.
- User-editable JS codecs.

### F-304: Downlink Scheduler
- Queue + conflict resolution for confirmed downlinks.

### F-305: ADR Tuning UI
- Visualise device data rate over time, suggest changes.

### F-310: Organizations + Teams
- Promote single-user model to org-with-members.
- Role-based access control with `owner`, `admin`, `editor`, `viewer`.
- Invite by email.

### F-311: Public Dashboards
- Read-only sharable URL with optional password.

### F-312: Postgres Row-Level Security
- Defense-in-depth over application authz.

### F-313: Custom Domains
- Bring-your-own domain with auto SSL via Caddy.

### F-320: Audit Log — Export & API

---

## 6. Phase 4 — Edge & Advanced (Outline)

### F-400: Edge Agent
- Go binary for Raspberry Pi-class.
- Buffers offline.
- Local rule eval.
- ONNX inference.
- OTA firmware management.

### F-401: Digital Twin Builder
- Floor-plan canvas; bind sensors to positions.

### F-402: Webhook Integration Marketplace
- Templates for Slack, Discord, Telegram, PagerDuty, Home Assistant, Node-RED.

### F-403: PWA Mobile App

---

## 7. Phase 5 — Monetization (Outline)

### F-500: Billing Integration (Polar.sh + Stripe)
### F-501: Usage Metering (Lago)
### F-502: Template Gallery (community)
### F-503: White-label
### F-504: WebAuthn / Passkeys
### F-505: SSO (OIDC, SAML)

---

## 8. Feature Dependency Graph (Phase 1)

```
F-100 Signup
  └─▶ F-101 Email verify
  └─▶ F-102 Login
        ├─▶ F-105 Refresh
        └─▶ F-106 Logout
  └─▶ F-103 Magic link
  └─▶ F-104 Password reset
  └─▶ F-110 Profile
  └─▶ F-120 Default project
        ├─▶ F-130 Device create
        │     ├─▶ F-131 List
        │     ├─▶ F-132 Detail
        │     ├─▶ F-133 Update
        │     ├─▶ F-134 Disable/enable
        │     ├─▶ F-135 Rotate creds
        │     └─▶ F-136 Delete
        ├─▶ F-140 HTTP ingest ──┐
        ├─▶ F-141 MQTT ingest ──┤
        │                        └─▶ F-142 Stream auto-discovery
        │                              ├─▶ F-143 Series query
        │                              ├─▶ F-144 Latest query
        │                              └─▶ F-145 WebSocket live
        │                                    └─▶ F-150..F-157 Dashboards
        │                              └─▶ F-160..F-165 Rules + alerts
        └─▶ F-170, F-171 API keys
        └─▶ F-198 Audit log

F-180..F-183 SDKs/CLI (parallel)
F-190 Docs (parallel)
F-191 Marketing (parallel)
F-195 Self-host (after core)
F-199 Onboarding tour (last)
```
