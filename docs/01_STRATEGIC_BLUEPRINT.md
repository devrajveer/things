# Building an AI-Native IoT Platform — Complete Blueprint

*A solo-developer playbook from MVP to revenue, using only open-source tooling.*

---

## 1. Strategic Positioning — What You're Actually Building

### Brutal market check first

Before scoping features, internalize the landscape. A "ThingSpeak clone" is dead on arrival — the market already has serious open-source players, and you cannot out-feature them as a solo dev.

| Player | Type | Strength | Weakness you exploit |
|---|---|---|---|
| ThingSpeak (MathWorks) | Closed | Brand, MATLAB integration | Stagnant, dated UX, restrictive free tier |
| ThingsBoard | Open source | Mature, full-featured | Dense UX, AI is bolted on, enterprise-feeling |
| Datacake | Closed | Clean UX, low-code | Closed, expensive at scale, no AI depth |
| Ubidots | Closed | Stable | Pricey, dated UI |
| Adafruit IO | Closed | Hobbyist-friendly | No scale path, no LoRa, no AI |
| AWS IoT / Azure IoT | Closed | Power, scale | Complex, expensive, hostile to small teams |
| Blynk | Closed | Mobile-first | Locked-in, limited backend |

**You cannot win on "more features." You win on a wedge.**

### Your wedge (positioning statement)

> **"The open-source, AI-native IoT platform with first-class LoRaWAN — built for developers who ship."**

Three pillars, each defensible:

1. **AI-native, not AI-bolted-on.** Natural-language dashboard creation, AI-generated automation rules, built-in anomaly detection per stream, conversational data exploration ("what changed in the greenhouse last night?"). Incumbents will take 2-3 years to retrofit this because their data models weren't built for it.
2. **LoRaWAN as a first-class citizen.** Most platforms treat LoRa as an afterthought (HTTP webhook in, that's it). You ship: a managed ChirpStack integration, gateway monitoring, device profile library, downlink scheduler with conflict resolution, ADR tuning UI. LoRa is the fastest-growing IoT segment in agriculture, utilities, asset tracking — underserved by current platforms.
3. **Developer-first DX.** Vercel/Supabase quality docs. SDKs that don't suck. CLI that mirrors the dashboard. One-line Docker self-host. Open source from day one.

### Business model: Open Core

- **Self-hosted (free, AGPL-3.0 or Apache-2.0):** full platform, your distribution channel.
- **Managed cloud (paid):** the same code, hosted, with billing, multi-region, backups, SSO, support.
- **Enterprise (paid):** on-prem support contracts, audit logs, advanced RBAC, SLA.

Why this works for a solo dev:
- GitHub stars and self-hosters are your free marketing army.
- Cloud customers pay you to not run infra.
- You don't need a sales team — devs find you, then bring you into their companies.
- Examples that worked: Supabase, PostHog, Plausible, Cal.com, Appwrite.

### Naming
Pick a name that is short (≤8 chars), pronounceable, has `.io` or `.com` available, and isn't trademark-conflicting. Brainstorm directions: "flow," "pulse," "signal," "beacon," "lumen," "veda" themes. Verify on namechk.com, USPTO TESS, and EU IPO before committing. Lock the GitHub org and npm/PyPI namespaces immediately.

---

## 2. Target Users — Who Pays You

### Year 1 wedge (the people who try you first)
- Hardware hobbyists building "serious-ish" projects (paid hobbyists, Hackaday/Hackster types)
- Indie hardware startups (consumer IoT, < 10 people)
- Agriculture/environmental monitoring builders (LoRa users)
- Solo industrial-monitoring consultants serving SMB factories

These users are tolerant of rough edges, give honest feedback, and become your evangelists. They are NOT your revenue source — they're your distribution.

### Year 2 revenue
- SMB industrial monitoring companies (predictive maintenance)
- Solar / energy monitoring installers
- Cold-chain logistics providers
- Smart building / facility management firms
- Agricultural co-operatives running sensor networks

### Avoid until Year 3+
- Fortune 500 enterprise (kills solo devs with procurement, security reviews, custom features)
- Heavy-regulated verticals (medical, aviation) — compliance burden too high
- Government tenders — sales cycle is 18+ months

---

## 3. MVP Feature Scope — What Ships First

The MVP test: **can a developer take an ESP32 from box to live chart in under 10 minutes following the quickstart?** If yes, ship.

### MVP scope (Months 2–4)
1. Auth: email/password + magic link, password reset
2. Single-user projects (no orgs/teams yet)
3. Device registry — create device, generate API key + MQTT credentials
4. Ingestion: HTTPS POST endpoint + MQTT broker (MQTT 3.1.1 + 5.0)
5. Time-series storage with retention policies
6. Dashboard builder with 5 widgets: line chart, gauge, single value, data table, map marker
7. Simple rule engine: threshold-based alerts → email + webhook
8. SDKs in 3 languages: Python, Arduino/ESP32 (C++), Node.js
9. CLI for device + project management
10. Docs site with quickstarts per language

### Explicitly cut from MVP (defer ruthlessly)
- Multi-tenant orgs/teams
- LoRaWAN (Phase 3)
- AI features (Phase 2 — yes, the differentiator comes after the foundation works)
- Mobile app
- Marketplace / template gallery
- White labeling
- Granular RBAC
- GraphQL API
- Plugins system

The temptation to build the AI features first will be enormous. Resist. AI on top of a broken ingest pipeline is a demo, not a product.

---

## 4. Complete System Architecture

### Layered view

```
┌────────────────────────────────────────────────────────────────┐
│  EDGE         devices, gateways, edge agent (Phase 4)          │
├────────────────────────────────────────────────────────────────┤
│  INGEST       MQTT broker · HTTPS endpoint · LoRaWAN bridge    │
├────────────────────────────────────────────────────────────────┤
│  PROCESS      validate · enrich · route · rules · AI pipeline  │
├────────────────────────────────────────────────────────────────┤
│  STORAGE      TimescaleDB · Postgres · Redis · MinIO · pgvector│
├────────────────────────────────────────────────────────────────┤
│  API          REST (FastAPI) · WebSocket (Node) · gRPC (intl)  │
├────────────────────────────────────────────────────────────────┤
│  FRONTEND     Next.js web app · embeddable dashboards          │
├────────────────────────────────────────────────────────────────┤
│  AI           LLM agents · anomaly detect · embeddings · RAG   │
├────────────────────────────────────────────────────────────────┤
│  OBSERVE      Prometheus · Loki · Tempo · Grafana              │
└────────────────────────────────────────────────────────────────┘
```

### Service topology — start as modular monolith

You are one person. **Do not start with microservices.** Start with a modular monolith — one repo, separable logical services, deployed as 3–4 processes:

- `api` — FastAPI public REST API + admin endpoints
- `realtime` — Node.js WebSocket fan-out service for live dashboard updates
- `ingest` — High-throughput data ingestion workers (Python, async)
- `worker` — Background jobs (alerts, retention sweeps, AI tasks) — Dramatiq/Celery

Plus infra services: PostgreSQL/TimescaleDB, EMQX (MQTT broker), Redis, MinIO, NATS (later).

You can split into microservices in Year 2 if a specific service becomes a bottleneck. Until then, monolith = your survival.

### Data flow (end to end)

1. Device publishes JSON to `mqtt://broker/v1/devices/{device_id}/telemetry` or `POST /v1/ingest`.
2. Ingest service authenticates (device token), validates schema, attaches metadata (device_id, project_id, received_at), and writes to a NATS subject `telemetry.{project_id}`.
3. **Three subscribers** consume from NATS in parallel:
   - **TimescaleDB writer** (batched inserts, ~1s window)
   - **Realtime fan-out** (WebSocket push to subscribed dashboards)
   - **Rule engine** (evaluate active rules, trigger alerts)
4. AI pipeline (Phase 2+) subscribes asynchronously for anomaly scoring + embedding generation.
5. Frontend reads historical data via REST (`GET /v1/projects/{id}/series?...`) and live data via WebSocket subscription.

### Why NATS for internal eventing
You don't need Kafka. NATS JetStream gives you persistent streams, easy ops, low memory footprint, and a single binary. If you ever outgrow it, swap to Redpanda (Kafka-compatible). Don't pre-optimize.

### Multi-tenancy strategy
Row-level isolation via `project_id` on every table. Add Postgres Row-Level Security policies in Phase 3. Avoid schema-per-tenant or DB-per-tenant — it kills you operationally as a solo dev.

---

## 5. Complete Open-Source Tech Stack

### Core platform

| Concern | Choice | Why |
|---|---|---|
| Web frontend | **Next.js 15 (App Router) + React 19** | You know it; SSR; great DX |
| UI components | **shadcn/ui + Tailwind** | Own your component code, no lock-in |
| Charts | **Apache ECharts** (primary), Recharts (simple) | ECharts handles huge time-series natively |
| Maps | **MapLibre GL JS** + OpenStreetMap tiles | Truly open, no Mapbox token cost |
| Backend API | **FastAPI** (Python 3.12+) | You know it; great async; Pydantic v2 |
| Realtime | **Node.js + uWebSockets.js** or **Socket.IO** | Better WS perf than Python at scale |
| Background jobs | **Dramatiq** (or Celery) + Redis | Dramatiq is simpler than Celery |
| MQTT broker | **EMQX Open Source** (or VerneMQ) | EMQX scales to millions of connections, free OSS edition |
| Internal eventing | **NATS JetStream** | Single binary, persistent, easy ops |
| Time-series DB | **TimescaleDB** (Postgres extension) | SQL you know + time-series perf, hypertables, continuous aggregates |
| Relational DB | **PostgreSQL 16+** | Same instance as Timescale |
| Vector DB | **pgvector** (in same Postgres) | One DB to operate; fine for your scale |
| Cache / pub-sub | **Redis** (or Valkey, the open fork) | Standard, you know it |
| Object storage | **MinIO** (or Garage) | S3-compatible, self-hosted |
| Search | **Meilisearch** (later, Phase 3) | Lighter than Elasticsearch |
| Auth | **Authentik** (self-hosted IdP) or roll-your-own JWT | Authentik gives SSO/OIDC for free; for MVP, roll your own with FastAPI-Users |

### LoRaWAN stack (Phase 3)

| Concern | Choice |
|---|---|
| Network Server | **ChirpStack v4** — the OSS gold standard |
| Gateway protocol | Semtech UDP packet forwarder (legacy) + Basic Station (modern) |
| Codecs | Repository of JS payload decoders (you'll build a UI library) |

### AI stack (Phase 2)

| Concern | Choice |
|---|---|
| Local LLM serving | **Ollama** (dev) + **vLLM** (production) |
| Models (default) | **Llama 3.3 70B** for quality; **Qwen 2.5 7B / Llama 3.2 3B** for fast/cheap tasks |
| Hosted fallback | OpenRouter or direct provider — let users BYO API key |
| Agent framework | **LangGraph** (state machines for agents) — more controllable than LangChain |
| RAG / vector | pgvector + your own thin retrieval layer (avoid heavy frameworks) |
| Embeddings | **BGE-M3** or **nomic-embed-text** via Ollama/sentence-transformers |
| Anomaly detection | **River** (online ML) for streaming + **Prophet** for forecasting + **PyOD** for batch |
| Edge AI runtime | **ONNX Runtime** (cross-platform) + **TensorFlow Lite Micro** (MCUs) |

### DevOps / infra

| Concern | Choice |
|---|---|
| Containers | Docker + Docker Compose (dev) |
| Orchestration | **K3s** (lightweight Kubernetes) on a few VPS nodes |
| Reverse proxy | **Caddy** (auto-HTTPS) or Traefik |
| CI/CD | GitHub Actions (free tier generous for OSS) |
| Self-host PaaS option | **Coolify** or **Dokploy** (for users who want one-click deploy) |
| IaC | **OpenTofu** (Terraform OSS fork) + **Ansible** for VM config |
| Secrets | **Infisical** (OSS) or SOPS for git-friendly secrets |
| Monitoring | **Prometheus + Grafana** |
| Logs | **Grafana Loki** |
| Traces | **Grafana Tempo** + **OpenTelemetry SDKs** |
| Errors | **GlitchTip** (OSS Sentry alt) or self-hosted Sentry |
| Status page | **Cachet** or **Statping** |
| Email (transactional) | **Postal** (OSS) or **Listmonk** for marketing; SMTP relay via your VPS |
| Docs site | **Nextra** or **Mintlify-style with Fumadocs** |
| Analytics | **Plausible** (self-hosted) or **PostHog** (OSS) |

### Hosting choices (cost-conscious)
- **Hetzner** dedicated/cloud — best price/performance in Europe, 80% cheaper than AWS
- **OVH** for diversity
- **Cloudflare** for DNS, CDN, R2 (egress-free) for static assets and backups
- **Backblaze B2** as backup for object storage

Estimated infra cost for first 1,000 users on managed cloud: **€80–150/month** if you're disciplined.

---

## 6. Phased Roadmap — From Zero to Revenue

Each phase has: **goal · deliverables · exit criteria · estimated time (solo, 30 hrs/week).**

### Phase 0 — Foundation & Validation (Weeks 1–4)

**Goal:** Confirm the wedge is real and lay foundations.

**Do:**
- Talk to 25 potential users in your wedge segments (Reddit r/IOT, r/homeautomation, r/raspberry_pi, Hackaday forums, LoRa Slack/Discords). Don't pitch — ask about their current pain.
- Map 5 specific painful workflows currently done in ThingSpeak/ThingsBoard/spreadsheets.
- Lock name, register `.com` + `.io`, GitHub org, npm/PyPI/crates namespaces.
- Create landing page (Next.js, deploy to Vercel free tier or your own VPS) with email capture + 3-bullet positioning.
- Open source the empty repo with a clear README, roadmap, and CONTRIBUTING.
- Set up monorepo structure, CI skeleton, conventional commits, linters.
- Choose license: **AGPL-3.0** (protects you from cloud vendors strip-mining you) or **Elastic License v2** (more permissive but not OSI-approved). For pure community love, MIT/Apache. **Recommendation: AGPL-3.0** — Grafana, MongoDB (pre-SSPL), and many others use it; permits self-host but blocks competitive cloud forks.

**Exit criteria:** 50+ landing page signups, 3+ users have agreed to pilot the MVP, repo skeleton green in CI.

### Phase 1 — MVP (Weeks 5–18, ~3 months)

**Goal:** End-to-end working platform a developer can self-host.

**Build order (don't deviate):**

**Sprint 1 (week 5–6): Auth + project + device registry**
- FastAPI app skeleton, Postgres + Alembic migrations, Pydantic schemas
- User table, project table, device table
- JWT auth (FastAPI-Users), magic link via Postal
- REST endpoints: signup, login, create project, create device (returns API key + MQTT creds)
- Basic Next.js shell, login flow, project list, device list

**Sprint 2 (week 7–8): Ingestion path**
- Stand up EMQX with auth via HTTP webhook to your API (validates device token)
- HTTPS `POST /v1/ingest` endpoint
- Both paths publish to NATS subject `telemetry.{project_id}`
- TimescaleDB writer worker: subscribes to NATS, batches every 1s, inserts to hypertable `telemetry` (columns: time, device_id, project_id, key, value_num, value_str, value_json)
- Define data model: a "stream" = unique (device_id, key) pair

**Sprint 3 (week 9–10): Read path + first widget**
- Query API: `GET /v1/projects/{id}/series?device=...&key=...&from=...&to=...&agg=avg&bucket=1m`
- Use Timescale's `time_bucket()` and continuous aggregates for performance
- Build line chart widget in Next.js with ECharts
- Realtime: Node WebSocket service subscribes to NATS, pushes to clients filtered by their dashboard subscriptions

**Sprint 4 (week 11–12): Dashboard editor**
- Drag-grid layout (react-grid-layout)
- Add/remove widgets, configure data source per widget
- Save dashboard JSON to Postgres
- Implement remaining 4 widgets: gauge, single value, table, map

**Sprint 5 (week 13–14): Rule engine v1**
- Rules table: name, trigger (stream + threshold + comparator), action (email / webhook)
- Rule evaluator subscribes to NATS, checks active rules per incoming datapoint, debounces (don't spam alerts)
- Email via Postal, webhook via httpx

**Sprint 6 (week 15–16): SDKs + CLI + docs**
- Python SDK (`pip install yourplatform`), publishes via MQTT or HTTP, with simple decorator API
- Arduino library (`#include <YourPlatform.h>`) for ESP32/ESP8266 — wraps PubSubClient
- Node.js SDK (`npm install @yourplatform/sdk`)
- CLI (`yp device create`, `yp project list`, `yp logs tail`) — Typer (Python) or oclif (Node)
- Docs site with: 5-min quickstart per language, concepts, API reference (auto-generated from FastAPI OpenAPI)

**Sprint 7 (week 17–18): Polish + deploy**
- One-line self-host: `docker compose up` works on a fresh Hetzner VPS
- Helm chart for K3s users (later, but stub it)
- Status page, basic analytics
- Pen-test your own auth flows (or use OWASP ZAP)
- Public beta launch

**Exit criteria:** 10 self-hosters confirmed running it, 50+ signups on hosted beta, your 3 pilot users actively using it weekly, < 10 critical bugs open.

### Phase 2 — AI Differentiation (Months 5–7)

**Goal:** Ship the wedge. This is what makes you not-another-IoT-platform.

**Features:**

**1. Natural-language dashboard builder**
- User types: *"Show me temperature trends from greenhouse-1 over the last week, plus humidity, side by side."*
- LangGraph agent with tools: `list_devices`, `list_streams`, `get_sample_data`, `create_widget`, `validate_query`
- Agent emits a dashboard JSON spec; UI renders preview; user accepts/edits.
- Use Llama 3.3 70B via Ollama for self-hosters, OpenRouter (BYO key) for cloud Pro.

**2. AI-generated automation rules**
- User describes: *"Alert me on Slack if any cold-storage sensor stays above -15°C for more than 10 minutes."*
- Agent generates rule JSON (with debounce, scope, action). User reviews and confirms.
- Ship a rule "explain in English" feature too — works both ways.

**3. Built-in anomaly detection per stream**
- Background job: for any stream with > 1000 datapoints, train a River HoeffdingAdaptive model online + Prophet forecast model nightly.
- Anomaly score is a derived stream — visualize it as an overlay on charts.
- Trigger built-in "anomaly" rule type without thresholds.

**4. Chat with your data ("Insight Console")**
- Conversation pane: *"What changed in the past 24 hours?"*, *"Why did the boiler trip on Tuesday?"*
- Agent has tools to query series, fetch logs, retrieve recent alerts, summarize patterns.
- RAG over device metadata, recent alerts, and user-written device notes.

**5. Embedding-based device search**
- Embed device names + descriptions + tags + recent values into pgvector.
- Search: *"sensors near the loading dock"* → returns ranked matches.

**Tech notes:**
- Keep AI optional and modular. Self-hosters can run without it (no Ollama required) — gracefully degrade UI.
- Stream LLM responses to the UI (Server-Sent Events).
- Cache prompt templates as files in repo (versioned), not in DB.
- Build a "tool registry" pattern so adding new agent tools is one file.

**Exit criteria:** Three AI features in production, at least 30% of weekly active cloud users have used at least one, qualitative feedback from 10+ users.

### Phase 3 — LoRaWAN + Multi-Tenant (Months 8–10)

**Goal:** Make it real for businesses with LoRa networks; enable team usage.

**Features:**
- Embed ChirpStack as a service in your stack; proxy its admin API behind your auth.
- LoRaWAN gateway management UI (status, last seen, RSSI heatmap of connected devices).
- Device profile library (codecs for popular sensors: Dragino, Milesight, Browan, Decentlab, Adeunis — JS payload decoders).
- Downlink scheduler with conflict resolution and confirmed-downlink handling.
- ADR (Adaptive Data Rate) tuning UI.
- Organizations + teams + role-based permissions (owner/admin/editor/viewer).
- Project sharing, public dashboard URLs (read-only, optional password).
- Postgres RLS for tenant isolation as a defense-in-depth layer.
- Audit log table.

**Exit criteria:** First paying business customer ($99+/mo). LoRaWAN end-to-end demo works flawlessly with a real Dragino gateway and 3 sensor types.

### Phase 4 — Edge & Advanced (Months 11–13)

**Goal:** Move beyond cloud-only — make the platform work at the edge.

**Features:**
- **Edge agent** (Go binary, < 20 MB) for Raspberry Pi-class devices and gateways:
  - Buffers data when offline
  - Runs local rules
  - Runs ONNX models for on-device anomaly scoring
  - Manages firmware-over-the-air updates for connected MCUs
- **Digital twin builder**: low-code visual canvas where users place sensor positions on a floor plan or P&ID, bind them to streams, get a live "system view."
- **Webhook integration marketplace** (templates for Slack, Discord, Telegram, PagerDuty, IFTTT, Home Assistant, Node-RED).
- **Mobile app**: PWA first (cheaper than React Native), React Native if pull is strong.
- **White-label option** for cloud customers on the Business plan (custom domain, logo, colors).

**Exit criteria:** 10+ paying customers, MRR > €1,500.

### Phase 5 — Monetization & Growth (Months 14–18+)

**Goal:** Compound. Reduce solo dev fragility.

**Do:**
- Hire your first contractor (frontend or DevRel) when MRR > €5k.
- Add billing properly with **Polar.sh** (OSS) or **Lago** (OSS metering) + Stripe.
- Build a public template gallery (community contributes dashboards, codecs, rules).
- Write 1 deep technical post per week (SEO + credibility).
- Launch on Product Hunt, Hacker News (Show HN), DEV.to.
- Apply to YC, Forum Ventures, or bootstrapper-friendly funds — only if you want to scale faster than revenue allows.

**Exit criteria:** Ramen-profitable (MRR > your living costs).

---

## 7. Implementation Details — Patterns That Will Save You

### Data model essentials

Hypertable for telemetry (TimescaleDB):

```sql
CREATE TABLE telemetry (
  time         TIMESTAMPTZ      NOT NULL,
  project_id   UUID             NOT NULL,
  device_id    UUID             NOT NULL,
  key          TEXT             NOT NULL,
  value_num    DOUBLE PRECISION,
  value_str    TEXT,
  value_json   JSONB,
  ingested_at  TIMESTAMPTZ      NOT NULL DEFAULT now()
);
SELECT create_hypertable('telemetry', 'time', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX ON telemetry (project_id, device_id, key, time DESC);

-- Continuous aggregates for fast reads of long ranges
CREATE MATERIALIZED VIEW telemetry_1m
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', time) AS bucket,
       project_id, device_id, key,
       AVG(value_num) AS avg_v, MIN(value_num) AS min_v, MAX(value_num) AS max_v, COUNT(*) AS n
FROM telemetry
GROUP BY bucket, project_id, device_id, key;

SELECT add_continuous_aggregate_policy('telemetry_1m',
  start_offset => INTERVAL '7 days',
  end_offset   => INTERVAL '1 minute',
  schedule_interval => INTERVAL '1 minute');

-- Retention policy (free tier: 30 days; paid: configurable)
SELECT add_retention_policy('telemetry', INTERVAL '30 days');
```

Add `_5m`, `_1h`, `_1d` aggregates as you scale. Read path picks the coarsest aggregate that satisfies the requested resolution.

### MQTT broker authentication

Configure EMQX to call your API on every connection:

```
auth.http.url = http://api:8000/internal/mqtt/auth
auth.http.method = post
auth.http.params = clientid=%c,username=%u,password=%P
```

Your endpoint validates the device token, returns 200 if valid, with topic ACL info. Cache decisions for 5 minutes.

### Device-friendly topic structure

```
v1/{project_id}/{device_id}/up        # device → cloud (telemetry)
v1/{project_id}/{device_id}/down      # cloud → device (commands)
v1/{project_id}/{device_id}/state     # retained, current state
v1/{project_id}/{device_id}/event     # discrete events
```

### Rule engine pattern

Don't roll a DSL. Use JSON spec:

```json
{
  "id": "rule_xyz",
  "name": "Cold storage breach",
  "scope": { "device_tags": ["cold-storage"], "key": "temperature" },
  "trigger": { "type": "threshold", "comparator": ">", "value": -15, "window_s": 600, "aggregation": "all" },
  "actions": [
    { "type": "email", "to": "ops@acme.com" },
    { "type": "webhook", "url": "https://hooks.slack.com/..." }
  ],
  "debounce_s": 1800,
  "enabled": true
}
```

Evaluator is a function: `evaluate(rule, datapoint, recent_state) -> Optional[FiringEvent]`. Easy to test, easy to extend, easy for AI to generate.

### LLM tool design (when you get to Phase 2)

Agent tools should be **small, named clearly, JSON-schema typed**, and idempotent. Examples:

- `list_devices(project_id, tag_filter=None) -> List[Device]`
- `get_recent_values(device_id, key, last_n=100) -> List[Datapoint]`
- `propose_widget(spec) -> WidgetPreview`
- `propose_rule(spec) -> RulePreview`

Always preview, never auto-apply. Human approves before persistence.

### Observability from day one

Even at MVP. Otherwise you'll be flying blind by Phase 2.

- OpenTelemetry SDK in FastAPI, Node, workers
- Trace every HTTP request and NATS message handler
- Prometheus `/metrics` endpoint per service
- Grafana dashboards (commit them to repo as JSON)
- Loki for logs with structured logging (`structlog` in Python, `pino` in Node)

### Testing strategy (solo dev edition)

Don't aim for 90% coverage. Aim for:
- **Smoke tests** end-to-end: ingest → store → query → alert (run in CI on every PR)
- **Critical path unit tests**: auth, rule evaluator, query builder, ingestion validator
- **Migration tests**: every Alembic migration up + down on a real Postgres in CI
- Skip UI tests except for login. Browser tests rot fast.

### Security baseline (don't ship without this)
- Argon2id password hashing
- Rate limit auth endpoints (slowapi)
- HSTS, CSP headers (configure in Caddy)
- All device tokens are random 32-byte URL-safe strings, hashed at rest
- API keys can be revoked individually
- Webhooks signed with HMAC-SHA256
- Run `cargo-audit`/`pip-audit`/`npm audit` in CI weekly
- Subscribe to GHSA advisories for your dependencies

---

## 8. Revenue Model — Concrete Pricing

Open core. Same code, free vs hosted with extras.

| Tier | Price | Includes |
|---|---|---|
| **Self-hosted** | Free (AGPL) | Full platform, BYO infra, BYO LLM, community support |
| **Cloud Free** | $0 | 1 project, 5 devices, 10K msgs/day, 7-day retention, BYO LLM key for AI |
| **Cloud Pro** | **$19/mo** | 5 projects, 50 devices, 1M msgs/day, 30-day retention, AI included (rate-limited) |
| **Cloud Team** | **$99/mo** | 20 projects, 500 devices, 10M msgs/day, 90-day retention, team seats (5), audit log |
| **Cloud Business** | **$499/mo** | Unlimited projects, 5000 devices, 100M msgs/day, 1-year retention, SSO, priority support, 99.9% SLA |
| **Enterprise** | Custom (€10–50k/yr) | On-prem support, dedicated CSM, custom integrations, security review |

**Add-ons:**
- Extra device pack: $X / 100 devices
- Extra retention: $X / month per +90 days
- Premium LoRaWAN device profile pack (community-contributed = free; you curate premium ones)
- Marketplace revenue share (Year 3+): take 20% of paid template/codec sales

**Realistic financial trajectory (conservative):**
- Month 12: 15 paying customers · MRR €600–€1,200
- Month 18: 60 paying customers · MRR €3,000–€6,000 (ramen profitable)
- Month 24: 200 paying customers · MRR €12,000–€20,000 (hire #1)
- Month 36: 600 paying customers + 2 enterprise · MRR €40,000–€70,000

The 95% case is slower. The 5% case is much faster (one viral HN post + Reddit megathread + agriculture co-op deal can compress 6 months into 6 weeks).

---

## 9. Go-to-Market — How Anyone Finds You

You don't have a marketing budget. You have:

### Owned content (long-term compounding)
- **Technical blog**: 1 post/week. Topics: "How we handle a million MQTT connections on one VPS," "Anomaly detection for sensor data: a practical guide," "Building a LoRaWAN payload decoder library." This is your SEO moat.
- **Docs site**: treat as marketing. Quickstarts that work make people stick.
- **YouTube**: screencasts of "ESP32 to dashboard in 10 minutes." Effort is real but pays for years.

### Community channels (where your wedge lives)
- r/IOT, r/homeautomation, r/raspberry_pi, r/embedded
- The Things Network forum (LoRa)
- Hacker News (Show HN at MVP launch, again at AI launch, again at LoRa launch — three free shots)
- DEV.to, Hashnode for cross-posting
- Discord/Slack for your platform, but only after you have ~100 users
- Hackster.io — publish your own tutorials with their hardware

### Partnerships (force multipliers)
- LoRaWAN gateway makers (Dragino, RAK Wireless, Browan): tutorial + listing
- ESP32 board vendors (Espressif, Adafruit, M5Stack)
- LoRa sensor manufacturers — offer free codec hosting
- Home Assistant integration → instant exposure to 1M+ users

### Build in public
- Twitter/X, LinkedIn, Bluesky
- Weekly progress threads
- Real metrics (signups, MRR) — vulnerability builds trust
- Stream coding sessions occasionally

---

## 10. Honest Viability Assessment

### What's working in your favor
- The wedge (AI + LoRa + OSS) is real and underserved.
- Open core has well-trodden playbooks (Supabase, PostHog, Plausible, Cal.com).
- Your existing skill set covers 80% of the stack — minimal learning curve.
- IoT data volumes are growing 25%+ YoY.
- Self-hosting has tailwinds (privacy, sovereignty, EU data residency rules).

### What will hurt
- **18-month time to ramen profitability is realistic, not pessimistic.** Have runway or income strategy.
- **ThingsBoard is a real competitor.** Your AI/LoRa wedge must stay sharp.
- **IoT customers are slow to switch.** Trust and reliability matter more than features.
- **Solo dev burnout is the #1 killer.** Plan rest weeks, not just sprints.
- **Support load grows faster than revenue early on.** Self-hosters will file issues without paying. Be friendly but firm: paid customers get reply SLAs, OSS gets best-effort.
- **Hardware diversity is a tax.** Every MCU/sensor/gateway is a potential support ticket. Document supported hardware tightly.
- **AI inference cost.** If you offer hosted AI, budget for it. BYO-key for free tier mitigates this.

### Key risks and mitigations

| Risk | Mitigation |
|---|---|
| AWS/Azure clones your AI features | AGPL license blocks competitive cloud forks; speed and community are your moat |
| Burnout | Hard cap working hours; one full rest day/week; quarterly 1-week breaks |
| Wedge proves too narrow | Evaluate at month 9; pivot positioning, not stack |
| Big customer demands custom features | Charge enterprise-tier for it or say no; never build one-off for less than €15k |
| Security incident | Bug bounty (free tier credits as reward); responsible disclosure policy; insurance from year 2 |
| Critical dependency abandoned | Audit dependencies quarterly; avoid one-author libraries on critical path |

### Go / no-go gates

- **Month 4 (post-MVP):** if < 5 self-hosters and < 30 cloud beta signups → revisit positioning, don't quit yet but talk to 25 more users
- **Month 9 (post-AI):** if no one is using AI features weekly → AI agents need redesign, not abandonment
- **Month 12:** if MRR < €300 → pivot positioning or go vertical (e.g., agriculture-only)
- **Month 18:** if MRR < €1,500 → consider acquiring a complementary OSS project, partnering, or shifting to consulting+platform model

---

## 11. Solo Developer Survival Kit

- **One-week sprints, public roadmap on GitHub Projects.** Visible progress fights despair.
- **Architecture Decision Records (ADRs)** in `/docs/adr/`. Future-you will forget why you picked NATS over Kafka.
- **Saturday is sacred.** No code. No issues. Walk, read, sleep.
- **Automate ruthlessly.** Renovate-bot for deps, GitHub Actions for releases, semantic-release for changelogs.
- **Ship behind feature flags** (Unleash, OSS) so you can dark-launch.
- **Talk to a user every week**, even when you're "too busy." This keeps the product real.
- **Hire a fractional accountant** by month 6 — you'll have invoices, taxes, possibly VAT MOSS.
- **Mental health > shipping.** A burned-out solo founder ships nothing.

---

## 12. Day-One Checklist (this week)

1. Lock the name. Buy `.com` + `.io`. GitHub org. npm/PyPI namespaces.
2. Write a one-pager positioning statement (use Section 1's wedge, refine in your voice).
3. Post on r/IOT and 2 LoRa forums: "Building an open-source AI-native IoT platform — what's broken with what you use today?" Read every reply.
4. Set up monorepo: `apps/web`, `apps/api`, `apps/realtime`, `apps/ingest`, `apps/worker`, `packages/sdk-py`, `packages/sdk-js`, `packages/sdk-arduino`, `infra/`, `docs/`.
5. Stand up Postgres + TimescaleDB + EMQX + NATS in Docker Compose. Smoke-test: publish MQTT message → see it in Postgres. That's your "hello world."
6. Pick the AGPL-3.0 license, commit it.
7. Open the public roadmap (GitHub Projects) — visible from README.
8. Write the first blog post: "Why I'm building yet another IoT platform." Publish on dev.to and your own site.
9. Email 10 people in your network describing what you're building. Ask for feedback. Make 3 of them future pilot users.
10. Set a weekly demo recording schedule for yourself — even if no one watches at first. It forces shippable progress.

You have everything you need: the skills, the wedge, and now the plan. The hard part is the next 18 months of consistent execution. Start with step 1 today.
