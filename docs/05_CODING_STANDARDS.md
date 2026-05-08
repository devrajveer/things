# Coding Standards

How code is written, organised, formatted, and tested across this project. **Every file an agent writes must conform.** When standards conflict with a generated example, the standard wins.

---

## 1. Universal Principles

1. **Clean architecture is law** ([02_ARCHITECTURE §6]). Domain → Application → Infrastructure → Interfaces. Inner never imports outer.
2. **Multi-tenancy is law** ([04_GLOSSARY §1]). Every query, event, log, and trace carries `project_id`. No exceptions.
3. **All public functions are typed.** Python: type hints + mypy-strict. TypeScript: strict mode, no `any`. Go: standard.
4. **No I/O in domain layer.** Domain functions are pure or nearly so.
5. **Errors are values, not exceptions, in cross-boundary code.** Throw inside, return result types at boundaries.
6. **Tests live next to code, not in a parallel tree** (per language convention below).
7. **Logs are structured.** Every log entry has `event`, `project_id` (where applicable), `request_id`/`trace_id`, plus contextual fields.
8. **Dead code is deleted, not commented out.** Git is the history.
9. **Magic numbers and strings are named constants** in a `constants.py` / `constants.ts` per module.
10. **One module = one bounded context.** Don't cross contexts via direct imports; cross via events ([07_DATA_CONTRACTS §3]).

---

## 2. Repository-Wide Standards

### Git

- **Branch naming:** `feat/<short-desc>`, `fix/<short-desc>`, `chore/<short-desc>`, `docs/<short-desc>`, `refactor/<short-desc>`.
- **Commit messages:** Conventional Commits.
  ```
  feat(api): add device disable endpoint
  fix(ingest): handle CBOR payload over 256 bytes
  chore(deps): bump fastapi to 0.115.0
  docs(prd): clarify Phase 2 anomaly scope
  refactor(domain/rules): extract evaluator pure function
  ```
- **Breaking changes:** `feat!:` or `fix!:` with a `BREAKING CHANGE:` footer.
- **PR title** = top commit message. PR body uses the template in `.github/PULL_REQUEST_TEMPLATE.md`.
- **No direct push to `main`.** All merges via PR with at least one CI green.
- **Squash merge only.** Keeps `main` history linear.
- **DCO sign-off required:** every commit signed with `Signed-off-by:` line.

### Pre-commit hooks (`.pre-commit-config.yaml`)

Runs on every commit, enforced by CI:
- `gitleaks` — block secret commits
- `ruff` — Python lint + format
- `mypy` — Python type check (in CI only, too slow for pre-commit)
- `eslint` + `prettier` — TypeScript
- `gofmt` + `golangci-lint` — Go
- `clang-format` — C++
- `markdownlint` — docs
- `yamllint` — config
- `hadolint` — Dockerfiles

### Files every directory has

- `README.md` if it's a top-level folder under `apps/` or `packages/`
- No empty folders. Use `.gitkeep` only if absolutely needed (avoid).

---

## 3. Python Standards (`api`, `ingest`, `worker`, `ai-worker`, `scheduler`, `sdk-py`, `cli`)

### Versions and tooling

| Tool | Version | Config file |
|---|---|---|
| Python | 3.12 (pin in `.python-version`) | — |
| Package manager | `uv` | `pyproject.toml` + `uv.lock` |
| Formatter | `ruff format` (PEP 8, 100-char lines) | `pyproject.toml` |
| Linter | `ruff check` (rules below) | `pyproject.toml` |
| Type checker | `mypy --strict` | `pyproject.toml` |
| Test runner | `pytest` + `pytest-asyncio` | `pyproject.toml` |
| Test fixtures | `pytest` fixtures + `factory-boy` | — |
| Containers (test) | `testcontainers` | — |

### Ruff config (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
  "E",    # pycodestyle
  "F",    # pyflakes
  "W",    # warnings
  "I",    # isort
  "N",    # pep8-naming
  "B",    # bugbear
  "UP",   # pyupgrade
  "ASYNC",# async-specific
  "S",    # bandit (security)
  "C4",   # comprehensions
  "DTZ",  # datetimez (no naive datetimes)
  "T20",  # no print()
  "RET",  # return statements
  "SIM",  # simplifications
  "ARG",  # unused args
  "PTH",  # prefer pathlib over os.path
  "ERA",  # no commented-out code
  "PL",   # pylint subset
  "TRY",  # try/except patterns
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "PLR2004"]  # asserts ok in tests

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
disallow_untyped_decorators = true
disallow_any_generics = true
warn_unreachable = true
```

### File and module organisation

```
src/<service_name>/
  __init__.py            # version + package-level constants only
  main.py                # entrypoint (FastAPI app factory or worker boot)
  settings.py            # Pydantic Settings; only place env vars are read
  constants.py           # service-wide constants
  exceptions.py          # service-level exception classes
  
  interfaces/            # outermost layer
    http/
      __init__.py
      v1/
        __init__.py
        <resource>.py    # one router per resource
      internal/
      admin/
      middleware/
        __init__.py
        request_id.py
        auth.py
        rate_limit.py
        otel.py
      dependencies.py    # FastAPI Depends() wiring
      errors.py          # error handler registration
      schemas/           # Pydantic DTOs (request/response)
        __init__.py
        <resource>.py
    cli/
      __init__.py
      <command>.py
    events/              # NATS consumers
      __init__.py
      <topic>_consumer.py
  
  application/           # use cases
    <bounded_context>/
      __init__.py
      use_cases/
        __init__.py
        <verb>_<noun>.py   # one file per use case
      services.py        # application-level services (orchestration helpers)
  
  domain/                # pure business logic
    <bounded_context>/
      __init__.py
      entities.py        # dataclasses or Pydantic models, no I/O
      value_objects.py
      events.py          # domain events
      ports.py           # Protocol interfaces (DI ports)
      services.py        # pure domain services
    shared/
      __init__.py
      types.py           # ProjectId, DeviceId, etc.
      events.py          # base DomainEvent
  
  infrastructure/        # adapters
    db/
      engine.py
      session.py
      models.py          # SQLAlchemy ORM mappings
      repositories/
        __init__.py
        <entity>_repository.py   # implements domain port
    nats/
      client.py
      event_bus.py       # implements domain EventBus port
    redis/
      client.py
      cache.py
      rate_limiter.py
    minio/
    email/
    llm/
      base.py            # Protocol
      ollama_client.py
      openrouter_client.py
    chirpstack/          # Phase 3
    mqtt/                # admin operations on EMQX
```

### Imports

- **Absolute imports only**, rooted at the package name.
- Order (auto-arranged by ruff/isort): stdlib → third-party → first-party → local.
- No `from x import *` ever.
- Inside `domain/`, only allowed imports are: stdlib, `pydantic`, `dataclasses`, other `domain.*` modules. Importing from `infrastructure/` or `interfaces/` fails CI.

```python
# Good
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel

from yourplatform.domain.shared.types import ProjectId
from yourplatform.domain.devices.entities import Device

# Bad - never relative imports
from ..entities import Device  # ❌

# Bad - wildcard
from yourplatform.domain.devices import *  # ❌
```

### Naming

| Thing | Convention | Example |
|---|---|---|
| Module file | `snake_case.py` | `device_repository.py` |
| Class | `PascalCase` | `DeviceRepository` |
| Function/method | `snake_case` | `create_device` |
| Variable | `snake_case` | `device_id` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_DEVICES_PER_PROJECT` |
| Private | leading underscore | `_validate_payload` |
| Type alias | `PascalCase` | `DeviceList = list[Device]` |
| Pydantic DTO | suffix with intent | `DeviceCreateRequest`, `DeviceResponse` |
| Use case class | suffix `UseCase` | `CreateDeviceUseCase` |
| Repository port | suffix `Repository` | `DeviceRepository` (Protocol) |
| Repository impl | prefix tech | `PostgresDeviceRepository` |

### Type hints

- **Every public function and method has full type hints**, including return type.
- Use `from __future__ import annotations` at the top of every file.
- Prefer `list[X]`, `dict[K, V]` over `List[X]`, `Dict[K, V]`.
- Use `TypedDict` for structural dicts, `Protocol` for ports.
- Use `Annotated[X, Field(...)]` for Pydantic constraints.
- `None`-returning functions explicitly annotate `-> None`.

```python
from __future__ import annotations

from typing import Protocol

from yourplatform.domain.shared.types import ProjectId, DeviceId
from yourplatform.domain.devices.entities import Device

class DeviceRepository(Protocol):
    async def get(self, project_id: ProjectId, device_id: DeviceId) -> Device | None: ...
    async def list(self, project_id: ProjectId, *, limit: int = 50, cursor: str | None = None) -> tuple[list[Device], str | None]: ...
    async def save(self, device: Device) -> None: ...
```

### Async

- **All I/O is async.** Sync I/O in async functions is a CI failure (detect via `flake8-async`).
- Use `asyncio.TaskGroup` (Python 3.11+) for structured concurrency.
- Never use `asyncio.run()` outside `main.py`.
- Timeouts always set: `async with asyncio.timeout(5.0):`.

### Error handling

Three error categories:

1. **Domain errors:** raised inside `domain/` and `application/`. Custom exception classes inheriting from `DomainError`.
2. **Infrastructure errors:** raised in adapters. Wrap third-party exceptions; never re-raise raw.
3. **HTTP errors:** raised only in `interfaces/http/`. Use `HTTPException` with our standard error code.

```python
# domain/devices/exceptions.py
class DeviceError(DomainError):
    """Base for device errors."""

class DeviceNotFound(DeviceError):
    code = "not_found"

class DeviceDisabled(DeviceError):
    code = "device_disabled"

# application — raises domain errors
async def disable_device(self, cmd: DisableDeviceCommand) -> None:
    device = await self.repo.get(cmd.project_id, cmd.device_id)
    if device is None:
        raise DeviceNotFound(cmd.device_id)
    device.disable()
    await self.repo.save(device)

# interface layer — translates to HTTP
@router.post("/devices/{device_id}/disable")
async def disable_device(...):
    try:
        await use_case.execute(DisableDeviceCommand(...))
    except DeviceNotFound as e:
        raise HTTPException(404, detail=error_payload("not_found", str(e)))
```

The only place an exception turns into an HTTP response is in `interfaces/http/errors.py`, which registers a global handler.

### Logging

- `structlog` configured to emit JSON in prod, console-pretty in dev.
- Bind context once per request:
  ```python
  log = structlog.get_logger().bind(request_id=req_id, project_id=str(project_id))
  log.info("device.created", device_id=str(device.id))
  ```
- **Event names are dotted lowercase verbs:** `device.created`, `ingest.rejected`, `rule.fired`.
- **Never log secrets:** API keys, tokens, passwords, PII beyond email. Add fields to a deny-list in the logger config.
- **Never use `print()`.** Linter blocks it.

### Datetime handling

- All datetimes are timezone-aware UTC: `datetime.now(UTC)`.
- Naive datetimes are a CI failure (`DTZ` rules).
- Compare and store as UTC. Convert to local only at the UI layer.

### Pydantic

- Use Pydantic v2 everywhere.
- Settings class per service in `settings.py`, loaded once at startup, injected via DI.
- API DTOs separate from domain entities. Never return ORM models from endpoints.

### Tests

- Path: `tests/unit/`, `tests/integration/`, `tests/e2e/` parallel to `src/`.
- One test file per source file: `test_<module_name>.py`.
- Naming: `def test_<unit>_<scenario>_<expected>():`
  ```python
  def test_create_device_with_duplicate_name_raises_already_exists(): ...
  ```
- Use **fakes over mocks**. `FakeDeviceRepository(in_memory=True)` beats `Mock()`.
- Fixtures in `conftest.py` per directory level.
- Coverage target: 80%+ on domain, 70%+ on application, critical paths only on interfaces.

### Docstrings

- One-line docstrings for trivial functions.
- Multi-line for complex ones: short summary, blank line, details.
- Use Google style (`Args:`, `Returns:`, `Raises:`).
- Public modules and classes always have docstrings.
- No type info in docstrings (it's in the hints).

```python
async def evaluate_rule(rule: Rule, datapoint: Datapoint, history: RuleHistory) -> RuleEvaluation:
    """Evaluate a rule against a single datapoint.

    Pure function. Does not mutate inputs. Used by the rule engine worker.

    Args:
        rule: The rule definition with trigger spec.
        datapoint: The new telemetry value being checked.
        history: Recent state for rules with time windows.

    Returns:
        A RuleEvaluation indicating whether the rule fires, with optional payload.
    """
```

---

## 4. TypeScript / JavaScript Standards (`web`, `realtime`, `sdk-js`)

### Versions and tooling

| Tool | Version | Config |
|---|---|---|
| Node.js | 20 LTS (pin in `.nvmrc`) | — |
| Package manager | `pnpm` | `pnpm-lock.yaml` |
| TypeScript | 5.x with `strict: true` | `tsconfig.json` |
| Formatter | `prettier` | `.prettierrc` |
| Linter | `eslint` flat config | `eslint.config.mjs` |
| Test runner | `vitest` | `vitest.config.ts` |
| E2E (web only) | `playwright` | `playwright.config.ts` |

### `tsconfig.json` baseline

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "esModuleInterop": true
  }
}
```

### File and module organisation (Next.js `web`)

```
app/
  (marketing)/                  # public pages
  (auth)/                       # login, signup
  (app)/                        # authenticated app
    layout.tsx
    projects/
      page.tsx
      [projectId]/
        layout.tsx
        page.tsx
        devices/page.tsx
        dashboards/page.tsx
        rules/page.tsx
  api/                          # BFF route handlers (only for SSR-side concerns)
components/
  ui/                           # shadcn primitives (vendored)
  charts/                       # ECharts wrappers
  widgets/                      # dashboard widget components
  forms/                        # form components with zod validation
  layout/
lib/
  api-client/                   # generated from OpenAPI
  ws-client.ts
  auth.ts
  hooks/
    use-project.ts
    use-streams.ts
  utils/
styles/
```

### Naming

| Thing | Convention | Example |
|---|---|---|
| File (non-component) | `kebab-case.ts` | `api-client.ts` |
| React component file | `PascalCase.tsx` | `DeviceTable.tsx` |
| Hook file | `use-<name>.ts` | `use-project.ts` |
| Route segment | Next.js convention | `page.tsx`, `layout.tsx` |
| Function | `camelCase` | `createDevice` |
| Component | `PascalCase` | `DeviceTable` |
| Hook | `useCamelCase` | `useProject` |
| Type / Interface | `PascalCase` | `Device`, `DeviceListResponse` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| Boolean prop | `is`/`has`/`can` prefix | `isDisabled`, `hasError` |
| Event handler prop | `on` prefix | `onSubmit`, `onDeviceClick` |

### Imports

- Absolute path imports via `@/` alias (configured in `tsconfig.json`).
- Side-effect imports (e.g., CSS) at the top.
- Auto-grouped by Prettier import sorter:
  1. React and Next
  2. Third-party
  3. `@/components`
  4. `@/lib`
  5. Relative

### React conventions

- **Functional components only.** No class components.
- **Default export is the component**, named exports for sub-components and types.
- **Props always typed**, never `any`.
- **One component per file** unless tightly coupled (e.g., subcomponent only used here).
- **Hooks at the top**, then derived state, then handlers, then render.
- No HTML `<form>` tags inside artifacts; use `onClick` handlers (this is a Claude artifact constraint, not relevant to web app).
- Use `react-hook-form` + `zod` for all forms.
- Use TanStack Query (React Query) for all API state. **Never** raw `fetch` in components.
- All ECharts charts wrapped in a memoized component to prevent re-renders.

```typescript
// good
'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { useProject } from '@/lib/hooks/use-project';

interface DevicePanelProps {
  projectId: string;
  onDeviceClick: (deviceId: string) => void;
}

export default function DevicePanel({ projectId, onDeviceClick }: DevicePanelProps) {
  const { data: devices, isLoading } = useQuery({
    queryKey: ['devices', projectId],
    queryFn: () => apiClient.devices.list(projectId),
  });

  if (isLoading) return <DevicePanelSkeleton />;
  if (!devices?.length) return <DevicePanelEmpty />;

  return (
    <div className="grid grid-cols-3 gap-4">
      {devices.map((device) => (
        <DeviceCard key={device.id} device={device} onClick={onDeviceClick} />
      ))}
    </div>
  );
}
```

### State management

- **Server state:** TanStack Query.
- **URL state:** Next.js search params + `nuqs` library.
- **Local UI state:** `useState`.
- **Cross-component shared state:** Zustand (sparingly; prefer URL or query state).
- **Forms:** react-hook-form.
- **No Redux.**

### CSS

- Tailwind utility classes.
- shadcn/ui components vendored under `components/ui/`. Modify directly, do not wrap unnecessarily.
- Custom CSS only in `styles/globals.css` for Tailwind layer overrides.
- Class lists kept readable with `cn()` utility (clsx + tailwind-merge).

### Error handling

- All async calls wrapped in try/catch or use TanStack Query error states.
- API errors typed via generated OpenAPI client.
- User-facing error UI uses the `<ErrorState>` component (defined in `components/layout/`).

### Tests

- Unit tests next to source: `device-table.test.tsx`.
- Integration tests in `tests/integration/`.
- E2E in `tests/e2e/` using Playwright.
- Component tests use Testing Library, never enzyme.

---

## 5. Node.js Standards (`realtime`)

Same TypeScript rules as above, plus:

- Pure backend, no JSX.
- Uses `uWebSockets.js` for performance — wrap in a thin abstraction so the rest of the code is testable.
- All async, never `then/catch` outside library boundaries.
- Module organisation mirrors Python services (interfaces / application / domain / infrastructure) but lighter — this is a single-purpose service.

---

## 6. C++ / Arduino Standards (`sdk-arduino`)

### Tooling

| Tool | Version | Notes |
|---|---|---|
| Build | PlatformIO + Arduino IDE compatible | `library.properties` + `library.json` |
| Formatter | `clang-format` (Google style, 100-col) | `.clang-format` |
| Linter | `clang-tidy` (basic ruleset) | `.clang-tidy` |
| Tests | Native + ESP32 simulator | `test/` folder |

### Naming

| Thing | Convention |
|---|---|
| Class | `PascalCase`, prefix with `YP` (YourPlatform) for namespace clarity: `YPClient`, `YPDevice` |
| Method | `camelCase`: `publishTelemetry`, `subscribeToCommand` |
| Constant | `UPPER_SNAKE_CASE`: `YP_MAX_PAYLOAD_SIZE` |
| Member variable | `camelCase` with trailing underscore: `mqttClient_`, `deviceId_` |
| Header guard | `YP_<MODULE>_H_` |
| File | `PascalCase.h` / `PascalCase.cpp` |

### Header organisation

```cpp
// YPClient.h
#ifndef YP_CLIENT_H_
#define YP_CLIENT_H_

#include <Arduino.h>
#include <PubSubClient.h>

namespace yp {

class Client {
 public:
  Client(const char* host, uint16_t port, const char* deviceToken);
  bool begin();
  bool publish(const char* key, float value);
  bool publishJson(const char* json);
  void loop();
  bool isConnected() const;

 private:
  // ...
};

}  // namespace yp

#endif  // YP_CLIENT_H_
```

### Compatibility

- Targets: **ESP32 (all variants), ESP8266, RP2040** at minimum. Arduino UNO R4 WiFi as bonus.
- No C++17 features that don't work on ESP8266 toolchain.
- Memory-conscious: avoid `String` where `const char*` works. Static buffers preferred.
- Hard limit: SRAM usage of library < 16 KB on ESP8266.

### Examples (in `examples/` folder)

Every public class must have at least one runnable example. Naming: `<Board>_<UseCase>` like `ESP32_BasicPublish`, `ESP32_OTA`, `ESP8266_DHT11`.

---

## 7. Go Standards (`edge-agent`, Phase 4)

### Tooling

| Tool | Version | Notes |
|---|---|---|
| Go | 1.22+ | `go.mod` |
| Formatter | `gofmt` (built-in) | — |
| Linter | `golangci-lint` with our config | `.golangci.yml` |
| Tests | standard `go test` | — |

### Standard layout

```
edge-agent/
  cmd/
    agent/
      main.go               # entrypoint, flag parsing
  internal/
    config/
    mqtt/
    storage/                 # local SQLite buffer
    rules/                   # local rule engine
    inference/               # ONNX runtime
    ota/                     # firmware update handler
    server/                  # local HTTP for status
  pkg/                       # exported (consumed by external tools)
  go.mod
  go.sum
```

### Conventions

- Standard Go style: `gofmt`-formatted, error returns, no panics in library code.
- Context propagation: every long-running function takes `ctx context.Context` as first arg.
- Errors wrapped with `fmt.Errorf("context: %w", err)`.
- Logging: `log/slog` standard library (structured).
- No global state except logger and metrics registry.
- Tests in same package: `<file>_test.go`.

---

## 8. SQL Standards

- **All migrations in Alembic** (`apps/api/migrations/versions/`).
- **One migration per PR** ideally; multiple only if logically inseparable.
- **Naming**: `YYYYMMDDHHMM_short_snake_case_description.py`, autogen header preserved.
- **Forward-only.** No down-migrations executed in prod (write a forward migration to fix).
- **Reversible** still required for dev convenience.
- **Long migrations use `CONCURRENTLY`** for index ops on large tables.
- **Never** drop a column in the same migration that stops writing to it. Two-step:
  1. Migration A: stop writing to the column, deploy.
  2. Migration B (next release): drop the column.

### SQL style

- Lowercase keywords (`select`, `from`, `where`).
- One column per line for SELECT > 3 columns.
- Snake_case identifiers.
- Aliases lowercase, descriptive: `from devices d` is fine, `from devices x` is not.
- Always specify columns in INSERT (never `insert into t values (...)`).
- No `select *` in code; only in ad-hoc queries.

```sql
-- Good
select
  d.id,
  d.name,
  d.last_seen_at,
  count(t.time) as datapoint_count
from devices d
left join telemetry t on t.device_id = d.id and t.time > now() - interval '24 hours'
where d.project_id = $1
  and d.status != 'deleted'
group by d.id
order by d.last_seen_at desc nulls last
limit $2;
```

### Indexes

- Every foreign key has an index.
- Every `WHERE` clause column on hot tables has a supporting index.
- Composite indexes ordered by selectivity (most selective first), with the time component last for time-series.
- Index names: `ix_<table>_<col1>_<col2>...`.

---

## 9. JSON / YAML Conventions

### JSON in API and events

- snake_case keys throughout.
- ISO-8601 UTC timestamps with `Z` suffix and millisecond precision.
- Numbers as JSON numbers (no string-encoded numerics).
- Booleans as `true`/`false`.
- Nulls explicit; do not omit fields to mean null in API responses.
- Array of objects, never object of arrays.

### YAML

- 2-space indent.
- Lowercase keys.
- Quotes only when needed (containing `:`, leading numbers, booleans).
- Comments above the line they describe.

---

## 10. Documentation in Code

### When to add a comment

- **Why**, not what. Code shows what; comments explain why this approach.
- Performance-critical sections: link to benchmark.
- Workarounds: link to upstream issue.
- TODOs: include a ticket reference (`# TODO(YP-123): handle CBOR negative ints`).

### When NOT to add a comment

- Restating the code (`# increment counter`).
- Generated code blocks (use `# AUTOGENERATED — do not edit` header instead).
- Commented-out code (delete it).

---

## 11. Performance Guidelines

- **No N+1 queries.** Use eager loading (`selectinload`) or explicit batch fetches.
- **Bulk operations** for >10 items: `executemany`, `COPY`, batched HTTP, etc.
- **Cache invalidation explicit**: every cache write notes its TTL and what invalidates it.
- **No synchronous I/O on hot paths.** All async.
- **Pagination required** on any list endpoint.
- **Backpressure**: NATS consumers use bounded queues; reject when full.

---

## 12. Security Guidelines (Code-Level)

See [09_SECURITY_SPEC.md] for full policy. Code-level musts:

- Never log secrets (passwords, tokens, API keys, AppKeys, AppSKeys).
- All SQL via parameterised queries (SQLAlchemy params, no string interpolation).
- All shell commands via list-form `subprocess.run([...])`, never `shell=True`.
- All file paths validated; never join user input directly.
- HTML escaped by default (Next.js handles this; in raw JSX use `dangerouslySetInnerHTML` only with sanitised input).
- Webhook URLs validated against deny-list (no localhost, no link-local, no metadata services).

---

## 13. Forbidden Patterns

These appear in linter rules. CI fails on them.

| Pattern | Reason | Replacement |
|---|---|---|
| `print()` (Python) | Use logger | `log.info(...)` |
| `console.log` (TS in production code) | Use logger or no-op | `log.info(...)` |
| `eval()` / `exec()` | Security | Restructure |
| `time.time()` for timestamps | Naive | `datetime.now(UTC)` |
| `requests` library | Sync-only | `httpx.AsyncClient` |
| `os.path.join` | Old style | `pathlib.Path` |
| `from x import *` | Pollutes namespace | Explicit imports |
| Bare `except:` | Hides bugs | `except SpecificError:` |
| `# type: ignore` without reason | Silently broken | `# type: ignore[code]  # reason` |
| `any` (TypeScript) | Type-unsafe | `unknown` + narrowing, or proper type |
| `as any` cast (TypeScript) | Type-unsafe | Real fix |
| Top-level `await` outside `main.py` | Subtle | Use `asyncio.run()` in main only |
| Direct DB query in domain layer | Architecture violation | Repository pattern |
| Cross-context import | Architecture violation | Event |

---

## 14. PR Checklist (enforced by template)

Every PR must answer:

- [ ] Added/updated tests
- [ ] Updated migrations (if schema changed)
- [ ] Updated docs (if behaviour or API changed)
- [ ] Updated CHANGELOG (or commit follows Conventional Commits and semantic-release will)
- [ ] No new `# TODO` without ticket reference
- [ ] No new dependencies without justification in PR body
- [ ] CI green on all jobs
