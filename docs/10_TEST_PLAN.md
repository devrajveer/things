# Test Plan

The testing contract. What is tested, where, how, by whom, and what counts as "done." **Every PR that adds production code must add or update tests per this document.**

> Cross-references: [05_CODING_STANDARDS §3.x] for test conventions per language; [07_DATA_CONTRACTS] for fixtures; [09_SECURITY_SPEC §3.4] for cross-tenant test sweep.

---

## Table of contents

- §1 Testing pyramid and philosophy
- §2 Test taxonomy
- §3 Per-service test strategy
- §4 Test environments
- §5 Test data and fixtures
- §6 Coverage targets and quality gates
- §7 CI pipeline
- §8 Manual / exploratory testing
- §9 Performance and load testing
- §10 Security testing
- §11 Regression and canary testing

---

## 1. Testing Pyramid and Philosophy

```
              /\
             /e2\         5%   — full stack, real browser
            /----\
           /  in  \      20%   — service + real DB / NATS / Redis
          /  teg   \
         /----------\
        /    unit    \   75%   — pure functions, isolated
       /--------------\
```

### Principles

1. **Tests are documentation.** Test name = behavior spec. A failing test must explain what's broken without reading the implementation.
2. **Test behavior, not implementation.** Refactoring should not require rewriting tests.
3. **Fakes over mocks.** A real in-memory implementation of a port is preferable to `Mock()`. Mocks brittle; fakes catch contract drift.
4. **Slow tests are bugs.** A test that takes >1s without a real reason gets fixed.
5. **Flaky tests are bugs.** A flaky test is quarantined within 24h or fixed within 1 week.
6. **Domain layer has no I/O in tests.** If a domain test needs a database, the boundary is wrong.

---

## 2. Test Taxonomy

### 2.1 Unit tests

- **Scope:** a single function or class in isolation.
- **Allowed dependencies:** stdlib only (in domain), or fakes (in application).
- **Speed budget:** <10 ms per test.
- **Located:** `tests/unit/` mirroring `src/` structure.
- **Run on:** every PR, every commit, pre-commit (optional).

### 2.2 Integration tests

- **Scope:** one service slice, real infrastructure (DB, NATS, Redis) via `testcontainers`.
- **Allowed dependencies:** real postgres, redis, nats, minio. External APIs (LLM, email) faked.
- **Speed budget:** <2 s per test, <5 min suite per service.
- **Located:** `tests/integration/`.
- **Run on:** every PR.

### 2.3 Contract tests

- **Scope:** validates that producer/consumer of an API or event conform to the schema in [07_DATA_CONTRACTS].
- **API contract:** OpenAPI spec used as oracle; client SDKs and server endpoints generated and tested against it.
- **Event contract:** JSON Schema for each event; producer test asserts published payload validates; consumer test asserts the consumer accepts golden payloads.
- **Located:** `tests/contract/`.
- **Run on:** every PR.

### 2.4 End-to-end (E2E) tests

- **Scope:** a real user flow via the web app or CLI, against a fully-booted environment.
- **Tool:** Playwright for web; pytest scripts for CLI/SDK.
- **Speed budget:** <30 s per test, <10 min suite.
- **Located:** `tests/e2e/`.
- **Run on:** main branch + nightly.

### 2.5 Performance tests

- **Scope:** specific endpoints or message paths under load.
- **Tool:** `k6` for HTTP/WebSocket; `mqtt-bench` for MQTT.
- **Located:** `tests/perf/` with scripts.
- **Run on:** nightly + before each release.
- **Pass criteria:** stays within budgets in [06_PRD §2 NFR-1].

### 2.6 Security tests

- **Static:** `bandit` (Python), `eslint-plugin-security` (TS), Trivy (containers), `gitleaks` (secrets).
- **Dynamic:** OWASP ZAP baseline against staging weekly.
- **Cross-tenant sweep:** integration test that, for every authenticated endpoint, attempts cross-tenant access.
- **Auth fuzzing:** Hypothesis tests against auth endpoints with malformed inputs.
- **Run on:** PR (static), nightly (dynamic), pre-release (full).

### 2.7 Migration tests

- **Scope:** every Alembic migration is dry-run on a snapshot of staging data.
- **Tool:** custom `pytest` fixture that loads the snapshot, applies migration, asserts outcome.
- **Run on:** PR that touches migrations.

### 2.8 Smoke tests

- **Scope:** "is the deploy alive?" — hits `/healthz`, `/readyz`, performs one read and one write.
- **Tool:** simple bash + curl, run from CI on each environment.
- **Run on:** post-deploy.

---

## 3. Per-Service Test Strategy

### 3.1 `api`

**Unit:**
- Domain: every entity invariant, every value object, every domain service.
- Application: every use case with at least: happy path, not-found, forbidden, validation failure, idempotency.
- Pure helpers in `interfaces/http/`: ID validators, query parsers.

**Integration:**
- One test file per `interfaces/http/v1/<resource>.py`.
- For each endpoint: 200 path, 401, 403, 404, 422, idempotency-key behavior.
- Database: `testcontainers-postgres` per session; `pytest-postgresql` per test (transactional rollback).
- NATS: `testcontainers-nats`. Tests verify events fired with expected schema.

**Contract:**
- `tests/contract/test_openapi.py`: load OpenAPI spec, validate every endpoint's responses with `schemathesis`.
- Client SDK uses generated types; test that one round-trip works.

**Cross-tenant sweep:**
- `tests/integration/test_cross_tenant_isolation.py` — generated from endpoint registry.

### 3.2 `ingest`

**Unit:**
- Payload parsers (JSON, CBOR, CayenneLPP, custom decoder runner).
- Validation rules.
- Reserved-key check.

**Integration:**
- HTTP path: full stack, post a payload, assert NATS event published.
- MQTT path: publish to local broker, assert NATS event published.
- Backpressure: send burst beyond rate limit, assert rejection.

### 3.3 `realtime`

**Unit:**
- Subscription matcher (filters → message routing).

**Integration:**
- Open WebSocket, subscribe, publish to NATS, assert message arrives.
- Auth failure on connect.
- Backpressure: slow consumer triggers drop + warning.

### 3.4 `worker`

**Unit:**
- Rule evaluator (pure function; many cases).
- Window aggregation.
- Debounce logic.
- Webhook signing.

**Integration:**
- Datapoint → rule fires → NATS alert event → email queued → fake SMTP receives.
- Webhook flow with fake HTTP receiver verifying signature.

### 3.5 `ai-worker` (Phase 2)

**Unit:**
- Tool schemas; tool-call validation.
- Proposal validators (must conform to dashboard/rule spec).

**Integration:**
- Recorded LLM provider responses (using `vcrpy`-style replay).
- End-to-end proposal generation with stub LLM.

### 3.6 `web`

**Unit (component):**
- React Testing Library: each `<Widget*>`, `<DataTable>`, `<RuleBuilder>` etc.
- For interactive components: render → user-event → assert state.

**Integration:**
- Mock Service Worker (msw) intercepts API calls.
- Page-level tests: render page, await data, interact, assert.

**E2E (Playwright):**
- See [§3.7].

### 3.7 E2E suite (`tests/e2e/`)

Critical user flows tested every release:

| ID | Flow | Steps |
|---|---|---|
| E1 | Signup to first datapoint | Sign up → verify email → device add → copy snippet → curl publish → see latest value on device page |
| E2 | Dashboard create | Login → new dashboard → add line widget → configure → save → see live update |
| E3 | Rule + alert | Create rule → trigger via curl → alert fires → email received (fake SMTP) → ack → resolve |
| E4 | API key usage | Create API key → use it via curl → revoke → confirm 401 |
| E5 | Password reset | Request reset → email received → reset → login with new password |
| E6 | Cross-tenant 404 | Login as A → try B's URL → 404 |
| E7 | MQTT publish | Add device → mosquitto_pub with credentials → see datapoint in UI |

### 3.8 SDK tests

**Python SDK:**
- Unit tests for parameter validation, retry logic, signing.
- Integration tests against a running `api` (in CI: brought up via docker-compose).
- Examples folder runs as part of CI (with cleanup).

**JS SDK:**
- Same shape.

**Arduino SDK:**
- Native unit tests via `unity` framework for protocol logic that doesn't need hardware.
- ESP32 hardware-in-loop test (manual / nightly): an ESP32 wired to USB publishes to a CI runner.

### 3.9 CLI

- Unit tests for argument parsing.
- Integration: each command run against a test instance, output asserted.

---

## 4. Test Environments

### 4.1 Local

- Developer's laptop.
- `docker-compose.test.yml` brings up minimal deps: postgres, redis, nats.
- `make test-unit`, `make test-integration` shortcuts.

### 4.2 CI

- GitHub Actions on every push.
- Matrix: Python 3.12, Node 20.
- Services brought up per-job via `services:` block (postgres, redis, nats).
- Larger fixtures cached.

### 4.3 Staging

- Identical to prod but smaller.
- Auto-deployed on `main` merge.
- E2E tests run after deploy.
- Performance tests run nightly here.

### 4.4 Production

- Smoke tests post-deploy.
- Synthetic monitoring (Uptime Kuma) every 60s.
- No destructive tests.

---

## 5. Test Data and Fixtures

### 5.1 Factories

`factory-boy` for Python; manual builder objects for TS.

```python
# tests/factories/devices.py
class DeviceFactory(factory.Factory):
    class Meta:
        model = Device

    id = factory.LazyFunction(lambda: f"dev_{ulid.new()}")
    project_id = factory.SubFactory(ProjectFactory).id
    name = factory.Sequence(lambda n: f"device-{n}")
    status = "active"
```

### 5.2 Builders for use cases

```python
# tests/builders.py
def a_device(**overrides) -> Device:
    return DeviceFactory(**overrides)

def a_rule_for_temperature(threshold: float = -15) -> Rule:
    return RuleFactory(spec={...})
```

### 5.3 Golden files

For complex outputs (e.g., serialized API responses), use golden file comparison.
- Stored under `tests/golden/`.
- Updated only on intentional changes via `pytest --update-golden`.

### 5.4 Time control

Tests must not depend on wall-clock. Inject a `Clock` port.

```python
class Clock(Protocol):
    def now(self) -> datetime: ...

class FakeClock:
    def __init__(self, t: datetime): self._t = t
    def now(self) -> datetime: return self._t
    def advance(self, td: timedelta) -> None: self._t += td
```

### 5.5 Random seed

All tests using random data set a seed. Repeatable failures.

---

## 6. Coverage Targets and Quality Gates

### 6.1 Coverage targets

| Layer | Target | Hard floor (CI fail below) |
|---|---|---|
| Domain | 95% | 90% |
| Application | 85% | 75% |
| Infrastructure | 70% | 60% |
| Interfaces | 70% | 60% |
| Web components | 70% | 50% |
| Total project | 80% | 70% |

### 6.2 Branch coverage

Required ≥ line coverage − 10%. Catches missing else paths.

### 6.3 Mutation testing (Phase 2+)

- `mutmut` weekly on domain layer.
- Mutation score target: 80%.

### 6.4 What "covered" doesn't mean

Coverage ≠ correctness. Reviewer must check that tests *assert* meaningful things, not just exercise lines.

### 6.5 Quality gates (PR cannot merge without)

- All tests pass on CI.
- Coverage ≥ floors.
- No new lint errors.
- No new mypy errors.
- No new high/critical security findings.
- All flaky-quarantined tests reviewed within their grace period.

---

## 7. CI Pipeline

### 7.1 GitHub Actions workflow structure

```yaml
.github/workflows/
  ci.yml              # PR + push to main
  nightly.yml         # full suite + perf + dynamic security
  release.yml         # on tag, build + publish + deploy
  scheduled-scans.yml # weekly Trivy + pip-audit + npm audit
```

### 7.2 PR workflow stages

```
[ Lint ]──parallel──[ Type check ]──parallel──[ Unit tests ]
   │                      │                         │
   └──────────┬───────────┴─────────────────────────┘
              ▼
       [ Build images ]
              │
       [ Integration tests (per service) ]
              │
       [ Contract tests ]
              │
       [ Web tests (jest + RTL) ]
              │
       [ E2E tests (against ephemeral env) ]   ← only on main, slow
              │
       [ Coverage report ]
              │
        [ All green → mergeable ]
```

### 7.3 Speed targets

- Unit + lint + types: <5 min.
- Full PR pipeline (without E2E): <15 min.
- E2E: <20 min.
- Total: <30 min PR lead time.

### 7.4 Failure handling

- Single test failure: PR blocked.
- Flaky failure: triggers re-run once. Two failures = blocked, requires investigation.
- Infra failure (e.g., docker pull rate limit): re-run by maintainer.

---

## 8. Manual / Exploratory Testing

### 8.1 Pre-release manual checklist

Before any tagged release, founder runs (60-min checklist, documented in `docs/release-checklist.md`):

- Sign up + verify email
- Create device + connect from each SDK + see data
- Create dashboard with each widget type
- Create rule + trigger + receive alert (email + webhook)
- API key full lifecycle
- Mobile responsive sanity check
- Self-host fresh install on an Ubuntu VM

### 8.2 Bug-bash days (Phase 5)

Once per quarter, dedicated session for finding edge cases.

---

## 9. Performance and Load Testing

### 9.1 Tools

- HTTP: `k6`.
- WebSocket: `k6` with WS extension.
- MQTT: `mqtt-bench` or custom Go script.

### 9.2 Test scenarios

| Scenario | Target |
|---|---|
| `S1` Steady ingest | 500 msg/s sustained for 30 min, p95 latency < 1.5 s end-to-end |
| `S2` Burst ingest | 5,000 msg/s for 30 s, no rejections, no data loss |
| `S3` Concurrent dashboards | 100 concurrent WebSocket clients viewing live, p95 fan-out < 500 ms |
| `S4` API browse | 200 RPS GET endpoints for 5 min, p95 < 500 ms |
| `S5` Rule storm | 1,000 rules + 500 msg/s, all rules evaluated within budget |
| `S6` Series query (cold) | 50 concurrent queries over 30-day windows, p95 < 2 s |
| `S7` Series query (cached) | Repeated queries, p95 < 50 ms (cache hit) |
| `S8` MQTT connect storm | 5,000 connections in 60 s, all accepted |

### 9.3 Schedule

- Nightly: S1, S4, S7.
- Pre-release: full suite.

### 9.4 Regression detection

- Results stored in time-series.
- Alerts on regression > 10% from previous baseline.

---

## 10. Security Testing

### 10.1 Static analysis

| Tool | Frequency | Action |
|---|---|---|
| `bandit` (Python) | Every PR | Block on high |
| `eslint-plugin-security` | Every PR | Block on errors |
| `gitleaks` | Pre-commit + PR | Block on any |
| `trivy` (container scan) | On image build | Block on high CVE in base image |
| `pip-audit` / `pnpm audit` | Weekly + PR | Issue created on high |

### 10.2 Dynamic analysis

- OWASP ZAP baseline scan against staging, weekly.
- Reports reviewed within 7 days.

### 10.3 Specific test sweeps

| Sweep | What |
|---|---|
| Cross-tenant | Every authenticated endpoint, attempt access to another tenant's resource |
| Auth fuzz | All auth endpoints with malformed bodies (Hypothesis) |
| ID prefix mismatch | Every `:resource_id` path, send wrong-prefix ID, expect `invalid_id_format` |
| SSRF webhook | Webhook URL validation: deny-list IPs, metadata endpoints, redirects to deny-list |
| Rate limit | Every endpoint with declared rate limit, confirm enforcement |
| Argon2 timing | Password verification time within expected envelope (no timing leak) |

### 10.4 Penetration testing

Phase 5: external pen test annually. Reports inform threat model.

---

## 11. Regression and Canary Testing

### 11.1 Regression test creation

Every reproducible bug fix must include a test that:
1. Fails on the broken code.
2. Passes after the fix.
3. Is named after the bug (e.g., `test_bug_142_inactivity_rule_fires_on_first_datapoint`).

### 11.2 Canary deploys (Phase 5)

- New version deployed to 5% of traffic for 30 min.
- Auto-rollback on: error rate > baseline + 1%, latency > baseline + 50%.

### 11.3 Synthetic monitoring

Probes from Uptime Kuma every 60s on:
- `https://app.<host>` (HTML 200)
- `https://api.<host>/v1/health` (JSON 200, status=ok)
- WebSocket connect to `wss://<host>/v1/realtime` with synthetic auth
- HTTP ingest with synthetic device → assert datapoint visible within 5 s

Alerting on 3 consecutive failures.
