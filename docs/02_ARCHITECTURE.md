# IoT Platform — Architecture & Codebase Blueprint

*A deep-dive companion to the strategic blueprint. This document locks in the architecture so it never needs a rewrite — only extensions.*

---

## Table of Contents

1. [Architectural Principles (Non-Negotiable)](#1-architectural-principles-non-negotiable)
2. [The Big Picture — System Context Diagram](#2-the-big-picture--system-context-diagram)
3. [Container Diagram — Runtime Services](#3-container-diagram--runtime-services)
4. [Data Flow Diagram — End-to-End](#4-data-flow-diagram--end-to-end)
5. [Deployment Diagram](#5-deployment-diagram)
6. [Internal Layered Architecture (Clean / Hexagonal)](#6-internal-layered-architecture-clean--hexagonal)
7. [Monorepo Structure — Complete Folder Layout](#7-monorepo-structure--complete-folder-layout)
8. [Per-Service Internal Architecture](#8-per-service-internal-architecture)
9. [Event & Message Contracts](#9-event--message-contracts)
10. [Database Schema & Data Model](#10-database-schema--data-model)
11. [API Design & Versioning](#11-api-design--versioning)
12. [Scaling Strategy — How Each Layer Grows](#12-scaling-strategy--how-each-layer-grows)
13. [Security Architecture](#13-security-architecture)
14. [Observability Architecture](#14-observability-architecture)
15. [Testing Strategy by Layer](#15-testing-strategy-by-layer)
16. [CI/CD Pipeline](#16-cicd-pipeline)
17. [Configuration & Secrets](#17-configuration--secrets)
18. [Golden Rules — Do Not Violate](#18-golden-rules--do-not-violate)

---

## 1. Architectural Principles (Non-Negotiable)

Eight rules that keep the codebase sane for the next five years. Violating any of them compounds pain.

1. **Modular monolith first, microservices only when pain forces it.** One repo, clear module boundaries, 3–4 deployable processes. Splitting a module into its own service later is a packaging change, not a rewrite — *if* module boundaries are respected.

2. **Clean architecture inside every service.** Four layers: `domain` (pure business logic, no I/O), `application` (use cases orchestrating domain), `infrastructure` (DB, MQTT, HTTP clients), `interfaces` (HTTP handlers, CLI, message consumers). Inner layers never import outer layers.

3. **Event-driven backbone.** All cross-module communication goes through NATS JetStream. Never have module A call module B's function directly. This is what makes future splitting trivial.

4. **Ports & adapters for every external dependency.** Your domain never knows it's using Postgres, MQTT, or Ollama. It talks to a `TimeseriesRepository` interface. Swap the adapter, domain doesn't flinch.

5. **Schema-driven contracts.** Every API, every event, every external integration has a schema (Pydantic, JSON Schema, Protobuf). Nothing ships untyped. Breaking changes bump a version number.

6. **Feature flags from day one.** Ship dark. Roll out gradually. Unleash (OSS) handles this. Never `if user.id == 42`.

7. **Tenancy is a first-class concept.** Every table has `project_id`. Every query is filtered by it. Every event carries it. You add multi-tenant features in Phase 3 without a migration nightmare.

8. **Twelve-factor everything.** Config via env vars, stateless processes, logs to stdout, dependencies explicit in manifests, dev/prod parity through Docker.

---

## 2. The Big Picture — System Context Diagram

This is the outermost view: who/what talks to your platform.

```
                              ┌─────────────────────────────────┐
                              │      EXTERNAL ACTORS            │
                              └─────────────────────────────────┘

    ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
    │  End User    │          │  Developer   │         │   Admin      │
    │ (dashboards) │          │  (SDK/CLI)   │         │  (platform)  │
    └──────┬───────┘          └──────┬───────┘         └──────┬───────┘
           │ HTTPS                   │ HTTPS/CLI              │ HTTPS
           │                         │                        │
    ┌──────▼─────────────────────────▼────────────────────────▼──────┐
    │                                                                │
    │                     YOUR IoT PLATFORM                          │
    │                   (everything inside §3)                       │
    │                                                                │
    └─┬─────────────────┬──────────────┬──────────────┬──────────────┘
      │ MQTT/HTTPS      │ LoRaWAN      │ Webhooks     │ OIDC/SSO
      │                 │              │ (outbound)   │ (optional)
      │                 │              │              │
┌─────▼─────┐    ┌──────▼──────┐  ┌────▼────────┐  ┌─▼─────────────┐
│   IoT     │    │  LoRaWAN    │  │ 3rd Party   │  │  Identity     │
│ Devices   │    │  Gateways   │  │  Services   │  │  Providers    │
│           │    │             │  │             │  │               │
│ ESP32/    │    │ Dragino/    │  │ Slack/      │  │ Authentik/    │
│ Pi/MCU    │    │ RAK/Browan  │  │ Discord/    │  │ Keycloak/     │
│           │    │             │  │ PagerDuty/  │  │ Google/       │
└───────────┘    └─────────────┘  │ Webhooks/   │  │ GitHub        │
                                  │ Node-RED/   │  └───────────────┘
                                  │ Home Asst.  │
                                  └─────────────┘
                                         ▲
                                         │ outbound only
                                   ┌─────┴──────┐
                                   │  LLM API   │
                                   │ (optional  │
                                   │   BYO key) │
                                   └────────────┘
```

**Key invariants:**
- Devices **only** speak MQTT or HTTPS inbound. No other protocols on the device-facing edge.
- LLM is **optional**. Self-hosters can run without it. Cloud users can BYO key or use bundled Ollama.
- External webhooks are **outbound only** from your platform.
- All inbound traffic terminates at the reverse proxy (Caddy).

---

## 3. Container Diagram — Runtime Services

The zoomed-in view of everything running inside your platform. Each box is a deployable container/process.

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                           YOUR IoT PLATFORM (one region)                          ║
║                                                                                   ║
║  ┌──────────────────────── EDGE / INGRESS LAYER ─────────────────────────────┐    ║
║  │                                                                            │    ║
║  │  ┌──────────┐          ┌──────────────┐         ┌───────────────────┐     │    ║
║  │  │  Caddy   │          │  EMQX MQTT   │         │  ChirpStack       │     │    ║
║  │  │ (HTTPS   │          │   Broker     │         │ (LoRaWAN NS+AS)   │     │    ║
║  │  │  + ACME) │          │ :1883/:8883  │         │  :8080 mgmt       │     │    ║
║  │  │  :443    │          │ :8083 WS     │         │  UDP :1700 gw     │     │    ║
║  │  └────┬─────┘          └──────┬───────┘         └─────────┬─────────┘     │    ║
║  │       │                       │                           │               │    ║
║  └───────┼───────────────────────┼───────────────────────────┼───────────────┘    ║
║          │                       │                           │                    ║
║  ┌───────┼───────────────────────┼───────────────────────────┼───────────────┐    ║
║  │       │     APPLICATION LAYER │                           │               │    ║
║  │       ▼                       ▼                           ▼               │    ║
║  │  ┌─────────┐            ┌──────────┐               ┌─────────────┐        │    ║
║  │  │   web   │            │ realtime │               │   ingest    │        │    ║
║  │  │(Next.js)│            │ (Node+WS)│               │ (Py/async)  │        │    ║
║  │  │  :3000  │            │  :3001   │               │   :8001     │        │    ║
║  │  └────┬────┘            └────┬─────┘               └──────┬──────┘        │    ║
║  │       │                      │                            │               │    ║
║  │       │ BFF calls            │ WS subs                    │ publishes     │    ║
║  │       ▼                      │                            │ events        │    ║
║  │  ┌───────────────────────────┴────────────────────────────┴───────────┐   │    ║
║  │  │                                                                    │   │    ║
║  │  │                      api (FastAPI)  :8000                          │   │    ║
║  │  │                                                                    │   │    ║
║  │  │  REST v1  +  OpenAPI  +  internal admin  +  webhook receivers      │   │    ║
║  │  └────┬─────────────────────────────────┬───────────────────────┬─────┘   │    ║
║  │       │                                 │                       │         │    ║
║  │       │ enqueue jobs                    │                       │         │    ║
║  │       ▼                                 │                       │         │    ║
║  │  ┌──────────────┐    ┌──────────────┐   │   ┌──────────────┐    │         │    ║
║  │  │   worker     │    │ ai-worker    │   │   │  scheduler   │    │         │    ║
║  │  │ (Dramatiq)   │    │ (LangGraph)  │   │   │ (APScheduler)│    │         │    ║
║  │  │              │    │              │   │   │              │    │         │    ║
║  │  │ alerts,      │    │ anomaly,     │   │   │ retention,   │    │         │    ║
║  │  │ webhooks,    │    │ embeddings,  │   │   │ aggregates,  │    │         │    ║
║  │  │ exports      │    │ agents, RAG  │   │   │ health checks│    │         │    ║
║  │  └──────┬───────┘    └──────┬───────┘   │   └──────┬───────┘    │         │    ║
║  │         │                   │           │          │            │         │    ║
║  └─────────┼───────────────────┼───────────┼──────────┼────────────┼─────────┘    ║
║            │                   │           │          │            │              ║
║  ┌─────────┼───────────────────┼───────────┼──────────┼────────────┼─────────┐    ║
║  │         │       MESSAGING / STATE LAYER             │                          │    ║
║  │         ▼                   ▼           ▼          ▼            ▼         │    ║
║  │  ┌──────────────────────────────────────────────────────────────────┐     │    ║
║  │  │              NATS JetStream  :4222    (internal event bus)       │     │    ║
║  │  │                                                                   │     │    ║
║  │  │   Streams: telemetry.*  alerts.*  rules.*  ai.*  audit.*         │     │    ║
║  │  └──────────────────────────────────────────────────────────────────┘     │    ║
║  │                                                                            │    ║
║  │  ┌──────────┐         ┌──────────────┐       ┌────────────────────┐       │    ║
║  │  │  Redis   │         │  PostgreSQL  │       │  MinIO (S3 API)    │       │    ║
║  │  │ (Valkey) │         │  + Timescale │       │                    │       │    ║
║  │  │          │         │  + pgvector  │       │  firmware blobs,   │       │    ║
║  │  │ cache,   │         │              │       │  exports, backups, │       │    ║
║  │  │ rate lim,│         │ OLTP +       │       │  AI models         │       │    ║
║  │  │ sessions │         │ timeseries + │       │                    │       │    ║
║  │  │          │         │ vectors      │       │                    │       │    ║
║  │  └──────────┘         └──────────────┘       └────────────────────┘       │    ║
║  └────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                   ║
║  ┌────────────────────────── OBSERVABILITY STACK ─────────────────────────────┐   ║
║  │                                                                             │   ║
║  │  ┌──────────┐   ┌────────┐   ┌────────┐   ┌─────────┐   ┌───────────┐      │   ║
║  │  │Prometheus│   │  Loki  │   │ Tempo  │   │ Grafana │   │ GlitchTip │      │   ║
║  │  │(metrics) │   │ (logs) │   │(traces)│   │   (UI)  │   │ (errors)  │      │   ║
║  │  └──────────┘   └────────┘   └────────┘   └─────────┘   └───────────┘      │   ║
║  └─────────────────────────────────────────────────────────────────────────────┘   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
```

**Services overview:**

| Service | Runtime | Purpose | Scales How |
|---|---|---|---|
| `caddy` | Caddy | TLS termination, reverse proxy, static files | Vertical + HA pair |
| `web` | Next.js (Node) | Frontend SSR + static | Horizontal |
| `api` | FastAPI (Python) | REST, OpenAPI, admin, webhook receivers | Horizontal |
| `realtime` | Node + uWS | WebSocket fan-out for live dashboards | Horizontal (sticky) |
| `ingest` | Python async | High-throughput data ingestion | Horizontal |
| `worker` | Dramatiq | General background jobs | Horizontal by queue |
| `ai-worker` | Python + LangGraph | LLM agents, embeddings, anomaly | Horizontal (GPU-aware) |
| `scheduler` | APScheduler | Cron-like jobs (retention, aggregates) | Singleton + leader-elect |
| `emqx` | EMQX | MQTT broker | Cluster |
| `chirpstack` | ChirpStack | LoRaWAN NS + AS | Cluster (Phase 3) |
| `nats` | NATS | Event bus | Cluster (3+ nodes) |
| `postgres` | PG + Timescale + pgvector | All structured data | Vertical → read replicas → partitioning |
| `redis` | Valkey | Cache, sessions, rate limits | Primary + replicas |
| `minio` | MinIO | Object storage | Distributed cluster |

---

## 4. Data Flow Diagram — End-to-End

This is the single most important diagram in the document. It shows **exactly** how one piece of data flows from a device to a user's dashboard.

```
┌──────────────┐
│  IoT Device  │
│   (ESP32)    │
└──────┬───────┘
       │ MQTT PUBLISH
       │ topic: v1/{proj}/{dev}/up
       │ payload: {"temp":23.5,"hum":58}
       ▼
┌──────────────────────────────────────────────┐
│              EMQX MQTT Broker                │
│                                              │
│  1. ACL check → HTTP auth to api service     │
│     (cached 5min)                            │
│  2. Validates client credentials              │
│  3. Republishes to internal subject           │
└──────┬───────────────────────────────────────┘
       │ Bridge rule: MQTT → NATS
       │ NATS subject: ingest.raw.{proj}
       ▼
┌──────────────────────────────────────────────┐
│          ingest service (Python)             │
│                                              │
│  1. Parse payload (JSON / CBOR / CayenneLPP) │
│  2. Schema validate against device profile   │
│  3. Enrich: attach project_id, device_id,    │
│     received_at, source (mqtt/http/lora)     │
│  4. Rate-limit check (Redis)                 │
│  5. Publish normalized event to NATS         │
└──────┬───────────────────────────────────────┘
       │ NATS subject: telemetry.{proj}
       │ JetStream: persisted, replayable
       │
       │ FAN-OUT to 4 consumers (parallel):
       │
       ├─────────────────┬──────────────────┬──────────────────┐
       ▼                 ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
│ ts-writer   │  │ rule-engine  │  │ realtime    │  │  ai-worker   │
│ (worker)    │  │  (worker)    │  │ (Node WS)   │  │              │
│             │  │              │  │             │  │              │
│ batch 1s,   │  │ evaluates    │  │ filters per │  │ anomaly      │
│ COPY into   │  │ active rules,│  │ subscribed  │  │ score,       │
│ hypertable  │  │ emits        │  │ dashboard,  │  │ embedding,   │
│             │  │ alert events │  │ pushes WS   │  │ index        │
└──────┬──────┘  └──────┬───────┘  └──────┬──────┘  └──────┬───────┘
       │                │                 │                │
       ▼                ▼                 ▼                ▼
┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌──────────────┐
│ Postgres │    │ NATS:        │    │ Browser │    │ Postgres     │
│ Timescale│    │ alerts.*     │    │ (user)  │    │ (pgvector,   │
│ hyper-   │    │              │    │         │    │  anomaly tbl)│
│ table    │    └──────┬───────┘    └─────────┘    └──────────────┘
└──────────┘           │
                       ▼
                ┌──────────────┐
                │ notification │
                │   worker     │
                │              │
                │ email/slack/ │
                │ webhook      │
                └──────────────┘
```

**Query (read) path:**

```
┌─────────┐
│ Browser │
└────┬────┘
     │ GET /v1/projects/{p}/series?device=&key=&from=&to=&agg=&bucket=
     ▼
┌─────────────────────────────────────────────────────┐
│                    api service                      │
│                                                     │
│  1. Authn (JWT) + Authz (project membership)        │
│  2. Rate limit (Redis)                              │
│  3. Cache lookup (Redis, query-hash key, 10s TTL)   │
│  4. If miss: pick best continuous aggregate         │
│     for requested resolution                        │
│  5. SELECT ... FROM telemetry_{bucket} WHERE ...    │
│  6. Serialize, cache, return                        │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
                ┌────────────┐
                │ Postgres / │
                │ Timescale  │
                └────────────┘
```

**Live subscription path:**

```
┌─────────┐                           ┌──────────────┐
│ Browser │ ◄── WSS ──────────────────│   realtime   │
└────┬────┘                           │   (Node WS)  │
     │                                └──────▲───────┘
     │ 1. Connect wss://.../live             │
     │ 2. Send {subscribe: {project, ...}}   │ subscribes to NATS
     │ 3. Receives filtered datapoints       │ telemetry.{proj}
     │                                       │
     │                                 ┌─────┴──────┐
     │                                 │    NATS    │
     │                                 └────────────┘
```

---

## 5. Deployment Diagram

How it physically runs in production. This layout supports your first 5,000 paying customers on ~€200–€400/mo infra. Scale-up path noted.

```
                          ┌────────────────────────────────┐
                          │       Cloudflare               │
                          │  (DNS, CDN, DDoS, WAF)         │
                          └──────────────┬─────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
         ┌──────────▼──────────┐    ┌────▼──────┐    ┌────────▼────────┐
         │  Hetzner EU-1       │    │ Hetzner   │    │  Hetzner EU-2   │
         │  (primary region)   │    │ Object    │    │  (DR/replica)   │
         │                     │    │ Storage   │    │                 │
         │  K3s cluster        │    │ (backups) │    │  Warm standby   │
         │   - 3× CX32 control │    └───────────┘    │  (Phase 4+)     │
         │   - 3× CX42 worker  │                     └─────────────────┘
         │   - 1× CCX33 DB     │
         │     (dedicated CPU, │
         │      NVMe, backup)  │
         └─────────────────────┘


Inside the K3s cluster (single-region view):

┌────────────────────────────────────────────────────────────────────┐
│  Namespace: ingress                                                │
│  ┌────────────┐   ┌────────────┐                                   │
│  │ caddy-0    │   │ caddy-1    │   (2 replicas, HA)                │
│  └────────────┘   └────────────┘                                   │
├────────────────────────────────────────────────────────────────────┤
│  Namespace: platform                                               │
│  Deployments (each 2+ replicas for HA):                            │
│  ┌─────┐ ┌─────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │ web │ │ api │ │realtime │ │ ingest │ │ worker │ │ ai-worker  │  │
│  └─────┘ └─────┘ └─────────┘ └────────┘ └────────┘ └────────────┘  │
│                                                                    │
│  Singleton (leader-elected):                                       │
│  ┌───────────┐                                                     │
│  │ scheduler │                                                     │
│  └───────────┘                                                     │
├────────────────────────────────────────────────────────────────────┤
│  Namespace: iot                                                    │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ emqx cluster │  │ chirpstack   │  (Phase 3)                     │
│  │ 3 replicas   │  │ + redis-ls   │                                │
│  └──────────────┘  └──────────────┘                                │
├────────────────────────────────────────────────────────────────────┤
│  Namespace: data                                                   │
│  StatefulSets (persistent volumes):                                │
│  ┌──────────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐            │
│  │ postgres-0   │  │ redis-0 │  │ nats-0  │  │minio-0 │            │
│  │ (primary)    │  │         │  │ nats-1  │  │minio-1 │            │
│  │ postgres-1   │  │ redis-1 │  │ nats-2  │  │minio-2 │            │
│  │ (replica)    │  │(replica)│  │(cluster)│  │minio-3 │            │
│  └──────────────┘  └─────────┘  └─────────┘  └────────┘            │
├────────────────────────────────────────────────────────────────────┤
│  Namespace: observability                                          │
│  ┌──────────┐ ┌──────┐ ┌───────┐ ┌────────┐ ┌──────────┐           │
│  │Prometheus│ │ Loki │ │ Tempo │ │Grafana │ │GlitchTip │           │
│  └──────────┘ └──────┘ └───────┘ └────────┘ └──────────┘           │
└────────────────────────────────────────────────────────────────────┘
```

**Scaling path:**
- Start: 3 small VPS nodes (~€60/mo total)
- 1k users: 5 nodes (~€150/mo)
- 5k users: 8 nodes + dedicated DB box (~€400/mo)
- 20k users: split ingest + AI to their own node pool, add PG read replicas (~€1.5k/mo)
- 100k+ users: multi-region active-active with geo-DNS (~€8k+/mo)

---

## 6. Internal Layered Architecture (Clean / Hexagonal)

Every service (api, ingest, worker, ai-worker) follows the same four-layer pattern. **This is the single most important rule for code that survives growth.**

```
         ┌──────────────────────────────────────────────────┐
         │           INTERFACES LAYER (outermost)           │
         │                                                  │
         │  FastAPI routers   CLI commands   NATS consumers │
         │  WebSocket handlers   Webhook receivers           │
         │                                                  │
         │  - Parse input, validate shape                   │
         │  - Call application layer                        │
         │  - Serialize output                              │
         │  - ZERO business logic here                      │
         └──────────────┬───────────────────────────────────┘
                        │ calls into
                        ▼
         ┌──────────────────────────────────────────────────┐
         │            APPLICATION LAYER                     │
         │                                                  │
         │  Use cases / services that orchestrate           │
         │                                                  │
         │  - CreateDeviceUseCase                           │
         │  - IngestTelemetryUseCase                        │
         │  - EvaluateRulesUseCase                          │
         │  - GenerateDashboardUseCase                      │
         │                                                  │
         │  Depends on: domain + port interfaces            │
         │  NEVER on concrete infrastructure                │
         └──────────────┬───────────────────────────────────┘
                        │ uses
                        ▼
         ┌──────────────────────────────────────────────────┐
         │            DOMAIN LAYER (innermost)              │
         │                                                  │
         │  Pure business logic. No I/O. No frameworks.     │
         │                                                  │
         │  - Entities: Device, Project, Rule, Stream       │
         │  - Value Objects: DeviceToken, Threshold         │
         │  - Domain Services: RuleEvaluator                │
         │  - Events: TelemetryReceived, RuleFired          │
         │  - Repository Interfaces (ports)                 │
         │                                                  │
         │  Testable with zero mocks or infrastructure      │
         └──────────────────────────────────────────────────┘
                        ▲
                        │ implements repo interfaces
                        │
         ┌──────────────┴───────────────────────────────────┐
         │          INFRASTRUCTURE LAYER                    │
         │                                                  │
         │  Concrete adapters for external systems          │
         │                                                  │
         │  - PostgresTelemetryRepository                   │
         │  - NatsEventBus                                  │
         │  - OllamaLlmClient                               │
         │  - EmqxMqttClient                                │
         │  - RedisCache                                    │
         │                                                  │
         │  Depends on external libs (SQLAlchemy, httpx…)   │
         └──────────────────────────────────────────────────┘
```

**Dependency rule (inviolable):**
```
interfaces ──────► application ──────► domain ◄────── infrastructure
                                         ▲
                                         │
                                  (pointing inward)
```

Domain knows nothing. Application knows domain + port interfaces. Infrastructure implements those interfaces. Interfaces (HTTP etc.) call application.

**Why this matters:**
- Business logic is testable without a database.
- Swap Postgres for CockroachDB? Write a new repo adapter, domain unchanged.
- Swap Ollama for vLLM? New adapter.
- Extract a module into a microservice? Move its domain + application + infra into a new service; the interfaces (NATS consumers, HTTP routes) are what's new.

---

## 7. Monorepo Structure — Complete Folder Layout

Below is the complete directory layout. Every folder has a single purpose. Every file has a home.

```
yourplatform/
│
├── README.md                          # Project overview, badges, links
├── CONTRIBUTING.md                    # How to contribute
├── LICENSE                            # AGPL-3.0
├── CODE_OF_CONDUCT.md
├── SECURITY.md                        # Vulnerability disclosure
├── CHANGELOG.md                       # Auto-generated by semantic-release
├── .editorconfig
├── .gitignore
├── .gitattributes
├── .pre-commit-config.yaml            # Ruff, mypy, eslint, prettier hooks
├── .nvmrc                             # Node version pin
├── .python-version                    # Python version pin
├── pnpm-workspace.yaml                # JS workspaces config
├── package.json                       # Root-level scripts only
├── Makefile                           # `make dev`, `make test`, etc.
├── turbo.json                         # TurboRepo for JS build orchestration
│
├── apps/                              # ─── User-facing surfaces (web, cli, docs) ───
│   │
│   ├── web/                           # Next.js frontend (App Router)
│   │   ├── app/                       # Route segments
│   │   │   ├── (marketing)/           # Public pages (landing, pricing, docs)
│   │   │   ├── (auth)/                # login, signup, magic-link
│   │   │   ├── (app)/                 # Authenticated app
│   │   │   │   ├── projects/
│   │   │   │   ├── devices/
│   │   │   │   ├── dashboards/
│   │   │   │   ├── rules/
│   │   │   │   ├── alerts/
│   │   │   │   ├── insights/          # AI chat
│   │   │   │   └── settings/
│   │   │   ├── api/                   # Next.js route handlers (BFF only)
│   │   │   └── layout.tsx
│   │   ├── components/                # React components
│   │   │   ├── ui/                    # shadcn primitives
│   │   │   ├── charts/                # ECharts wrappers
│   │   │   ├── widgets/               # Dashboard widgets
│   │   │   ├── forms/
│   │   │   └── layout/
│   │   ├── lib/                       # Client utilities
│   │   │   ├── api-client.ts          # Typed wrapper around REST API
│   │   │   ├── ws-client.ts           # WebSocket client
│   │   │   ├── auth.ts
│   │   │   └── hooks/
│   │   ├── styles/
│   │   ├── public/
│   │   ├── tests/                     # Playwright E2E
│   │   ├── next.config.mjs
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── cli/                           # `yp` command-line tool (Python Typer)
│   │   ├── src/yp_cli/
│   │   │   ├── __main__.py
│   │   │   ├── main.py
│   │   │   └── commands/
│   │   │       ├── project.py
│   │   │       ├── device.py
│   │   │       ├── logs.py
│   │   │       └── deploy.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── docs/                          # Astro Starlight documentation site
│       ├── src/content/docs/
│       ├── astro.config.mjs
│       └── package.json
│
├── services/                          # ─── Backend services (deployable processes) ───
│   │
│   ├── _shared/                       # Shared Python base package (yp_shared)
│   │   ├── src/yp_shared/             # logging, settings, errors, ids, time, nats, db, redis, health
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── api/                           # FastAPI backend (main service)
│   │   ├── src/
│   │   │   └── yp_api/
│   │   │       ├── __init__.py
│   │   │       ├── main.py            # FastAPI app factory
│   │   │       ├── settings.py        # Pydantic Settings (env config)
│   │   │       │
│   │   │       ├── interfaces/        # ── LAYER 1 ──
│   │   │       │   ├── http/
│   │   │       │   │   ├── v1/        # Versioned routers
│   │   │       │   │   │   ├── auth.py
│   │   │       │   │   │   ├── projects.py
│   │   │       │   │   │   ├── devices.py
│   │   │       │   │   │   ├── streams.py
│   │   │       │   │   │   ├── dashboards.py
│   │   │       │   │   │   ├── rules.py
│   │   │       │   │   │   ├── alerts.py
│   │   │       │   │   │   ├── ingest.py
│   │   │       │   │   │   └── ai.py
│   │   │       │   │   ├── internal/  # Not public (MQTT auth, etc.)
│   │   │       │   │   ├── admin/     # Platform admin only
│   │   │       │   │   ├── middleware/
│   │   │       │   │   ├── dependencies.py
│   │   │       │   │   ├── errors.py
│   │   │       │   │   └── schemas/   # Request/response Pydantic DTOs
│   │   │       │   ├── cli/           # Typer CLI commands for ops
│   │   │       │   └── events/        # NATS consumers owned by this service
│   │   │       │
│   │   │       ├── application/       # ── LAYER 2 ──
│   │   │       │   ├── auth/
│   │   │       │   │   ├── use_cases/
│   │   │       │   │   └── services.py
│   │   │       │   ├── devices/
│   │   │       │   ├── projects/
│   │   │       │   ├── telemetry/
│   │   │       │   ├── dashboards/
│   │   │       │   ├── rules/
│   │   │       │   ├── alerts/
│   │   │       │   └── ai/
│   │   │       │
│   │   │       ├── domain/            # ── LAYER 3 (pure) ──
│   │   │       │   ├── auth/
│   │   │       │   │   ├── entities.py
│   │   │       │   │   ├── value_objects.py
│   │   │       │   │   └── ports.py   # Repository interfaces (Protocols)
│   │   │       │   ├── devices/
│   │   │       │   ├── projects/
│   │   │       │   ├── telemetry/
│   │   │       │   ├── dashboards/
│   │   │       │   ├── rules/
│   │   │       │   │   ├── entities.py
│   │   │       │   │   ├── evaluator.py   # Pure function
│   │   │       │   │   └── ports.py
│   │   │       │   ├── alerts/
│   │   │       │   ├── ai/
│   │   │       │   └── shared/
│   │   │       │       ├── events.py      # Domain event base
│   │   │       │       └── types.py       # ProjectId, DeviceId, etc.
│   │   │       │
│   │   │       └── infrastructure/    # ── LAYER 4 ──
│   │   │           ├── db/
│   │   │           │   ├── engine.py
│   │   │           │   ├── models.py      # SQLAlchemy ORM
│   │   │           │   └── repositories/  # Implement domain ports
│   │   │           ├── nats/
│   │   │           │   ├── client.py
│   │   │           │   └── event_bus.py
│   │   │           ├── redis/
│   │   │           │   ├── client.py
│   │   │           │   ├── cache.py
│   │   │           │   └── rate_limiter.py
│   │   │           ├── minio/
│   │   │           ├── email/
│   │   │           ├── mqtt/              # Admin operations on EMQX
│   │   │           ├── llm/
│   │   │           │   ├── ollama_client.py
│   │   │           │   ├── openrouter_client.py
│   │   │           │   └── base.py        # Protocol
│   │   │           └── chirpstack/        # Phase 3
│   │   ├── migrations/                    # Alembic
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   ├── tests/
│   │   │   ├── unit/                      # Pure domain tests
│   │   │   ├── integration/               # With real DB
│   │   │   └── e2e/                       # Full HTTP
│   │   ├── alembic.ini
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── ingest/                        # High-throughput ingestion service
│   │   ├── src/yp_ingest/
│   │   │   ├── main.py
│   │   │   ├── settings.py
│   │   │   ├── interfaces/
│   │   │   │   ├── http.py            # FastAPI, POST /ingest
│   │   │   │   ├── mqtt_bridge.py     # EMQX → NATS
│   │   │   │   └── lora_bridge.py     # ChirpStack → NATS (Phase 3)
│   │   │   ├── application/
│   │   │   │   └── ingest_use_case.py
│   │   │   ├── domain/
│   │   │   │   ├── validators.py
│   │   │   │   ├── enrichers.py
│   │   │   │   └── decoders/          # Payload decoders (JSON, CBOR, CayenneLPP, custom JS)
│   │   │   └── infrastructure/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── realtime/                      # Node WebSocket fan-out
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── server.ts
│   │   │   ├── subscriptions.ts
│   │   │   ├── filters.ts
│   │   │   └── nats.ts
│   │   ├── tests/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   │
│   ├── worker/                        # Dramatiq background worker
│   │   ├── src/yp_worker/
│   │   │   ├── main.py
│   │   │   ├── tasks/
│   │   │   │   ├── alerts.py
│   │   │   │   ├── webhooks.py
│   │   │   │   ├── exports.py
│   │   │   │   ├── retention.py
│   │   │   │   └── ts_writer.py       # Batches NATS → Timescale
│   │   │   └── consumers/             # NATS subscribers
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── ai-worker/                     # AI tasks (isolated for GPU nodes)
│   │   ├── src/yp_ai_worker/
│   │   │   ├── main.py
│   │   │   ├── agents/
│   │   │   │   ├── dashboard_builder.py
│   │   │   │   ├── rule_builder.py
│   │   │   │   ├── insight_console.py
│   │   │   │   └── tools/             # Agent tool functions
│   │   │   ├── anomaly/
│   │   │   │   ├── online.py          # River
│   │   │   │   ├── batch.py           # PyOD
│   │   │   │   └── forecast.py        # Prophet
│   │   │   ├── embeddings/
│   │   │   └── rag/
│   │   ├── prompts/                   # Versioned prompt templates
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── scheduler/                     # Cron-style jobs
│   │   ├── src/yp_scheduler/
│   │   └── Dockerfile
│   │
│   └── edge-agent/                    # Phase 4 — Go binary for gateways/Pi
│       ├── cmd/agent/main.go
│       ├── internal/
│       ├── go.mod
│       └── Dockerfile
│
├── packages/                          # ─── Shared libraries ───
│   │
│   ├── shared-types/                  # JSON schemas + generated TS/Py types
│   │   ├── schemas/                   # Source of truth: JSON Schema files
│   │   │   ├── events/
│   │   │   │   ├── telemetry.v1.json
│   │   │   │   ├── alert.v1.json
│   │   │   │   └── rule-fired.v1.json
│   │   │   ├── api/
│   │   │   └── configs/
│   │   ├── generated/
│   │   │   ├── typescript/
│   │   │   └── python/
│   │   └── scripts/generate.sh
│   │
│   ├── sdk-py/                        # pip install yourplatform
│   │   ├── src/yourplatform/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── mqtt.py
│   │   │   └── http.py
│   │   ├── examples/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── sdk-js/                        # npm install @yourplatform/sdk
│   │   ├── src/
│   │   ├── examples/
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── sdk-arduino/                   # Arduino library (PlatformIO + Arduino IDE)
│   │   ├── src/
│   │   │   ├── YourPlatform.h
│   │   │   └── YourPlatform.cpp
│   │   ├── examples/
│   │   │   ├── ESP32_BasicPublish/
│   │   │   ├── ESP32_WithOTA/
│   │   │   └── ESP8266_DHT11/
│   │   ├── library.properties
│   │   └── library.json
│   │
│   ├── shared-ts/                     # Shared TypeScript utilities (ids, time, errors, api-client, types)
│   │   ├── src/
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── ui-components/                 # Shared React components across apps (if ever)
│   │   └── package.json
│   │
│   └── codecs/                        # LoRaWAN payload decoders library
│       ├── dragino/
│       ├── milesight/
│       └── README.md
│
├── infra/                             # ─── Infrastructure as code ───
│   │
│   ├── docker-compose/
│   │   ├── docker-compose.dev.yml     # Full dev stack
│   │   ├── docker-compose.prod.yml    # Single-host prod (for self-hosters)
│   │   └── .env.example
│   │
│   ├── helm/                          # Helm charts for K8s deploy
│   │   └── yourplatform/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       ├── values.prod.yaml
│   │       └── templates/
│   │
│   ├── kustomize/                     # Alternative to Helm
│   │
│   ├── opentofu/                      # VPS provisioning
│   │   ├── hetzner/
│   │   └── modules/
│   │
│   ├── ansible/                       # Node configuration (non-K8s)
│   │   ├── playbooks/
│   │   └── roles/
│   │
│   └── grafana/                       # Pre-built dashboards (JSON)
│       ├── platform-overview.json
│       ├── ingestion-health.json
│       └── alerts-summary.json
│
├── docs/                              # ─── Documentation site ───
│   ├── next.config.mjs                # Nextra or Fumadocs
│   ├── content/
│   │   ├── introduction/
│   │   ├── quickstarts/
│   │   │   ├── esp32-arduino.mdx
│   │   │   ├── raspberry-pi-python.mdx
│   │   │   ├── lorawan-dragino.mdx
│   │   │   └── nodejs.mdx
│   │   ├── concepts/
│   │   ├── guides/
│   │   ├── api/                       # Auto-generated from OpenAPI
│   │   ├── sdk/
│   │   ├── self-hosting/
│   │   └── adr/                       # Architecture Decision Records
│   └── package.json
│
├── examples/                          # ─── End-to-end runnable examples ───
│   ├── esp32-temperature/
│   ├── raspberry-pi-dashboard/
│   ├── lorawan-agriculture/
│   └── industrial-predictive/
│
├── scripts/                           # ─── Dev / ops scripts ───
│   ├── dev/
│   │   ├── setup.sh
│   │   ├── seed-db.py
│   │   └── reset-db.sh
│   ├── release/
│   │   ├── bump-version.sh
│   │   └── publish-sdks.sh
│   └── ops/
│       ├── backup-db.sh
│       └── restore-db.sh
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                     # Lint, typecheck, test on every PR
│   │   ├── build-images.yml           # Build Docker images on merge to main
│   │   ├── release.yml                # Semantic-release, publishes SDKs
│   │   ├── deploy-staging.yml
│   │   ├── deploy-production.yml
│   │   ├── security-scan.yml          # Weekly dep audit
│   │   └── docs.yml
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
│
└── benchmarks/                        # Load / perf tests
    ├── ingest-load/                   # k6 or locust scripts
    ├── api-load/
    └── results/
```

**Why this structure works:**

- **Three-way top-level split `services/` + `apps/` + `packages/`:**
  - `services/` = backend processes (headless, deployed as containers, written mostly in Python): `api`, `ingest`, `realtime`, `worker`, `ai-worker`, `scheduler`, plus `_shared` base lib. These run as daemons and talk to each other over NATS/HTTP.
  - `apps/` = user-facing surfaces (things a human or external consumer interacts with directly): `web` (Next.js), `cli` (Typer), `docs` (Astro). These are deployed or distributed as end-user artifacts.
  - `packages/` = libraries (consumed by other code, not run standalone): `sdk-py`, `sdk-js`, `sdk-arduino`, `shared-ts`, `shared-types`, `ui-components`, `codecs`. These ship to PyPI, npm, Arduino Library Manager, etc.
  - Clean import boundary: `packages/` can be imported by anyone; `apps/` and `services/` never import from each other; everyone can import from `packages/`. This prevents circular coupling.
- **Clean architecture inside each service:** every service follows the same 4 layers. Onboarding a contributor into `ingest` feels identical to `api`.
- **Schemas first (`packages/shared-types`):** single source of truth. Backend + frontend + SDKs consume generated types. Break the schema → CI catches it everywhere.
- **Infrastructure in-tree:** Helm chart updates ship in the same PR as code. Self-hosters get one-line deploys.
- **Docs in-tree:** docs version-lock with code. Breaking change = doc update in same PR or CI fails.

---

## 8. Per-Service Internal Architecture

### 8.1 `api` service (FastAPI) — the central brain

```
┌────────────────────────────────────────────────────────────┐
│                       api service                          │
│                                                            │
│  HTTP Request                                              │
│       │                                                    │
│       ▼                                                    │
│  ┌─────────────────────────────────────┐                   │
│  │ Middleware chain:                   │                   │
│  │  1. Request ID                      │                   │
│  │  2. OpenTelemetry span              │                   │
│  │  3. Rate limit (Redis)              │                   │
│  │  4. Authentication (JWT/API key)    │                   │
│  │  5. Authorization (project scope)   │                   │
│  │  6. Error handler                   │                   │
│  └──────────────┬──────────────────────┘                   │
│                 ▼                                          │
│  ┌─────────────────────────────────────┐                   │
│  │  interfaces/http/v1/{resource}.py   │                   │
│  │  (FastAPI router)                   │                   │
│  │                                     │                   │
│  │  - Parses path/query/body           │                   │
│  │  - Validates via Pydantic DTO       │                   │
│  │  - Calls use case                   │                   │
│  │  - Serializes response              │                   │
│  └──────────────┬──────────────────────┘                   │
│                 ▼                                          │
│  ┌─────────────────────────────────────┐                   │
│  │  application/{bounded_context}/     │                   │
│  │     use_cases/some_use_case.py      │                   │
│  │                                     │                   │
│  │  class CreateDeviceUseCase:         │                   │
│  │    def __init__(                    │                   │
│  │      self,                          │                   │
│  │      device_repo: DeviceRepo,       │  ← port interface │
│  │      event_bus: EventBus,           │  ← port interface │
│  │    ): ...                           │                   │
│  │    async def execute(cmd): ...      │                   │
│  └──────────────┬──────────────────────┘                   │
│                 │ uses                                     │
│                 ▼                                          │
│  ┌─────────────────────────────────────┐                   │
│  │  domain/{context}/                  │                   │
│  │                                     │                   │
│  │  entities.py (Device, Project)      │                   │
│  │  value_objects.py                   │                   │
│  │  events.py (DeviceCreated)          │                   │
│  │  ports.py (DeviceRepo protocol)     │                   │
│  └──────────────┬──────────────────────┘                   │
│                 │ implemented by                           │
│                 ▼                                          │
│  ┌─────────────────────────────────────┐                   │
│  │  infrastructure/                    │                   │
│  │                                     │                   │
│  │  db/repositories/device_repo.py     │ → Postgres        │
│  │  nats/event_bus.py                  │ → NATS            │
│  │  redis/cache.py                     │ → Redis           │
│  │  email/postal.py                    │ → Postal          │
│  └─────────────────────────────────────┘                   │
└────────────────────────────────────────────────────────────┘

Dependency injection: all wiring in one place (interfaces/http/dependencies.py)
using FastAPI's Depends() + a small container pattern.
```

### 8.2 `ingest` service — the data firehose

```
Two inbound paths:
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  PATH A: HTTP POST /v1/ingest (FastAPI)                    │
│  PATH B: NATS subject ingest.raw.* (from MQTT bridge)      │
│                                                            │
│           │                          │                     │
│           ▼                          ▼                     │
│     ┌──────────────────────────────────────┐               │
│     │      IngestTelemetryUseCase          │               │
│     │                                      │               │
│     │  1. auth() (device token or JWT)     │               │
│     │  2. decode(payload, device.profile)  │  ← decoders   │
│     │  3. validate(datapoint, schema)      │               │
│     │  4. enrich(device, project, time)    │               │
│     │  5. rate_limit(device_id)            │               │
│     │  6. publish(telemetry.{project})     │  → NATS       │
│     └──────────────────────────────────────┘               │
│                                                            │
│  Zero business logic past this point.                      │
│  Four workers downstream fan out independently.            │
└────────────────────────────────────────────────────────────┘
```

### 8.3 `realtime` service — live dashboard pipe

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Client ◄─── WSS ───┐                                      │
│                     │                                      │
│              ┌──────▼────────┐                             │
│              │  Connection   │                             │
│              │  Manager      │  in-memory map:             │
│              │               │  socket → {subscriptions}   │
│              └──────┬────────┘                             │
│                     │ registers                            │
│                     ▼                                      │
│              ┌───────────────┐                             │
│              │ Subscription  │                             │
│              │ Router        │                             │
│              └──────┬────────┘                             │
│                     │ subscribes                           │
│                     ▼                                      │
│              ┌───────────────┐                             │
│              │ NATS consumer │ ──── telemetry.{proj}       │
│              └──────┬────────┘                             │
│                     │                                      │
│                     │ fan-out filter                       │
│                     ▼                                      │
│              ┌───────────────┐                             │
│              │ Backpressure  │  drop old frames if         │
│              │ Buffer        │  client is slow             │
│              └──────┬────────┘                             │
│                     ▼                                      │
│                  (WSS out)                                 │
│                                                            │
│  Redis pub/sub used across replicas for presence + fanout. │
│  Sticky sessions at Caddy (consistent hashing).            │
└────────────────────────────────────────────────────────────┘
```

### 8.4 `worker` — background jobs

```
Queues (NATS-backed via Dramatiq):
  - default          (webhooks, email)
  - ts-writer        (batched Timescale inserts)
  - rule-engine      (evaluate rules)
  - exports          (CSV/Parquet generation)
  - retention        (scheduled cleanup)

Each task function:
  @dramatiq.actor(queue_name="default", max_retries=3)
  async def send_webhook(url: str, signed_body: bytes):
      ...

Workers are stateless. Scale horizontally per queue.
```

### 8.5 `ai-worker` — LLM and ML isolated

Kept separate because:
- GPU node affinity (different K8s node pool)
- Different scaling characteristics (CPU/GPU heavy, few req/s)
- Different failure modes (LLM timeouts, model loading) shouldn't affect core

```
LangGraph agents as state machines:
  - dashboard_builder_agent
  - rule_builder_agent
  - insight_console_agent

Each agent:
  - Loads prompts from prompts/ (versioned in git)
  - Calls tools (read-only data access)
  - Produces a structured proposal (JSON spec)
  - Proposal goes to api service via NATS request/reply

NEVER lets the agent write directly. Always "propose + human confirm".
```

---

## 9. Event & Message Contracts

Every cross-service communication is schema-versioned. No exceptions.

### NATS subject naming

```
<category>.<resource>.<version>.<project_id>[.<optional_specifier>]

Examples:
  ingest.raw.v1.{project_id}           # pre-validation
  telemetry.datapoint.v1.{project_id}  # validated
  alerts.fired.v1.{project_id}
  alerts.resolved.v1.{project_id}
  rules.changed.v1.{project_id}
  ai.request.v1.{project_id}
  ai.response.v1.{project_id}
  audit.event.v1.{project_id}
  devices.state.v1.{project_id}.{device_id}
```

### Event envelope (every message has this shape)

```json
{
  "schema": "telemetry.datapoint.v1",
  "event_id": "01HXYZ...",          // ULID, globally unique
  "occurred_at": "2025-01-15T10:30:00.123Z",
  "ingested_at": "2025-01-15T10:30:00.567Z",
  "project_id": "prj_...",
  "correlation_id": "req_...",
  "source": "mqtt|http|lora|internal",
  "data": {
    // schema-specific payload
  },
  "metadata": {
    "tenant_tier": "pro",
    "trace_id": "..."
  }
}
```

### Versioning rules (breaking-change policy)

- Additive changes (new optional field) → same version.
- Breaking changes (remove field, change type, rename) → new version (`v2`).
- Old and new versions run side-by-side until all producers migrated.
- Consumers handle unknown schemas by logging + dropping (never crashing).

### Idempotency
- All event handlers use `event_id` for dedup (Redis set, 24h TTL).
- Webhook deliveries use HTTP idempotency keys.

---

## 10. Database Schema & Data Model

Full schema committed as Alembic migrations. This is the initial v1.

### Core tables (OLTP)

```sql
-- Tenants & identity
users                 (id, email, password_hash, name, created_at, ...)
organizations         (id, name, owner_id, tier, created_at)
organization_members  (org_id, user_id, role)
projects              (id, org_id, name, slug, created_at, deleted_at)
project_members       (project_id, user_id, role)
api_keys              (id, project_id, hashed_secret, scopes, expires_at, revoked_at)

-- Devices
device_profiles       (id, project_id, name, decoder_js, schema_json)
devices               (id, project_id, profile_id, name, labels, last_seen, status)
device_credentials    (device_id, hashed_token, mqtt_username)
device_downlinks      (id, device_id, payload, scheduled_at, status)

-- Streams (logical data series)
streams               (id, project_id, device_id, key, unit, display_name)
                       UNIQUE (device_id, key)

-- Dashboards
dashboards            (id, project_id, name, layout_json, visibility)
widgets               (id, dashboard_id, type, config_json, position_json)

-- Rules & alerts
rules                 (id, project_id, name, spec_json, enabled, last_fired_at)
alerts                (id, rule_id, project_id, fired_at, payload_json, state)
alert_deliveries      (id, alert_id, channel, status, attempted_at)

-- AI
ai_conversations      (id, project_id, user_id, title, created_at)
ai_messages           (id, conversation_id, role, content, tokens, created_at)
ai_proposals          (id, project_id, user_id, kind, spec_json, applied_at)

-- Embeddings (pgvector)
embeddings            (id, project_id, subject_type, subject_id, vector VECTOR(768), text)
                       INDEX USING hnsw (vector vector_cosine_ops)

-- Audit
audit_events          (id, project_id, actor_id, action, target, data, created_at)

-- Billing (Phase 3+)
subscriptions, invoices, usage_counters
```

### Telemetry (OLAP / time-series)

```sql
-- Hypertable
CREATE TABLE telemetry (
  time         TIMESTAMPTZ      NOT NULL,
  project_id   UUID             NOT NULL,
  device_id    UUID             NOT NULL,
  stream_id    UUID             NOT NULL,   -- denormalized for speed
  key          TEXT             NOT NULL,
  value_num    DOUBLE PRECISION,
  value_bool   BOOLEAN,
  value_str    TEXT,
  value_json   JSONB,
  quality      SMALLINT DEFAULT 0,
  ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

SELECT create_hypertable('telemetry', 'time',
    chunk_time_interval => INTERVAL '1 day',
    partitioning_column => 'project_id',
    number_partitions   => 16);

CREATE INDEX ix_tel_proj_dev_key_time ON telemetry (project_id, device_id, key, time DESC);
CREATE INDEX ix_tel_stream_time       ON telemetry (stream_id, time DESC);

-- Continuous aggregates (downsampled)
CREATE MATERIALIZED VIEW telemetry_1m  WITH (timescaledb.continuous) AS ...;
CREATE MATERIALIZED VIEW telemetry_5m  WITH (timescaledb.continuous) AS ...;
CREATE MATERIALIZED VIEW telemetry_1h  WITH (timescaledb.continuous) AS ...;
CREATE MATERIALIZED VIEW telemetry_1d  WITH (timescaledb.continuous) AS ...;

-- Compression (after 7 days)
ALTER TABLE telemetry SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'project_id, device_id, key'
);
SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- Retention (configurable per tier)
SELECT add_retention_policy('telemetry', INTERVAL '30 days'); -- free tier default
```

### Multi-tenancy enforcement

**Every query must include `project_id`.** Add a thin wrapper in the repo layer that injects `project_id` from the auth context. In Phase 3, add PostgreSQL Row-Level Security policies as defense in depth:

```sql
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
CREATE POLICY devices_project_isolation ON devices
  USING (project_id = current_setting('app.current_project_id')::uuid);
```

Set `app.current_project_id` per-connection in your connection pool middleware.

### Migration strategy
- Alembic, one migration per PR.
- Migrations must be **forward-only** in production. No rollback-in-place — roll forward fixes.
- Every migration tested with real data in staging.
- Long migrations (index creation on hypertables) done with `CONCURRENTLY` and online.

---

## 11. API Design & Versioning

### URL structure

```
https://api.yourplatform.io/v1/projects/{id}/devices
                             ▲                 ▲
                             │                 │
                        major version     resource
```

### Versioning policy
- Major version in URL path (`/v1`, `/v2`).
- Minor/patch changes are backward-compatible only.
- Deprecation: `Deprecation` + `Sunset` HTTP headers, 6-month window minimum.
- Clients identified via `User-Agent` get deprecation warnings logged server-side.

### Response envelope (consistent across all endpoints)

```json
// Success
{
  "data": { ... } | [ ... ],
  "meta": { "page": 1, "total": 42, "request_id": "req_..." }
}

// Error
{
  "error": {
    "code": "device_not_found",
    "message": "Device prj_abc/dev_xyz does not exist",
    "details": { ... },
    "request_id": "req_..."
  }
}
```

### Error code taxonomy
Namespaced machine-readable codes (`device_not_found`, `rate_limited`, `invalid_schema`). Clients switch on these, never on HTTP status alone.

### Pagination
Cursor-based only. No offset pagination (breaks under writes).

```
GET /v1/projects/{id}/devices?limit=50&cursor=eyJpZCI6...
```

### Filtering
Simple query params for common cases. For advanced: a JSON query body on POST endpoints (`/v1/projects/{id}/devices/search`).

### Rate limits
- Per API key: 1000 req/min (free), 10k (pro), 100k (business)
- Ingest: higher limits, per-device enforced
- Returned headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 12. Scaling Strategy — How Each Layer Grows

| Bottleneck | Early signal | Scale move | When |
|---|---|---|---|
| `api` CPU | p95 latency > 300ms | Add more api replicas | 1k+ users |
| `api` DB connections | pool exhaustion | Add PgBouncer | Week 1 (do it early) |
| Postgres OLTP | > 60% CPU | Vertical resize | 5k users |
| Postgres reads slow | query p95 > 200ms | Add read replica, send OLAP queries there | 10k users |
| Telemetry writes lag | JetStream backlog grows | Scale `worker` ts-writer replicas | 2k+ devices |
| MQTT connection count | > 50k | EMQX cluster, sticky LB | 20k+ devices |
| Realtime WS connections | > 10k per node | More realtime replicas + Redis pub/sub | 5k+ users |
| LLM latency/cost | > $100/mo spend | Route cheap queries to Qwen-7B, expensive to 70B | Phase 2 |
| Object storage IOPS | slow exports | Migrate hot prefix to dedicated MinIO pool | 20k+ users |
| Hypertable size | > 1TB | Tiered storage (Timescale: move old chunks to S3) | 10k+ heavy users |

**Split-out milestones** (when modules become microservices):
- `ingest` splits first — easy, pure function, already stateless. At ~5k devices/sec.
- `ai-worker` splits next — already isolated by design.
- `realtime` splits third — sticky-session concerns make it the right candidate.
- `api` stays a monolith longest — splitting it prematurely creates distributed monoliths.

---

## 13. Security Architecture

```
┌────────────────────────────────────────────────────────────┐
│   Defense in depth — each layer is independent             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  EDGE                                                      │
│  ├─ Cloudflare WAF + DDoS                                  │
│  ├─ TLS 1.3 (Caddy, auto-cert)                             │
│  ├─ HSTS, CSP, X-Frame-Options                             │
│  └─ mTLS for LoRaWAN gateway control (Phase 3)             │
│                                                            │
│  IDENTITY                                                  │
│  ├─ Passwords: Argon2id                                    │
│  ├─ Sessions: JWT (short) + refresh (long, rotated)        │
│  ├─ 2FA: TOTP (pyotp), WebAuthn (Phase 3)                  │
│  └─ Magic links: single-use, 15-min expiry                 │
│                                                            │
│  API ACCESS                                                │
│  ├─ API keys: scoped (read-only, write, admin)             │
│  ├─ Device tokens: per-device, revocable                   │
│  ├─ Rate limit: per-IP + per-key                           │
│  └─ Request signing: HMAC for sensitive endpoints          │
│                                                            │
│  DATA                                                      │
│  ├─ Encryption at rest: DB volume-level + MinIO SSE        │
│  ├─ Secrets: Infisical / SOPS, never in env files in git   │
│  ├─ PII: minimize, document in data-map                    │
│  ├─ Row-level security (Phase 3)                           │
│  └─ Backups: encrypted, off-region, restore-tested monthly │
│                                                            │
│  CODE                                                      │
│  ├─ Deps: pip-audit / npm audit in CI weekly               │
│  ├─ SAST: Bandit, Semgrep, CodeQL                          │
│  ├─ Container scan: Trivy                                  │
│  ├─ Signed commits (DCO at minimum)                        │
│  └─ SBOM: Syft, published with each release                │
│                                                            │
│  OPS                                                       │
│  ├─ Audit log for all mutations                            │
│  ├─ Break-glass admin access with alerting                 │
│  ├─ Kubernetes NetworkPolicies (zero-trust between pods)   │
│  └─ bug bounty: SECURITY.md with disclosure policy         │
└────────────────────────────────────────────────────────────┘
```

---

## 14. Observability Architecture

```
Every service emits three signals:

  METRICS (Prometheus)       LOGS (Loki)            TRACES (Tempo)
      │                          │                       │
      │                          │                       │
      │    structlog (py)        │                       │
      │    pino (node)           │  otel SDKs            │
      ▼                          ▼                       ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   Grafana (single pane)                 │
  │                                                         │
  │  Pre-built dashboards (committed as JSON):              │
  │    - platform-overview                                  │
  │    - ingestion-health                                   │
  │    - api-latency                                        │
  │    - business-kpis (signups, DAU, MRR)                  │
  │                                                         │
  │  Alerts (Alertmanager):                                 │
  │    - p95 API latency > 1s for 5min                      │
  │    - ingestion lag > 30s                                │
  │    - any 5xx rate > 1%                                  │
  │    - DB replication lag                                 │
  │    - certificate expiry < 7 days                        │
  └─────────────────────────────────────────────────────────┘
```

**Golden signals tracked for every service:**
- Traffic (req/s)
- Errors (error rate)
- Latency (p50/p95/p99)
- Saturation (CPU, memory, queue depth)

---

## 15. Testing Strategy by Layer

| Layer | Test type | Tool | Coverage target |
|---|---|---|---|
| Domain | Unit, pure | pytest | High (80%+) — cheap, valuable |
| Application use cases | Unit with fakes | pytest + fakes | 70%+ |
| Infrastructure | Integration | pytest + testcontainers | Critical paths |
| HTTP interfaces | Integration | httpx.AsyncClient + test DB | Critical endpoints |
| Cross-service | Contract | Schemathesis + NATS mocks | All event producers/consumers |
| End-to-end | Smoke | Playwright | Login, create device, see datapoint |
| Load | Perf | k6 or locust | Ingest + hot read paths |
| Security | DAST | OWASP ZAP in CI (nightly) | Auth flows |

Fakes over mocks. `FakeDeviceRepository` in-memory beats Mock objects.

---

## 16. CI/CD Pipeline

```
Developer pushes PR
     │
     ▼
┌──────────────────────────────────────┐
│  GitHub Actions: ci.yml              │
│                                      │
│  Parallel jobs:                      │
│   ├─ lint (ruff, eslint)             │
│   ├─ typecheck (mypy, tsc)           │
│   ├─ unit tests (pytest, vitest)     │
│   ├─ integration tests (testcont.)   │
│   ├─ security scan (semgrep, trivy)  │
│   └─ build docker images (cached)    │
└──────────────┬───────────────────────┘
               │ all green
               ▼
        Merge to main
               │
               ▼
┌──────────────────────────────────────┐
│  build-images.yml                    │
│   ├─ tag images: sha + branch        │
│   ├─ push to ghcr.io                 │
│   └─ generate SBOM (Syft)            │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  deploy-staging.yml (auto)           │
│   ├─ helm upgrade on staging K3s     │
│   ├─ run migration check             │
│   ├─ smoke tests against staging     │
│   └─ notify in #deploys channel      │
└──────────────┬───────────────────────┘
               │ approve (manual gate)
               ▼
┌──────────────────────────────────────┐
│  deploy-production.yml               │
│   ├─ canary: 10% of api pods         │
│   ├─ metrics check (5 min)           │
│   ├─ ramp to 100%                    │
│   └─ auto-rollback if SLO breached   │
└──────────────────────────────────────┘
```

SDK publishing via `release.yml`:
- Triggered by `[release]` tag
- semantic-release determines version from commits
- Publishes sdk-py → PyPI, sdk-js → npm, sdk-arduino → PlatformIO + release tag

---

## 17. Configuration & Secrets

**Config philosophy:** one `settings.py` per service using Pydantic Settings. Config loads from env vars. Defaults are development-safe. Production values from Infisical/SOPS.

```python
# services/api/src/yp_api/settings.py
class Settings(BaseSettings):
    environment: Literal["dev", "staging", "prod"] = "dev"
    database_url: PostgresDsn
    redis_url: RedisDsn
    nats_url: str = "nats://nats:4222"
    jwt_secret: SecretStr
    smtp: SmtpSettings
    features: FeatureFlags
    # ...

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
```

**Tier hierarchy (precedence, low → high):**
1. Hardcoded defaults
2. `.env.defaults` (committed)
3. `.env` (gitignored, dev local)
4. OS environment (production)
5. Runtime overrides via admin API (feature flags only, via Unleash)

**Secrets never touch git.** Infisical stores them; deploy pipeline injects them as env vars.

---

## 18. Golden Rules — Do Not Violate

Print these and tape them above your desk.

1. **Never import `infrastructure` from `domain`.** If you do, you've lost the architecture.
2. **Never call another service's function directly from a different bounded context.** Publish an event.
3. **Never query the DB without `project_id` in the filter.** Multi-tenancy depends on it.
4. **Never merge a schema change without a migration.** Alembic migration required per PR.
5. **Never deploy without metrics + logs for the new code.** If you can't see it, you can't run it.
6. **Never let an LLM write to the DB directly.** Always propose + human confirm.
7. **Never block on an LLM call in a user-facing request path.** Stream or queue.
8. **Never commit a secret.** Pre-commit hook enforces it (gitleaks).
9. **Never skip the changelog.** Semantic-release handles this; use conventional commits.
10. **Never ship a feature without a feature flag if it touches critical paths.** Flags are your safety net.

---

## Appendix A — First-Week Setup Commands

```bash
# 1. Scaffold the repo
mkdir yourplatform && cd yourplatform
git init
pnpm init -y
# ... create folder structure from §7

# 2. Bring up dev stack
make dev               # runs docker-compose.dev.yml
# Starts: postgres, timescale, redis, nats, emqx, minio, mailhog

# 3. Run migrations
make migrate

# 4. Seed dev data
make seed

# 5. Start all services in watch mode
make run

# 6. Sanity check
curl http://localhost:8000/health
mosquitto_pub -h localhost -p 1883 -u dev -P dev \
  -t "v1/prj_dev/dev_test/up" -m '{"temp":23.5}'
# should appear in dashboard within 1s
```

## Appendix B — ADR Template (commit to `docs/adr/`)

```
# ADR-NNNN: <Title>

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded by ADR-MMMM

## Context
What problem are we solving? What constraints matter?

## Decision
What did we decide?

## Alternatives considered
1. Option A — pros/cons
2. Option B — pros/cons

## Consequences
What becomes easier? Harder? What do we lock in?
```

Write one per significant choice. Future-you and contributors will thank you.

---

## Summary — Why This Architecture Lasts

Every decision in this document is chosen so that **growth is a matter of adding, not rewriting**:

- **Clean architecture** means feature growth is isolated per bounded context.
- **Event-driven backbone** means any module can become a microservice without touching its code.
- **Schema-versioned contracts** mean client and server can evolve independently.
- **Multi-tenancy from day one** means adding orgs/teams in Phase 3 is a UI and authz change, not a data re-model.
- **Clean separation of `services/`, `apps/`, and `packages/`** means backend internals, user-facing surfaces, and libraries evolve independently — SDKs stay stable while services churn.
- **Observability in-tree** means you can see into production from week one.
- **Feature flags** mean you always have an escape hatch.

Build it in this shape from the first commit. It costs maybe 10–15% more time upfront. It saves 10× more time for the next 5 years.