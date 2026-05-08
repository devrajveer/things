# Data Contracts

The complete contract between systems. Every API endpoint, every database table, every event message. **Agents writing code must implement exactly what's specified here.**

> Conventions: [04_GLOSSARY] for naming, IDs, enums. [05_CODING_STANDARDS §8] for SQL style.

---

## Table of contents

- §1 HTTP API — Conventions
- §2 HTTP API — Phase 1 Endpoints
- §3 NATS Event Catalog
- §4 Rule Specification
- §5 Database Schema (DDL)
- §6 Time-series Tables and Aggregates
- §7 Webhook Payload Specification
- §8 MQTT Topic & Payload Specification

---

## 1. HTTP API — Conventions

### Base URL
```
https://api.<domain>/v1/...
```

### Auth methods
- **JWT Bearer** for user-driven calls: `Authorization: Bearer <access_token>`
- **API key** for programmatic calls: `Authorization: Bearer yp_<env>_<chars>`
- **Device token** for ingest only: `Authorization: Bearer <http_token>` on `/v1/ingest`

### Request envelope
- All bodies: `Content-Type: application/json`
- Body fields: snake_case
- Timestamps: ISO-8601 UTC with `Z` suffix
- Optional fields explicitly nullable

### Response envelope (success)
```json
{
  "data": { /* object or array */ },
  "meta": {
    "request_id": "req_01H...",
    "page"?: { "cursor"?: "...", "next_cursor"?: "...", "has_more": false, "limit": 50 }
  }
}
```

### Response envelope (error)
```json
{
  "error": {
    "code": "validation_failed",
    "message": "Human-readable summary",
    "details"?: { "field_name": ["specific issue"] },
    "request_id": "req_01H..."
  }
}
```

### Standard headers (response)
- `X-Request-Id: req_...`
- `X-RateLimit-Limit: 1000`
- `X-RateLimit-Remaining: 999`
- `X-RateLimit-Reset: 1736932200`
- `Deprecation: true` (when applicable)
- `Sunset: Wed, 01 Jan 2026 00:00:00 GMT` (when applicable)

### Pagination
Cursor-based only. Send `?cursor=<opaque>&limit=<n>`. Response includes next cursor in `meta.page.next_cursor`. Max `limit`: 200, default 50.

### Idempotency
Mutating endpoints accept `Idempotency-Key: <client-generated-uuid>`. Server stores result for 24 h; same key with same body returns the original response.

### Common HTTP status usage

| Status | When |
|---|---|
| 200 | GET success, PUT/PATCH success |
| 201 | POST creating a resource (returns the resource) |
| 202 | POST accepted but async (e.g., ingest) |
| 204 | DELETE success |
| 400 | Malformed request (rare; usually 422) |
| 401 | Unauthenticated |
| 402 | Payment required (quota or subscription) |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 422 | Validation failed |
| 423 | Resource locked (e.g., disabled device) |
| 429 | Rate limited |
| 500 | Internal error |
| 502 | Upstream dependency failure |
| 503 | Service unavailable |
| 504 | Timeout |

Error codes per [04_GLOSSARY §6].

---

## 2. HTTP API — Phase 1 Endpoints

### 2.1 Auth

#### `POST /v1/auth/signup`
Create a new user, default org, default project. See [06_PRD F-100].

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Tr0ub4dor&3-correct-horse",
  "name": "Jane Doe"
}
```
**Response 201:**
```json
{
  "data": {
    "user": { "id": "usr_...", "email": "...", "name": "...", "email_verified": false },
    "organization": { "id": "org_...", "name": "...", "tier": "free" },
    "project": { "id": "prj_...", "name": "My Project" },
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "...",
      "expires_in": 900,
      "token_type": "Bearer"
    }
  },
  "meta": { "request_id": "req_..." }
}
```

#### `POST /v1/auth/login`
**Request:** `{ "email": "...", "password": "..." }`
**Response 200:** `{ "data": { "user": {...}, "tokens": {...} } }`
**Response 401:** error code `invalid_credentials`

#### `POST /v1/auth/magic-link`
**Request:** `{ "email": "..." }`
**Response 200:** `{ "data": { "sent": true } }` (always, even if email doesn't exist)

#### `GET /v1/auth/magic?token=...`
Server endpoint hit by email link. Validates token, sets cookie, redirects to `/`.

#### `POST /v1/auth/password-reset/request`
**Request:** `{ "email": "..." }`
**Response:** `{ "data": { "sent": true } }`

#### `POST /v1/auth/password-reset/confirm`
**Request:** `{ "token": "...", "new_password": "..." }`
**Response 200:** `{ "data": { "password_reset": true } }`

#### `POST /v1/auth/refresh`
**Request:** `{ "refresh_token": "..." }`
**Response 200:** `{ "data": { "tokens": {...} } }`

#### `POST /v1/auth/logout`
**Request:** `{ "refresh_token": "..." }`
**Response 204**

#### `GET /v1/auth/verify-email?token=...`
Returns 302 redirect to web app with success/failure flag.

---

### 2.2 Me (current user)

#### `GET /v1/me`
**Response 200:**
```json
{ "data": { "id": "usr_...", "email": "...", "name": "...", "email_verified": true, "timezone": "UTC", "locale": "en", "created_at": "..." } }
```

#### `PATCH /v1/me`
**Request (any subset):** `{ "name"?: "...", "timezone"?: "Europe/Berlin", "locale"?: "en" }`

#### `POST /v1/me/email-change`
**Request:** `{ "new_email": "..." }`
Sends confirmation email to new address.

---

### 2.3 Organizations (Phase 1: read-only on default)

#### `GET /v1/organizations/{org_id}`
**Response:** `{ "data": { "id": "org_...", "name": "...", "tier": "free", "created_at": "..." } }`

---

### 2.4 Projects

#### `GET /v1/projects`
**Response:**
```json
{
  "data": [
    { "id": "prj_...", "name": "My Project", "organization_id": "org_...", "device_count": 12, "created_at": "..." }
  ],
  "meta": { "page": { "has_more": false } }
}
```

#### `POST /v1/projects` (Phase 3 — gated by feature flag in Phase 1)
**Request:** `{ "name": "Production", "organization_id": "org_..." }`

#### `GET /v1/projects/{project_id}`
**Response:**
```json
{
  "data": {
    "id": "prj_...",
    "name": "...",
    "organization_id": "org_...",
    "device_count": 12,
    "datapoints_24h": 142000,
    "active_alerts": 1,
    "retention_days": 30,
    "created_at": "..."
  }
}
```

#### `PATCH /v1/projects/{project_id}`
**Request:** `{ "name"?: "..." }`

#### `DELETE /v1/projects/{project_id}` (Phase 3)

---

### 2.5 Devices

#### `POST /v1/projects/{project_id}/devices`
**Request:**
```json
{
  "name": "greenhouse-1-temp",
  "profile_id"?: "dpf_...",
  "labels"?: { "location": "greenhouse-1", "type": "sensor" },
  "description"?: "..."
}
```
**Response 201:**
```json
{
  "data": {
    "device": {
      "id": "dev_...",
      "project_id": "prj_...",
      "name": "...",
      "status": "provisioned",
      "profile_id": "dpf_...",
      "labels": {...},
      "description": "...",
      "created_at": "..."
    },
    "credentials": {
      "mqtt_username": "dev_...",
      "mqtt_password": "<32-char-shown-once>",
      "http_token": "<32-char-shown-once>",
      "mqtt_topics": {
        "up": "v1/prj_.../dev_.../up",
        "down": "v1/prj_.../dev_.../down",
        "state": "v1/prj_.../dev_.../state",
        "event": "v1/prj_.../dev_.../event",
        "ack": "v1/prj_.../dev_.../ack"
      },
      "http_endpoint": "https://api.<host>/v1/ingest"
    },
    "snippets": {
      "python": "from yourplatform import Client\n...",
      "arduino": "#include <YourPlatform.h>\n...",
      "node": "import { Client } from '@yourplatform/sdk';\n...",
      "curl": "curl -X POST https://...\n..."
    }
  }
}
```

#### `GET /v1/projects/{project_id}/devices`
Query: `?status=&label=&search=&sort=&limit=&cursor=`
**Response:**
```json
{
  "data": [
    {
      "id": "dev_...",
      "name": "...",
      "status": "active",
      "last_seen_at": "...",
      "profile_id": "dpf_...",
      "labels": {...},
      "datapoints_24h": 1440
    }
  ],
  "meta": { "page": { "next_cursor": "...", "has_more": true } }
}
```

#### `GET /v1/projects/{project_id}/devices/{device_id}`
**Response:**
```json
{
  "data": {
    "id": "dev_...",
    "name": "...",
    "status": "active",
    "profile_id": "dpf_...",
    "labels": {...},
    "description": "...",
    "last_seen_at": "...",
    "created_at": "...",
    "streams": [
      { "id": "str_...", "key": "temperature", "value_type": "number", "unit": "C", "display_name": "Temperature", "last_value": 23.5, "last_value_at": "..." }
    ]
  }
}
```

#### `PATCH /v1/projects/{project_id}/devices/{device_id}`
Body: `{ "name"?, "profile_id"?, "labels"?, "description"? }`

#### `POST /v1/projects/{project_id}/devices/{device_id}/disable`
#### `POST /v1/projects/{project_id}/devices/{device_id}/enable`
#### `POST /v1/projects/{project_id}/devices/{device_id}/credentials/rotate`
Returns same credentials object as create.

#### `DELETE /v1/projects/{project_id}/devices/{device_id}`
Soft delete. Returns 204.

---

### 2.6 Device Profiles (Phase 1: minimal CRUD)

#### `POST /v1/projects/{project_id}/device-profiles`
**Request:**
```json
{
  "name": "DHT22 Sensor",
  "schema": {
    "type": "object",
    "properties": {
      "temperature": { "type": "number", "minimum": -40, "maximum": 85, "unit": "C" },
      "humidity": { "type": "number", "minimum": 0, "maximum": 100, "unit": "%" }
    }
  },
  "payload_format": "json"
}
```

#### `GET /v1/projects/{project_id}/device-profiles`
#### `GET /v1/projects/{project_id}/device-profiles/{profile_id}`
#### `PATCH /v1/projects/{project_id}/device-profiles/{profile_id}`
#### `DELETE /v1/projects/{project_id}/device-profiles/{profile_id}`

---

### 2.7 Streams

Streams are auto-created by ingest. CRUD is read + edit only.

#### `GET /v1/projects/{project_id}/streams`
Query: `?device_id=&search=&limit=&cursor=`

#### `GET /v1/projects/{project_id}/streams/{stream_id}`
**Response:**
```json
{
  "data": {
    "id": "str_...",
    "device_id": "dev_...",
    "key": "temperature",
    "value_type": "number",
    "unit": "C",
    "display_name": "Temperature",
    "last_value": 23.5,
    "last_value_at": "...",
    "first_value_at": "...",
    "datapoint_count_24h": 1440
  }
}
```

#### `PATCH /v1/projects/{project_id}/streams/{stream_id}`
Body: `{ "display_name"?, "unit"?, "value_type"? }`

---

### 2.8 Telemetry Ingest

#### `POST /v1/ingest`
Auth: device token (preferred) or API key with `write` scope.

**Request body shape A (single value):**
```json
{ "key": "temperature", "value": 23.5, "ts"?: "2025-01-15T10:30:00Z" }
```

**Request body shape B (multi-key):**
```json
{ "values": { "temperature": 23.5, "humidity": 58 }, "ts"?: "..." }
```

**Request body shape C (batch):**
```json
{
  "batch": [
    { "values": { "temperature": 23.5, "humidity": 58 }, "ts": "..." },
    { "values": { "temperature": 23.6 }, "ts": "..." }
  ]
}
```

If using device token, project_id and device_id are inferred from token. If using API key, request must specify `device_id` field at top level.

**Response 202:**
```json
{ "data": { "accepted": 2, "request_id": "req_..." } }
```

---

### 2.9 Telemetry Query

#### `GET /v1/projects/{project_id}/streams/{stream_id}/series`
Query:
- `from` (ISO-8601, required)
- `to` (ISO-8601, default now)
- `agg` (`avg|min|max|sum|count|last`, default `avg`)
- `bucket` (ISO-8601 duration, optional)
- `limit` (max 10000, default 1000)

**Response:**
```json
{
  "data": {
    "stream_id": "str_...",
    "from": "...",
    "to": "...",
    "bucket": "PT1M",
    "agg": "avg",
    "points": [
      { "t": "2025-01-15T10:00:00Z", "v": 23.4 },
      { "t": "2025-01-15T10:01:00Z", "v": 23.5 }
    ]
  }
}
```

#### `GET /v1/projects/{project_id}/streams/series-multi`
Query as above plus `?stream_ids=str_a,str_b,str_c`. Returns array of series.

#### `GET /v1/projects/{project_id}/devices/{device_id}/latest`
**Response:** `{ "data": { "streams": [ { "stream_id": "str_...", "key": "...", "v": 23.5, "t": "..." } ] } }`

#### `GET /v1/projects/{project_id}/streams/{stream_id}/latest`
**Response:** `{ "data": { "v": 23.5, "t": "..." } }`

---

### 2.10 Dashboards

#### `POST /v1/projects/{project_id}/dashboards`
Body: `{ "name", "description"? }`

#### `GET /v1/projects/{project_id}/dashboards`

#### `GET /v1/projects/{project_id}/dashboards/{dashboard_id}`
**Response:**
```json
{
  "data": {
    "id": "dsh_...",
    "name": "...",
    "description": "...",
    "layout": [
      { "id": "wid_...", "x": 0, "y": 0, "w": 6, "h": 4, "type": "line_chart", "config": {...} }
    ],
    "updated_at": "..."
  }
}
```

#### `PATCH /v1/projects/{project_id}/dashboards/{dashboard_id}`
Body: `{ "name"?, "description"? }`

#### `PUT /v1/projects/{project_id}/dashboards/{dashboard_id}/layout`
Body: `{ "layout": [...] }` — replaces entire layout.

#### `DELETE /v1/projects/{project_id}/dashboards/{dashboard_id}`

---

### 2.11 Rules

#### `POST /v1/projects/{project_id}/rules`
Body conforms to [§4 Rule Specification].

#### `GET /v1/projects/{project_id}/rules`
#### `GET /v1/projects/{project_id}/rules/{rule_id}`
#### `PATCH /v1/projects/{project_id}/rules/{rule_id}`
#### `POST /v1/projects/{project_id}/rules/{rule_id}/enable`
#### `POST /v1/projects/{project_id}/rules/{rule_id}/disable`
#### `DELETE /v1/projects/{project_id}/rules/{rule_id}`

#### `GET /v1/projects/{project_id}/rules/{rule_id}/preview`
Query: `?lookback=PT24H` — returns datapoints in lookback that would have triggered the rule.

---

### 2.12 Alerts

#### `GET /v1/projects/{project_id}/alerts`
Query: `?state=&rule_id=&from=&to=&limit=&cursor=`

#### `GET /v1/projects/{project_id}/alerts/{alert_id}`
**Response:**
```json
{
  "data": {
    "id": "alt_...",
    "rule_id": "rul_...",
    "rule_name": "...",
    "state": "firing",
    "fired_at": "...",
    "acknowledged_at": null,
    "resolved_at": null,
    "snoozed_until": null,
    "trigger_data": {
      "device_id": "dev_...",
      "stream_id": "str_...",
      "value": -10.5,
      "threshold": -15
    },
    "deliveries": [
      { "id": "dlv_...", "channel": "email", "to": "ops@...", "status": "delivered", "attempted_at": "..." }
    ]
  }
}
```

#### `POST /v1/projects/{project_id}/alerts/{alert_id}/acknowledge`
#### `POST /v1/projects/{project_id}/alerts/{alert_id}/resolve`
#### `POST /v1/projects/{project_id}/alerts/{alert_id}/snooze`
Body: `{ "duration_s": 3600 }`

---

### 2.13 API Keys

#### `POST /v1/projects/{project_id}/api-keys`
Body: `{ "name", "scopes": ["read","write"], "expires_at"?: "..." }`
**Response 201 (one-time display):**
```json
{
  "data": { "id": "key_...", "name": "...", "scopes": [...], "key": "yp_live_AbC...", "expires_at": "...", "created_at": "..." }
}
```

#### `GET /v1/projects/{project_id}/api-keys`
**Response includes only:** id, name, scopes, prefix (`yp_live_AbC...`), last4, last_used_at, created_at, expires_at.

#### `DELETE /v1/projects/{project_id}/api-keys/{api_key_id}`
Revokes immediately.

---

### 2.14 Audit Log

#### `GET /v1/projects/{project_id}/audit-events`
Query: `?action=&actor_id=&from=&to=&limit=&cursor=`
**Response:**
```json
{
  "data": [
    {
      "id": "aud_...",
      "action": "device.created",
      "actor": { "type": "user", "id": "usr_...", "email": "..." },
      "target": { "type": "device", "id": "dev_..." },
      "data": { "name": "..." },
      "ip": "1.2.3.4",
      "user_agent": "...",
      "created_at": "..."
    }
  ]
}
```

---

### 2.15 Internal Endpoints (not public)

#### `POST /internal/mqtt/auth`
Called by EMQX. Validates client credentials. Returns ACL.
**Request:** `{ "clientid": "...", "username": "...", "password": "..." }`
**Response 200:** `{ "result": "allow", "acl": [ { "action": "publish", "topic": "v1/.../up" }, ... ] }`
**Response 200 (deny):** `{ "result": "deny" }`

#### `POST /internal/mqtt/disconnect`
Called by EMQX webhook on disconnect. Updates device status.

---

## 3. NATS Event Catalog

### 3.1 Envelope (every message)

```json
{
  "schema": "telemetry.datapoint.v1",
  "event_id": "01H8...",
  "occurred_at": "2025-01-15T10:30:00.123Z",
  "ingested_at": "2025-01-15T10:30:00.567Z",
  "project_id": "prj_...",
  "correlation_id": "req_...",
  "source": "mqtt",
  "data": { /* schema-specific */ },
  "metadata": {
    "tenant_tier": "pro",
    "trace_id": "0af7651916cd43dd8448eb211c80319c"
  }
}
```

### 3.2 Streams (NATS JetStream)

| Stream name | Subject pattern | Retention | Storage |
|---|---|---|---|
| `INGEST` | `ingest.raw.v1.>` | 24h | file |
| `TELEMETRY` | `telemetry.datapoint.v1.>` | 24h | file |
| `ALERTS` | `alerts.fired.v1.>`, `alerts.resolved.v1.>` | 7d | file |
| `RULES` | `rules.changed.v1.>` | 24h | memory |
| `AUDIT` | `audit.event.v1.>` | 30d | file |
| `DEVICES` | `devices.state.v1.>` | 24h | file |
| `AI` | `ai.request.v1.>`, `ai.response.v1.>` | 24h | file |

### 3.3 Event schemas

#### `ingest.raw.v1`
```json
{
  "schema": "ingest.raw.v1",
  "data": {
    "device_id": "dev_..." | null,
    "source": "mqtt|http|lora",
    "payload_format": "json|cbor|cayenne_lpp|binary",
    "payload": "<base64-encoded raw payload>",
    "received_at": "...",
    "transport_metadata": {
      "mqtt_topic"?: "...",
      "lora_dev_eui"?: "...",
      "rssi"?: -90,
      "snr"?: 9.5
    }
  }
}
```

#### `telemetry.datapoint.v1`
```json
{
  "schema": "telemetry.datapoint.v1",
  "data": {
    "device_id": "dev_...",
    "stream_id": "str_...",
    "key": "temperature",
    "value_type": "number",
    "value_num"?: 23.5,
    "value_bool"?: null,
    "value_str"?: null,
    "value_json"?: null,
    "ts": "2025-01-15T10:30:00.123Z",
    "quality": 0
  }
}
```

#### `alerts.fired.v1`
```json
{
  "schema": "alerts.fired.v1",
  "data": {
    "alert_id": "alt_...",
    "rule_id": "rul_...",
    "rule_name": "...",
    "device_id": "dev_...",
    "stream_id": "str_...",
    "trigger_value": -10.5,
    "trigger_window": [{"t": "...", "v": -10.0}, {"t": "...", "v": -10.5}],
    "actions": [
      { "type": "email", "to": "..." },
      { "type": "webhook", "url": "...", "secret": "..." }
    ]
  }
}
```

#### `alerts.resolved.v1`
```json
{ "schema": "alerts.resolved.v1", "data": { "alert_id": "alt_...", "resolved_at": "...", "resolved_by": "user|auto" } }
```

#### `rules.changed.v1`
```json
{ "schema": "rules.changed.v1", "data": { "rule_id": "rul_...", "change": "created|updated|deleted|enabled|disabled" } }
```

#### `devices.state.v1`
```json
{ "schema": "devices.state.v1", "data": { "device_id": "dev_...", "status": "active|inactive|disabled", "previous_status": "..." } }
```

#### `audit.event.v1`
```json
{
  "schema": "audit.event.v1",
  "data": {
    "action": "device.created",
    "actor": { "type": "user|api_key|system", "id": "...", "email"?: "..." },
    "target": { "type": "device", "id": "..." },
    "data": { /* action-specific */ },
    "ip"?: "...",
    "user_agent"?: "..."
  }
}
```

### 3.4 Idempotency

- Every consumer dedups on `event_id` via Redis `SETEX <event_id> 86400 1` then `EXISTS`.
- Producers must guarantee unique `event_id` per logical event (use ULID).

### 3.5 Versioning rules

- New optional fields: same `vN`, no break.
- Removed/renamed/retyped: bump to `v(N+1)`. Old version runs side by side until all consumers migrate.
- Consumers ignore unknown schema versions (log + drop, never crash).

---

## 4. Rule Specification

### 4.1 Rule JSON schema

```json
{
  "id": "rul_...",
  "project_id": "prj_...",
  "name": "Cold storage breach",
  "description": "Optional",
  "scope": {
    "device_ids"?: ["dev_..."],
    "device_label_selector"?: { "type": "sensor", "location": "warehouse-1" },
    "stream_keys": ["temperature"]
  },
  "trigger": {
    "type": "threshold|range|rate_of_change|inactivity|anomaly|composite",
    /* fields depend on type, see §4.2 */
  },
  "actions": [
    { "type": "email", "to": "ops@example.com", "include_chart"?: true },
    { "type": "webhook", "url": "https://...", "secret": "...", "headers"?: {} },
    { "type": "slack", "webhook_url": "https://hooks.slack.com/..." }
  ],
  "debounce_s": 1800,
  "auto_resolve_s"?: 600,
  "enabled": true,
  "created_at": "...",
  "updated_at": "..."
}
```

### 4.2 Trigger type variants

#### `threshold`
```json
{
  "type": "threshold",
  "comparator": "> | >= | < | <= | == | !=",
  "value": -15.0,
  "window_s": 600,
  "aggregation": "all | any | avg | min | max"
}
```
- `window_s = 0`: single-datapoint check.
- `window_s > 0`: collect datapoints in window, apply `aggregation`, compare.

#### `range` (Phase 1.5)
```json
{ "type": "range", "min": -20, "max": -10, "outside_range": true, "window_s": 0 }
```

#### `rate_of_change` (Phase 2)
```json
{ "type": "rate_of_change", "delta": 5, "comparator": ">", "window_s": 60 }
```

#### `inactivity` (Phase 2)
```json
{ "type": "inactivity", "duration_s": 3600 }
```

#### `anomaly` (Phase 2)
```json
{ "type": "anomaly", "score_threshold": 0.85, "min_confidence": 0.7 }
```

### 4.3 Scope resolution
- If `device_ids` specified: use those.
- Else if `device_label_selector` specified: match all devices whose labels contain all selector pairs.
- `stream_keys` filters which streams of those devices are considered.

### 4.4 Debounce
After firing, rule cannot fire again for `debounce_s` seconds.

### 4.5 Auto-resolve
If `auto_resolve_s` set: alert auto-resolves after `auto_resolve_s` of condition no longer being met.

---

## 5. Database Schema (DDL)

> Migrations: Alembic, `apps/api/migrations/versions/`. Each PR adds at most a few. Naming: `YYYYMMDDHHMM_<short_desc>.py`.

### 5.1 Initial migration: identity & tenancy

```sql
create extension if not exists "pg_trgm";
create extension if not exists "vector";
create extension if not exists "timescaledb";

create table users (
  id            text primary key,
  email         citext unique not null,
  password_hash text not null,
  name          text not null,
  email_verified_at timestamptz,
  timezone      text not null default 'UTC',
  locale        text not null default 'en',
  status        text not null default 'active',
  failed_login_count int not null default 0,
  locked_until  timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table organizations (
  id          text primary key,
  name        text not null,
  tier        text not null default 'free',
  owner_id    text not null references users(id),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index ix_organizations_owner on organizations(owner_id);

create table organization_members (
  organization_id text not null references organizations(id) on delete cascade,
  user_id         text not null references users(id) on delete cascade,
  role            text not null,
  created_at      timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create table projects (
  id              text primary key,
  organization_id text not null references organizations(id),
  name            text not null,
  slug            text not null,
  retention_days  int not null default 30,
  status          text not null default 'active',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  deleted_at      timestamptz,
  unique (organization_id, slug)
);
create index ix_projects_org on projects(organization_id) where deleted_at is null;

create table project_members (
  project_id text not null references projects(id) on delete cascade,
  user_id    text not null references users(id) on delete cascade,
  role       text not null,
  created_at timestamptz not null default now(),
  primary key (project_id, user_id)
);

create table refresh_tokens (
  id           text primary key,
  user_id      text not null references users(id) on delete cascade,
  hashed_token text not null,
  expires_at   timestamptz not null,
  used_at      timestamptz,
  created_at   timestamptz not null default now()
);
create index ix_refresh_tokens_user on refresh_tokens(user_id);
create index ix_refresh_tokens_expires on refresh_tokens(expires_at);

create table magic_links (
  id           text primary key,
  email        citext not null,
  hashed_token text not null,
  purpose      text not null,         -- 'login' | 'verify_email' | 'password_reset'
  expires_at   timestamptz not null,
  used_at      timestamptz,
  created_at   timestamptz not null default now()
);
create index ix_magic_links_email on magic_links(email, purpose);
create index ix_magic_links_expires on magic_links(expires_at);
```

### 5.2 Devices, profiles, credentials

```sql
create table device_profiles (
  id             text primary key,
  project_id     text not null references projects(id) on delete cascade,
  name           text not null,
  schema         jsonb not null default '{}'::jsonb,
  decoder_js     text,
  payload_format text not null default 'json',
  protocol       text not null default 'mqtt',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (project_id, name)
);

create table devices (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  profile_id   text references device_profiles(id),
  name         text not null,
  description  text,
  labels       jsonb not null default '{}'::jsonb,
  status       text not null default 'provisioned',
  protocol     text not null default 'mqtt',
  last_seen_at timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  deleted_at   timestamptz,
  unique (project_id, name)
);
create index ix_devices_project_status on devices(project_id, status) where deleted_at is null;
create index ix_devices_labels on devices using gin(labels);
create index ix_devices_last_seen on devices(last_seen_at desc nulls last);

create table device_credentials (
  device_id      text primary key references devices(id) on delete cascade,
  mqtt_username  text not null unique,
  mqtt_password_hash text not null,
  http_token_hash text not null unique,
  rotated_at     timestamptz not null default now()
);

create table device_downlinks (
  id           text primary key,
  device_id    text not null references devices(id) on delete cascade,
  payload      bytea not null,
  payload_format text not null default 'json',
  fport        int default 10,                -- LoRa
  scheduled_at timestamptz not null default now(),
  delivered_at timestamptz,
  acknowledged_at timestamptz,
  status       text not null default 'queued',
  created_at   timestamptz not null default now()
);
create index ix_downlinks_device_status on device_downlinks(device_id, status);
```

### 5.3 Streams

```sql
create table streams (
  id              text primary key,
  project_id      text not null references projects(id) on delete cascade,
  device_id       text not null references devices(id) on delete cascade,
  key             text not null,
  value_type      text not null,
  unit            text,
  display_name    text,
  last_value      jsonb,
  last_value_at   timestamptz,
  first_value_at  timestamptz,
  created_at      timestamptz not null default now(),
  unique (device_id, key)
);
create index ix_streams_project on streams(project_id);
create index ix_streams_key_trgm on streams using gin (key gin_trgm_ops);
```

### 5.4 Dashboards & widgets

```sql
create table dashboards (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  name         text not null,
  description  text,
  layout       jsonb not null default '[]'::jsonb,  -- array of widgets inline
  visibility   text not null default 'private',
  share_token  text,
  share_password_hash text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  deleted_at   timestamptz
);
create index ix_dashboards_project on dashboards(project_id) where deleted_at is null;
create unique index ix_dashboards_share_token on dashboards(share_token) where share_token is not null;
```

(Widgets stored as embedded JSON within layout to avoid join chatter.)

### 5.5 Rules & alerts

```sql
create table rules (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  name         text not null,
  description  text,
  spec         jsonb not null,
  status       text not null default 'enabled',
  last_fired_at timestamptz,
  fire_count   bigint not null default 0,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index ix_rules_project_status on rules(project_id, status);
create index ix_rules_spec_devices on rules using gin ((spec->'scope'->'device_ids'));

create table alerts (
  id              text primary key,
  rule_id         text not null references rules(id),
  project_id      text not null,
  state           text not null default 'firing',
  fired_at        timestamptz not null,
  acknowledged_at timestamptz,
  resolved_at     timestamptz,
  snoozed_until   timestamptz,
  trigger_data    jsonb not null,
  created_at      timestamptz not null default now()
);
create index ix_alerts_project_state on alerts(project_id, state, fired_at desc);
create index ix_alerts_rule on alerts(rule_id, fired_at desc);

create table alert_deliveries (
  id           text primary key,
  alert_id     text not null references alerts(id) on delete cascade,
  channel      text not null,
  target       text not null,
  status       text not null default 'pending',
  attempt_count int not null default 0,
  last_attempt_at timestamptz,
  delivered_at timestamptz,
  error        text,
  created_at   timestamptz not null default now()
);
create index ix_deliveries_alert on alert_deliveries(alert_id);
create index ix_deliveries_status on alert_deliveries(status, last_attempt_at);
```

### 5.6 API keys

```sql
create table api_keys (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  name         text not null,
  prefix       text not null,           -- yp_live_AbCd
  last4        text not null,
  hashed_secret text not null,
  scopes       text[] not null default '{}',
  created_by   text not null references users(id),
  expires_at   timestamptz,
  revoked_at   timestamptz,
  last_used_at timestamptz,
  created_at   timestamptz not null default now()
);
create index ix_api_keys_project on api_keys(project_id) where revoked_at is null;
```

### 5.7 AI (Phase 2 stubs)

```sql
create table ai_conversations (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  user_id      text not null references users(id),
  title        text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create table ai_messages (
  id              text primary key,
  conversation_id text not null references ai_conversations(id) on delete cascade,
  role            text not null,
  content         text not null,
  tool_calls      jsonb,
  tokens_in       int,
  tokens_out      int,
  model           text,
  created_at      timestamptz not null default now()
);
create index ix_ai_messages_conv on ai_messages(conversation_id, created_at);

create table ai_proposals (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  user_id      text not null references users(id),
  conversation_id text references ai_conversations(id),
  kind         text not null,
  spec         jsonb not null,
  status       text not null default 'proposed',
  applied_at   timestamptz,
  rejected_at  timestamptz,
  created_at   timestamptz not null default now(),
  expires_at   timestamptz not null
);

create table embeddings (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  subject_type text not null,
  subject_id   text not null,
  text         text not null,
  vector       vector(768) not null,
  created_at   timestamptz not null default now(),
  unique (project_id, subject_type, subject_id)
);
create index ix_embeddings_vec on embeddings using hnsw (vector vector_cosine_ops);
```

### 5.8 Audit log

```sql
create table audit_events (
  id           text primary key,
  project_id   text references projects(id) on delete set null,
  organization_id text references organizations(id) on delete set null,
  action       text not null,
  actor_type   text not null,
  actor_id     text,
  actor_email  text,
  target_type  text,
  target_id    text,
  data         jsonb not null default '{}'::jsonb,
  ip           inet,
  user_agent   text,
  created_at   timestamptz not null default now()
);
create index ix_audit_project_time on audit_events(project_id, created_at desc);
create index ix_audit_actor on audit_events(actor_id, created_at desc);
create index ix_audit_action on audit_events(action, created_at desc);
```

### 5.9 Webhooks

```sql
create table webhooks (
  id           text primary key,
  project_id   text not null references projects(id) on delete cascade,
  name         text not null,
  url          text not null,
  secret_hash  text not null,
  events       text[] not null,
  enabled      boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
```

### 5.10 Subscriptions / billing (Phase 5 stub)

```sql
create table subscriptions (
  id              text primary key,
  organization_id text not null unique references organizations(id),
  tier            text not null,
  status          text not null,
  current_period_end timestamptz,
  external_id     text,                -- Stripe / Polar id
  metadata        jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create table usage_counters (
  organization_id text not null references organizations(id),
  metric          text not null,
  period          text not null,        -- '2025-01'
  value           bigint not null default 0,
  primary key (organization_id, metric, period)
);
```

---

## 6. Time-series Tables and Aggregates

### 6.1 Hypertable

```sql
create table telemetry (
  time         timestamptz not null,
  project_id   text not null,
  device_id    text not null,
  stream_id    text not null,
  key          text not null,
  value_num    double precision,
  value_bool   boolean,
  value_str    text,
  value_json   jsonb,
  quality      smallint not null default 0,
  ingested_at  timestamptz not null default now()
);

select create_hypertable('telemetry', 'time',
  chunk_time_interval => interval '1 day',
  partitioning_column => 'project_id',
  number_partitions   => 16);

create index ix_tel_proj_dev_key_time on telemetry (project_id, device_id, key, time desc);
create index ix_tel_stream_time on telemetry (stream_id, time desc);
```

### 6.2 Continuous aggregates

```sql
create materialized view telemetry_1m
with (timescaledb.continuous) as
select time_bucket('1 minute', time) as bucket,
       project_id, device_id, stream_id, key,
       avg(value_num) as avg_v,
       min(value_num) as min_v,
       max(value_num) as max_v,
       sum(value_num) as sum_v,
       count(*)        as n,
       last(value_num, time) as last_v
from telemetry
where value_num is not null
group by bucket, project_id, device_id, stream_id, key;

select add_continuous_aggregate_policy('telemetry_1m',
  start_offset => interval '7 days',
  end_offset   => interval '1 minute',
  schedule_interval => interval '1 minute');

-- Repeat for 5m, 1h, 1d
```

### 6.3 Compression

```sql
alter table telemetry set (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'project_id, device_id, key'
);
select add_compression_policy('telemetry', interval '7 days');
```

### 6.4 Retention

Per project, configurable. Implemented via scheduler that drops chunks older than `retention_days` per project (chunk drop is by time, so we use a project-aware deletion job for cross-cutting cases). For Phase 1: global retention via Timescale policy aligned with the highest tier's value (365 days).

```sql
select add_retention_policy('telemetry', interval '365 days');
```

The scheduler additionally runs nightly:
```sql
delete from telemetry t
where t.project_id = $1
  and t.time < now() - interval '<project_retention_days> days';
```
(Less efficient but project-scoped.)

### 6.5 Read path

The `series` query selects the smallest aggregate satisfying `bucket`:

```sql
-- pseudo
select
  case
    when bucket >= '1 day'::interval    then 'telemetry_1d'
    when bucket >= '1 hour'::interval   then 'telemetry_1h'
    when bucket >= '5 minutes'::interval then 'telemetry_5m'
    when bucket >= '1 minute'::interval  then 'telemetry_1m'
    else 'telemetry'
  end;
```

---

## 7. Webhook Payload Specification

### 7.1 Headers
- `User-Agent: yourplatform-webhook/1.0`
- `X-YP-Event: alert.fired` (or other event name)
- `X-YP-Delivery: dlv_...`
- `X-YP-Timestamp: 1736932200`
- `X-YP-Signature: sha256=<hex>`
- `Content-Type: application/json`

### 7.2 Signature
```
HMAC-SHA256( secret, "{X-YP-Timestamp}.{raw_body}" )
```
Receivers must:
1. Verify timestamp within 5 minutes of now.
2. Compute HMAC; constant-time compare.

### 7.3 Body schemas

**`alert.fired`:**
```json
{
  "event": "alert.fired",
  "delivery_id": "dlv_...",
  "alert": {
    "id": "alt_...",
    "rule_id": "rul_...",
    "rule_name": "Cold storage breach",
    "fired_at": "...",
    "trigger_data": { ... }
  },
  "project": { "id": "prj_...", "name": "..." }
}
```

**`alert.resolved`, `device.offline`** etc. — same shape, different `event` and payload.

### 7.4 Retry policy
- 3 attempts: immediate, +1m, +5m, +15m.
- Considered delivered on 2xx response.
- Considered failed (no retry) on 410 Gone.
- Requires response within 10 s.

---

## 8. MQTT Topic & Payload Specification

### 8.1 Topic structure

```
v1/<project_id>/<device_id>/<channel>
```

Channels:
| Channel | Direction | QoS | Retain | Purpose |
|---|---|---|---|---|
| `up` | device → cloud | 0 or 1 | no | Telemetry payload |
| `down` | cloud → device | 1 | no | Command / downlink |
| `state` | device → cloud | 1 | yes | Latest state, retained |
| `event` | device → cloud | 1 | no | Discrete event (button press, etc.) |
| `ack` | device → cloud | 1 | no | Acknowledge a downlink |

### 8.2 Payload formats

**JSON (default):**
- Same shapes as HTTP `/v1/ingest` body (single, multi-key, batch).
- UTF-8 encoded.

**CBOR:**
- Same logical shapes, encoded per RFC 8949.
- Indicated by device profile `payload_format: cbor`.

**CayenneLPP:**
- Per [Cayenne LPP spec].
- Channel byte → mapped to stream key via device profile.

**Binary (custom):**
- Decoded by device profile's `decoder_js` function (sandboxed JS, runs in ingest service).

### 8.3 Connection

- Username = `dev_<device_id>` (or as returned at provisioning).
- Password = `mqtt_password` from credentials.
- Client ID format: `dev_<device_id>` (uniqueness enforced; second connection kicks first).
- Keepalive: 60s recommended; broker max 600s.
- Clean session: true by default. Persistent session allowed (QoS 1+) by configuration.

### 8.4 Will message (recommended)

```
topic: v1/<project_id>/<device_id>/state
retained: true
payload: {"online": false, "ts": "<sent-on-connect>"}
```

On normal connect, device publishes `{"online": true, ...}` with retain=true.
