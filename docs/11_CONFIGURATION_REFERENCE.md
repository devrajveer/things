# Configuration Reference

Every environment variable for every service. **All configuration is environment-driven.** No service reads from disk at runtime except for static asset paths.

> Conventions: [05_CODING_STANDARDS §13]: var names ending in `_PASSWORD`, `_SECRET`, `_KEY`, `_TOKEN`, `_DSN` are secrets and must never be logged. Loaded into Pydantic Settings classes per service.

---

## Table of contents

- §1 Conventions
- §2 Shared variables (set in `.env` for all services)
- §3 Per-service variables
- §4 Feature flags
- §5 Local development defaults (`.env.example`)
- §6 Production checklist
- §7 Schema validation

---

## 1. Conventions

### 1.1 Naming

- All env vars `UPPER_SNAKE_CASE`.
- Service-specific vars NOT prefixed with service name unless they conflict (avoid prefix sprawl).
- Boolean values: `true` / `false` (case-insensitive). Settings parses to `bool`.
- Duration values: integer seconds, suffix `_SECONDS` or `_S`. Or ISO-8601 duration with `_DURATION` suffix.
- URL values: full URL including scheme. Suffix `_URL`.
- DSN/connection strings: suffix `_DSN`.
- File paths: suffix `_PATH`.

### 1.2 Loading order

Each service's `Settings` class loads from:
1. Real environment.
2. `.env` file in working directory (development only; not loaded in production).
3. Defaults declared in the Settings model.

Production processes start with `--no-env-file` to prevent accidental load.

### 1.3 Validation

- Every variable typed in Pydantic.
- Required variables have no default.
- On boot, if any required var is missing or invalid, the service exits with code `2` and prints which var is bad.

### 1.4 Required vs optional

In tables below: **R** = required (no default, must be set), **O** = optional (has default).

---

## 2. Shared Variables

These are commonly set on all services in the platform's `.env`.

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `ENVIRONMENT` | enum: `dev|staging|prod` | R | — | Deployment environment. Affects logging format, error verbosity, defaults. |
| `LOG_LEVEL` | enum: `debug|info|warning|error|critical` | O | `info` (prod), `debug` (dev) | Root logger level. |
| `LOG_FORMAT` | enum: `json|console` | O | `json` (prod), `console` (dev) | Log output format. |
| `RELEASE_VERSION` | string | O | `dev` | Set at build time to git SHA / CalVer; included in logs and error reports. |
| `SERVICE_NAME` | string | O | (per service) | Override of default service name in logs/traces. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | URL | O | unset | If set, traces and metrics exported via OTLP. |
| `OTEL_RESOURCE_ATTRIBUTES` | string | O | unset | Comma-separated extra OTel resource attributes. |
| `SENTRY_DSN` | DSN | O | unset | If set, errors reported to Sentry/GlitchTip. |
| `SENTRY_TRACES_SAMPLE_RATE` | float 0–1 | O | `0.1` | Trace sampling. |

---

## 3. Per-Service Variables

### 3.1 `api` (FastAPI)

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `HOST` | string | O | `0.0.0.0` | Bind interface. |
| `PORT` | int | O | `8000` | HTTP port. |
| `WORKERS` | int | O | `(2 × cores) + 1` | Gunicorn worker count. |
| `MAX_REQUESTS` | int | O | `1000` | Max requests per worker before recycle. |
| `MAX_REQUESTS_JITTER` | int | O | `50` | Recycle jitter. |
| `KEEPALIVE_SECONDS` | int | O | `5` | HTTP keep-alive. |
| `REQUEST_TIMEOUT_SECONDS` | int | O | `30` | Per-request hard timeout. |
| `POSTGRES_DSN` | DSN | R | — | e.g. `postgresql+asyncpg://yp:pw@db:5432/yourplatform` |
| `POSTGRES_POOL_MIN` | int | O | `5` | Min pool connections. |
| `POSTGRES_POOL_MAX` | int | O | `20` | Max pool connections. |
| `POSTGRES_POOL_TIMEOUT_SECONDS` | int | O | `30` | Connection acquire timeout. |
| `REDIS_URL` | URL | R | — | e.g. `redis://:pw@redis:6379/0` |
| `REDIS_POOL_MAX` | int | O | `50` | Max pool connections. |
| `NATS_URL` | URL | R | — | e.g. `nats://api-user:pw@nats:4222` |
| `NATS_STREAM_NAME` | string | O | `INGEST,TELEMETRY,ALERTS,RULES,DEVICES,AUDIT` | Streams the API service publishes to. |
| `MINIO_ENDPOINT` | URL | R | — | e.g. `http://minio:9000` |
| `MINIO_ACCESS_KEY` | string | R | — | |
| `MINIO_SECRET_KEY` | string | R | — | |
| `MINIO_USE_SSL` | bool | O | `false` | |
| `MINIO_BUCKET_AVATARS` | string | O | `yp-avatars` | |
| `MINIO_BUCKET_EXPORTS` | string | O | `yp-exports` | |
| `JWT_SECRET` | string ≥32 chars | R | — | HS256 key. Rotate per [09_SECURITY_SPEC §5.4]. |
| `JWT_SECRET_PREVIOUS` | string | O | unset | During key rotation; tokens signed with this still verified. |
| `JWT_ACCESS_TTL_SECONDS` | int | O | `900` (15 min) | |
| `JWT_ISSUER` | string | O | `https://api.<host>` | |
| `JWT_AUDIENCE` | string | O | `yp-api` | |
| `REFRESH_TOKEN_TTL_SECONDS` | int | O | `2592000` (30 d) | |
| `PASSWORD_PEPPER` | string | O | unset | Optional global pepper added before hash. |
| `ARGON2_TIME_COST` | int | O | `3` | |
| `ARGON2_MEMORY_KIB` | int | O | `65536` | 64 MB. |
| `ARGON2_PARALLELISM` | int | O | `4` | |
| `RATE_LIMIT_LOGIN_PER_MIN` | int | O | `5` | Failed logins per email per minute. |
| `RATE_LIMIT_DEFAULT_PER_MIN` | int | O | `60` | Default per-IP rate. |
| `EMAIL_FROM_ADDRESS` | email | R | — | e.g. `noreply@<host>` |
| `EMAIL_FROM_NAME` | string | O | `yourplatform` | |
| `SMTP_HOST` | string | R | — | Postal host or SMTP relay. |
| `SMTP_PORT` | int | O | `587` | |
| `SMTP_USERNAME` | string | R | — | |
| `SMTP_PASSWORD` | string | R | — | |
| `SMTP_USE_TLS` | bool | O | `true` | |
| `WEB_APP_BASE_URL` | URL | R | — | e.g. `https://app.<host>` (used in email links). |
| `API_BASE_URL` | URL | R | — | e.g. `https://api.<host>` (used in code snippets). |
| `MQTT_PUBLIC_HOST` | string | R | — | Hostname devices connect to. |
| `MQTT_PUBLIC_PORT_PLAIN` | int | O | `1883` | |
| `MQTT_PUBLIC_PORT_TLS` | int | O | `8883` | |
| `CORS_ORIGINS` | comma list | R | — | e.g. `https://app.<host>,https://docs.<host>` |
| `INTERNAL_API_TOKEN` | string ≥32 | R | — | Shared secret used by EMQX/ChirpStack for internal endpoints. |
| `FEATURE_FLAGS` | comma list | O | (env-defaults, see §4) | Override flags. |

### 3.2 `ingest` (Python async)

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `HOST` | string | O | `0.0.0.0` | |
| `PORT` | int | O | `8001` | HTTP port for `/v1/ingest`. |
| `POSTGRES_DSN` | DSN | R | — | Used for credential validation cache only. |
| `REDIS_URL` | URL | R | — | Token validation cache + per-device rate limit. |
| `NATS_URL` | URL | R | — | Publishes `ingest.raw.v1`, `telemetry.datapoint.v1`. |
| `MQTT_BROKER_URL` | URL | R | — | EMQX endpoint for internal subscription, e.g. `mqtt://ingest-user:pw@emqx:1883` |
| `MQTT_TOPIC_FILTER` | string | O | `v1/+/+/up,v1/+/+/state,v1/+/+/event,v1/+/+/ack` | Topics consumed. |
| `MAX_PAYLOAD_BYTES` | int | O | `262144` (256 KB) | Per-message hard limit. |
| `MAX_BATCH_SIZE` | int | O | `100` | Max items in a batch HTTP body. |
| `INGEST_DEFAULT_RATE_PER_SEC` | int | O | `10` | Per-device default rate. |
| `JS_DECODER_TIMEOUT_MS` | int | O | `50` | Sandbox timeout for custom JS decoders. |
| `JS_DECODER_MEMORY_MB` | int | O | `16` | |
| `LORA_INTEGRATION_ENABLED` | bool | O | `false` | Phase 3. Enables ChirpStack MQTT subscription. |
| `LORA_MQTT_URL` | URL | O | unset | ChirpStack internal MQTT bridge. |

### 3.3 `realtime` (Node + uWebSockets)

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `HOST` | string | O | `0.0.0.0` | |
| `PORT` | int | O | `8002` | |
| `NATS_URL` | URL | R | — | Subscribes to `telemetry.datapoint.v1.>`, `alerts.fired.v1.>`. |
| `JWT_SECRET` | string | R | — | For verifying access tokens on connect. |
| `JWT_ISSUER` | string | O | `https://api.<host>` | |
| `JWT_AUDIENCE` | string | O | `yp-api` | |
| `REDIS_URL` | URL | R | — | Authz cache. |
| `MAX_CONNECTIONS_PER_USER` | int | O | `10` | |
| `MAX_SUBSCRIPTIONS_PER_CONN` | int | O | `100` | |
| `BACKPRESSURE_BUFFER_MS` | int | O | `1000` | Drop after this much queued time. |
| `HEARTBEAT_INTERVAL_SECONDS` | int | O | `30` | |
| `HEARTBEAT_TIMEOUT_SECONDS` | int | O | `90` | Disconnect idle clients. |

### 3.4 `worker` (Dramatiq)

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `POSTGRES_DSN` | DSN | R | — | |
| `REDIS_URL` | URL | R | — | Dramatiq broker + dedup. |
| `NATS_URL` | URL | R | — | Subscribes to `telemetry.datapoint.v1.>`, publishes `alerts.fired.v1`. |
| `MINIO_ENDPOINT` | URL | R | — | For exports. |
| `MINIO_ACCESS_KEY` | string | R | — | |
| `MINIO_SECRET_KEY` | string | R | — | |
| `WORKER_PROCESSES` | int | O | `2` | |
| `WORKER_THREADS_PER_PROCESS` | int | O | `8` | |
| `WORKER_QUEUES` | comma list | O | `default,ts_writer,rule_engine,alerts,webhooks,exports,retention` | |
| `RULE_HISTORY_CACHE_TTL_SECONDS` | int | O | `300` | |
| `WEBHOOK_TIMEOUT_SECONDS` | int | O | `10` | |
| `WEBHOOK_MAX_RETRIES` | int | O | `3` | |
| `WEBHOOK_DENY_NETWORKS` | comma list | O | (per [09_SECURITY_SPEC §6.5]) | CIDRs blocked for outbound. |
| `EMAIL_FROM_ADDRESS` | email | R | — | |
| `SMTP_*` | (same as api) | R | — | |
| `TS_WRITER_BATCH_SIZE` | int | O | `1000` | Datapoints per insert batch. |
| `TS_WRITER_FLUSH_INTERVAL_MS` | int | O | `200` | |

### 3.5 `ai-worker` (LangGraph) — Phase 2

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `POSTGRES_DSN` | DSN | R | — | |
| `NATS_URL` | URL | R | — | |
| `REDIS_URL` | URL | R | — | |
| `LLM_PROVIDER` | enum: `openrouter|openai|anthropic|ollama|none` | O | `openrouter` | |
| `LLM_MODEL_DEFAULT` | string | O | `meta-llama/llama-3.1-70b-instruct` | |
| `LLM_API_KEY` | string | R if provider != none/ollama | — | |
| `LLM_BASE_URL` | URL | O | provider default | Override (Ollama: `http://ollama:11434`). |
| `LLM_TIMEOUT_SECONDS` | int | O | `60` | |
| `LLM_MAX_TOKENS` | int | O | `4000` | |
| `LLM_MAX_CONTEXT_TOKENS` | int | O | `32000` | Truncate older messages above this. |
| `EMBEDDINGS_MODEL` | string | O | `nomic-embed-text` | |
| `EMBEDDINGS_PROVIDER` | enum | O | `ollama` | |
| `AI_PROPOSAL_TTL_SECONDS` | int | O | `1800` (30 min) | Auto-expiry. |
| `BYO_KEY_ENABLED` | bool | O | `true` | Lets users supply their own LLM keys. |

### 3.6 `scheduler`

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `POSTGRES_DSN` | DSN | R | — | |
| `REDIS_URL` | URL | R | — | Distributed leader lock. |
| `NATS_URL` | URL | R | — | |
| `LEADER_LOCK_TTL_SECONDS` | int | O | `30` | |
| `LEADER_RENEW_INTERVAL_SECONDS` | int | O | `10` | |
| `JOBS_ENABLED` | comma list | O | `retention,aggregations,subscription_renewal,backup_check,inactivity_check` | |

### 3.7 `web` (Next.js)

Note: vars prefixed `NEXT_PUBLIC_` are inlined into client bundles and visible to users — never put secrets there.

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | URL | R | — | e.g. `https://api.<host>` |
| `NEXT_PUBLIC_REALTIME_URL` | URL | R | — | e.g. `wss://realtime.<host>` |
| `NEXT_PUBLIC_DOCS_URL` | URL | O | `https://docs.<host>` | |
| `NEXT_PUBLIC_BRAND_NAME` | string | O | `yourplatform` | |
| `NEXT_PUBLIC_PRIMARY_COLOR_HSL` | string | O | `221 83% 53%` | Theme primary. |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN | O | unset | Client-side error reporting. |
| `NEXT_PUBLIC_FEATURE_FLAGS` | comma list | O | (env defaults) | Client-visible flags. |
| `NEXT_PUBLIC_PLAUSIBLE_DOMAIN` | string | O | unset | Privacy-first analytics. |
| `NEXTAUTH_URL` | URL | R | — | Used by middleware. |
| `NEXTAUTH_SECRET` | string ≥32 | R | — | Cookie session encryption (server). |
| `INTERNAL_API_TOKEN` | string | O | unset | For server-side BFF route handlers needing privileged calls. |

### 3.8 `mqtt-broker` (EMQX)

EMQX has its own config file (`emqx.conf` mounted in container). Key env overrides:

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `EMQX_NODE__COOKIE` | string | R | — | Cluster cookie. |
| `EMQX_DASHBOARD__DEFAULT_USERNAME` | string | O | `admin` | Disable in prod. |
| `EMQX_DASHBOARD__DEFAULT_PASSWORD` | string | R | — | Strong password if dashboard exposed. |
| `EMQX_LISTENER__TCP__EXTERNAL` | string | O | `0.0.0.0:1883` | |
| `EMQX_LISTENER__SSL__EXTERNAL` | string | O | `0.0.0.0:8883` | TLS port. |
| `EMQX_LISTENER__WS__EXTERNAL` | string | O | `0.0.0.0:8083` | WebSocket. |
| `EMQX_LISTENER__WSS__EXTERNAL` | string | O | `0.0.0.0:8084` | WSS. |
| `EMQX_LOG__CONSOLE_HANDLER__LEVEL` | string | O | `warning` | |
| `EMQX_AUTH__HTTP__AUTH_REQ` | URL | R | — | `http://api:8000/internal/mqtt/auth` |
| `EMQX_AUTH__HTTP__SUPER_REQ` | URL | O | unset | Disable; no super users. |
| `EMQX_ACL__HTTP__ACL_REQ` | URL | R | — | Same endpoint, ACL action. |

Custom config file mounts handle TLS certs, rate limits, plugin enablement.

### 3.9 `nats` (NATS server with JetStream)

Configured via `nats.conf` mounted in container. Env minimums:

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `NATS_USER` | string | R | — | Default admin (rotate). |
| `NATS_PASSWORD` | string | R | — | |
| Per-service users defined in `nats.conf`: `api-user`, `ingest-user`, `worker-user`, `realtime-user`, `ai-user`, `scheduler-user`. | | | | |

### 3.10 `postgres`

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `POSTGRES_USER` | string | R | — | Superuser. Migrations only. |
| `POSTGRES_PASSWORD` | string | R | — | |
| `POSTGRES_DB` | string | O | `yourplatform` | |
| Application users (per service: `api`, `ingest`, `worker`, etc.) created via init script with minimal grants. | | | | |

### 3.11 `redis` (Valkey)

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `REDIS_PASSWORD` | string | R | — | Set via `--requirepass` in launch command. |
| `REDIS_MAXMEMORY` | string | O | `512mb` | |
| `REDIS_MAXMEMORY_POLICY` | string | O | `allkeys-lru` | |

### 3.12 `minio`

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `MINIO_ROOT_USER` | string | R | — | Admin. Used to create per-service keys at first boot. |
| `MINIO_ROOT_PASSWORD` | string | R | — | |
| `MINIO_BROWSER` | bool | O | `off` (prod) | Disable web console in prod, or restrict by IP. |

### 3.13 `caddy`

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `CADDY_DOMAIN` | string | R | — | e.g. `<host>` |
| `CADDY_EMAIL` | email | R | — | Let's Encrypt account email. |

`Caddyfile` mounted; templated with environment.

### 3.14 `chirpstack` (Phase 3)

Config files mounted; env wires DB and Redis only:

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `POSTGRES_DSN_CHIRPSTACK` | DSN | R | — | Separate DB user with own schema. |
| `REDIS_URL_CHIRPSTACK` | URL | R | — | |
| `MQTT_BROKER_URL_INTERNAL` | URL | R | — | EMQX internal user for ChirpStack uplinks/downlinks. |
| `LORA_KEY_KEK` | string ≥32 | R | — | Encryption key for AppKeys at rest. |

### 3.15 `edge-agent` (Phase 4) — installed on customer hardware

| Variable | Type | R/O | Default | Description |
|---|---|---|---|---|
| `YP_DEVICE_TOKEN` | string | R | — | Token from platform. |
| `YP_BACKEND_URL` | URL | O | `https://api.<host>` | |
| `YP_LOCAL_DB_PATH` | path | O | `/var/lib/yp-agent/buffer.db` | SQLite buffer. |
| `YP_BUFFER_MAX_BYTES` | int | O | `536870912` (512 MB) | |
| `YP_LOCAL_API_PORT` | int | O | `9090` | Local status server. |
| `YP_RULES_LOCAL_PATH` | path | O | `/etc/yp-agent/rules.yaml` | Local rule definitions. |

---

## 4. Feature Flags

Centralised in `packages/flags/` (Python) and `packages/flags-ts/` (TS), with the same source of truth (`flags.toml`).

Format:
```toml
[ai_dashboard_builder]
default = false
description = "Enables natural-language dashboard builder UI"
phase = 2
owner = "founder"

[lora_devices]
default = false
phase = 3

[multi_user_projects]
default = false
phase = 3

[mobile_pwa]
default = false
phase = 4

[billing_enabled]
default = false
phase = 5
```

Loaded at boot. Per-environment overrides via `FEATURE_FLAGS=ai_dashboard_builder=true,lora_devices=true`.

Per-org overrides (Phase 3+) stored in DB (`organizations.feature_flags JSONB`).

Code reads via:
```python
from yourplatform.flags import flags
if flags.is_enabled("ai_dashboard_builder", org_id=org.id):
    ...
```

---

## 5. Local Development Defaults

`apps/<service>/.env.example` shipped. Root `.env.example` covers `docker-compose.dev.yml`:

```bash
# === Shared ===
ENVIRONMENT=dev
LOG_LEVEL=debug
LOG_FORMAT=console

# === api ===
HOST=0.0.0.0
PORT=8000
POSTGRES_DSN=postgresql+asyncpg://yp:yp@postgres:5432/yourplatform
REDIS_URL=redis://:devpassword@redis:6379/0
NATS_URL=nats://api-user:devpassword@nats:4222
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=devkey
MINIO_SECRET_KEY=devsecret
JWT_SECRET=local-development-jwt-secret-change-me-32chars
EMAIL_FROM_ADDRESS=noreply@localhost
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
WEB_APP_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
MQTT_PUBLIC_HOST=localhost
CORS_ORIGINS=http://localhost:3000
INTERNAL_API_TOKEN=dev-internal-token-change-me

# === postgres / redis / minio passwords ===
POSTGRES_USER=yp
POSTGRES_PASSWORD=yp
POSTGRES_DB=yourplatform
REDIS_PASSWORD=devpassword
MINIO_ROOT_USER=devkey
MINIO_ROOT_PASSWORD=devsecret

# === Optional: AI ===
LLM_PROVIDER=ollama
LLM_BASE_URL=http://ollama:11434

# === Web ===
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_REALTIME_URL=ws://localhost:8002
NEXT_PUBLIC_BRAND_NAME=yourplatform
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=local-development-nextauth-secret-32chars
```

Mailpit replaces real SMTP for local — surfaces sent emails in a UI.

---

## 6. Production Checklist

Before going live, verify in your `.env.production` (or secrets manager) that:

- [ ] All `R` (required) vars set
- [ ] `ENVIRONMENT=prod`
- [ ] All passwords/secrets ≥32 random chars and unique
- [ ] No defaults like `change-me` left in
- [ ] `JWT_SECRET` rotated from any dev value
- [ ] `INTERNAL_API_TOKEN` rotated
- [ ] `WEB_APP_BASE_URL` and `API_BASE_URL` set to real HTTPS URLs
- [ ] `MQTT_PUBLIC_HOST` resolves publicly
- [ ] `SMTP_*` configured against real provider
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` and `SENTRY_DSN` configured for observability
- [ ] `EMQX_DASHBOARD__DEFAULT_PASSWORD` strong (or dashboard disabled)
- [ ] `MINIO_BROWSER=off`
- [ ] `LOG_LEVEL=info` (not debug)
- [ ] `LOG_FORMAT=json`
- [ ] Backup credentials configured (separate from app DB user)
- [ ] DNS for all subdomains (`app.`, `api.`, `mqtt.`, `realtime.`, `docs.`) pointing correctly
- [ ] Caddy automatic HTTPS confirmed working

---

## 7. Schema Validation

Each service has a `settings.py`:

```python
from pydantic import Field, PostgresDsn, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class APISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    environment: str = Field(pattern=r"^(dev|staging|prod)$")
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error|critical)$")
    log_format: str = Field(default="json", pattern=r"^(json|console)$")
    
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    
    postgres_dsn: PostgresDsn
    redis_url: str
    nats_url: str
    
    jwt_secret: str = Field(min_length=32)
    jwt_access_ttl_seconds: int = Field(default=900, ge=60, le=86400)
    
    cors_origins: list[str]
    
    # ... etc
```

The settings class is instantiated once at boot. If validation fails, Pydantic raises with field-by-field errors. Boot script catches and prints.

```python
# main.py
try:
    settings = APISettings()
except ValidationError as e:
    print("Invalid configuration:", file=sys.stderr)
    for err in e.errors():
        print(f"  {'.'.join(str(p) for p in err['loc'])}: {err['msg']}", file=sys.stderr)
    sys.exit(2)
```

This guarantees: services that boot have valid config; misconfiguration is caught at deploy time, not 3 AM.
