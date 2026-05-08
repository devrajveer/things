# Client Interfaces Specification

The complete public API for every client surface developers will use: Python SDK, JavaScript/Node SDK, Arduino library, and the `yp` CLI. **Every public symbol listed here must exist with exactly this signature.** Internal helpers may be added freely; nothing here may be removed without an ADR + deprecation window.

> Cross-references: [07_DATA_CONTRACTS] for wire formats; [09_SECURITY_SPEC §2.6] for device auth; [05_CODING_STANDARDS §3,§4,§6] for code style per language.

---

## Table of contents

- §1 Common cross-SDK semantics
- §2 Python SDK (`yourplatform`)
- §3 JavaScript / Node SDK (`@yourplatform/sdk`)
- §4 Arduino library (`YourPlatform`)
- §5 CLI (`yp`)
- §6 Versioning policy

---

## 1. Common Cross-SDK Semantics

### 1.1 Identity

- All SDKs identify themselves with `User-Agent: yourplatform-<lang>/<version> (<runtime>)` on every HTTP request.
- All SDKs send `X-YP-SDK: <lang>/<version>` for telemetry.

### 1.2 Authentication forms supported

| Form | Used by | When |
|---|---|---|
| Device token | Python, JS, Arduino, CLI (selected commands) | Publishing telemetry from a device |
| API key | Python, JS, CLI | Server-to-server / scripts |
| Access token (JWT) | CLI (after `yp login`) | Interactive use by humans |

### 1.3 Default endpoints

If not overridden, SDKs use:
- HTTP API: `https://api.yourplatform.io`
- MQTT: `mqtts://mqtt.yourplatform.io:8883`
- Realtime WS: `wss://realtime.yourplatform.io`

Self-host users override via constructor / config / env.

### 1.4 Retry and timeout defaults

- HTTP timeout: 30 s.
- HTTP retries: 3 attempts on 5xx and network errors with exponential backoff (1s, 2s, 4s) + jitter.
- HTTP no retry on 4xx (except 408, 429).
- MQTT auto-reconnect: enabled, exponential backoff (1s → 60s capped).

### 1.5 Error model

Every SDK exposes:
- `YPError` — base class
- `AuthenticationError` — 401
- `AuthorizationError` — 403
- `NotFoundError` — 404
- `ValidationError` — 422 (with `details` of field errors)
- `RateLimitError` — 429 (with `retry_after`)
- `QuotaError` — 402
- `ConflictError` — 409
- `NetworkError` — connection issues
- `TimeoutError` — request/op timeout
- `ServerError` — 5xx

Each error carries: `code` (string from [04_GLOSSARY §6]), `message`, `request_id`, optional `details`.

### 1.6 Telemetry payload conventions

All SDKs accept the same logical shapes ([07_DATA_CONTRACTS §2.8]):

- Single value: one key + one value
- Multi-key: dict of key→value
- Batch: list of multi-key items, each with optional timestamp

SDKs do client-side basic validation (reserved keys, payload size) before sending.

---

## 2. Python SDK (`yourplatform`)

### 2.1 Install

```bash
pip install yourplatform
```

Supports Python 3.10+. Distributed as wheels for Linux/macOS/Windows.

### 2.2 Public API surface

```python
from yourplatform import (
    Client,                  # Sync API client
    AsyncClient,             # Async API client (asyncio)
    DeviceClient,            # Sync device-side client (HTTP+MQTT)
    AsyncDeviceClient,       # Async device-side client
    
    # Errors
    YPError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    QuotaError,
    ConflictError,
    NetworkError,
    TimeoutError,
    ServerError,
    
    # Models
    Device,
    DeviceProfile,
    Stream,
    Datapoint,
    Dashboard,
    Rule,
    Alert,
    Project,
    APIKey,
    
    # Helpers
    parse_jwt,
    set_default_logger,
    
    __version__,
)
```

### 2.3 `Client` (sync, server-side use)

```python
class Client:
    def __init__(
        self,
        api_key: str | None = None,
        api_base_url: str = "https://api.yourplatform.io",
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent_extra: str | None = None,
    ) -> None: ...

    # Resources exposed as attributes:
    projects:    "ProjectsResource"
    devices:     "DevicesResource"      # use: client.devices.list(project_id="prj_...")
    streams:     "StreamsResource"
    dashboards:  "DashboardsResource"
    rules:       "RulesResource"
    alerts:      "AlertsResource"
    api_keys:    "APIKeysResource"
    audit:       "AuditResource"

    def close(self) -> None: ...
    def __enter__(self) -> "Client": ...
    def __exit__(self, *exc) -> None: ...
```

### 2.4 Resource methods

Every resource follows the same pattern:

```python
class DevicesResource:
    def list(
        self,
        project_id: str,
        *,
        status: DeviceStatus | None = None,
        label: str | None = None,
        search: str | None = None,
        sort: str = "last_seen_at",
        limit: int = 50,
        cursor: str | None = None,
    ) -> "Page[Device]": ...

    def iter(
        self,
        project_id: str,
        **filters,
    ) -> Iterator[Device]: ...   # auto-paginates

    def get(self, project_id: str, device_id: str) -> Device: ...

    def create(
        self,
        project_id: str,
        *,
        name: str,
        profile_id: str | None = None,
        labels: dict[str, str] | None = None,
        description: str | None = None,
    ) -> "DeviceCreated": ...   # carries credentials (one-time)

    def update(
        self,
        project_id: str,
        device_id: str,
        *,
        name: str | None = None,
        profile_id: str | None = None,
        labels: dict[str, str] | None = None,
        description: str | None = None,
    ) -> Device: ...

    def disable(self, project_id: str, device_id: str) -> Device: ...
    def enable(self, project_id: str, device_id: str) -> Device: ...
    def rotate_credentials(self, project_id: str, device_id: str) -> "DeviceCredentials": ...
    def delete(self, project_id: str, device_id: str) -> None: ...
```

### 2.5 Streams + telemetry queries

```python
class StreamsResource:
    def list(self, project_id: str, *, device_id: str | None = None, search: str | None = None,
             limit: int = 50, cursor: str | None = None) -> Page[Stream]: ...
    def get(self, project_id: str, stream_id: str) -> Stream: ...
    def update(self, project_id: str, stream_id: str, *, display_name: str | None = None,
               unit: str | None = None) -> Stream: ...

    def series(
        self,
        project_id: str,
        stream_id: str,
        *,
        from_: datetime,
        to: datetime | None = None,
        agg: Literal["avg","min","max","sum","count","last"] = "avg",
        bucket: timedelta | None = None,
        limit: int = 1000,
    ) -> "Series": ...                 # .points: list[(datetime, float)]

    def latest(self, project_id: str, stream_id: str) -> Datapoint: ...

    def export_csv(
        self,
        project_id: str,
        stream_id: str,
        *,
        from_: datetime,
        to: datetime | None = None,
        path: str | os.PathLike,
    ) -> Path: ...
```

### 2.6 Pagination helper

```python
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool

    def __iter__(self) -> Iterator[T]: ...
```

### 2.7 `DeviceClient` (publishing telemetry from a device)

```python
class DeviceClient:
    def __init__(
        self,
        token: str,                                      # device HTTP token
        *,
        transport: Literal["http","mqtt"] = "http",
        api_base_url: str = "https://api.yourplatform.io",
        mqtt_url: str = "mqtts://mqtt.yourplatform.io:8883",
        mqtt_username: str | None = None,                # required for MQTT
        mqtt_password: str | None = None,                # required for MQTT
        client_id: str | None = None,                    # MQTT client id
        keepalive: int = 60,
        clean_session: bool = True,
        tls_ca_path: str | None = None,
        timeout: float = 30.0,
        on_command: Callable[[Command], None] | None = None,  # MQTT downlink callback
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[Exception | None], None] | None = None,
    ) -> None: ...

    # Connect (MQTT) / no-op (HTTP)
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    # Publish single
    def publish(
        self,
        values: dict[str, Any] | tuple[str, Any],
        *,
        ts: datetime | None = None,
    ) -> None: ...

    # Publish batch
    def publish_batch(
        self,
        items: list[dict[str, Any]],     # each item: {"values": {...}, "ts": ...}
    ) -> None: ...

    # Publish state (retained on MQTT)
    def publish_state(self, state: dict[str, Any]) -> None: ...

    # Publish event (discrete)
    def publish_event(self, name: str, data: dict[str, Any] | None = None) -> None: ...

    # Acknowledge a command
    def ack(self, command_id: str, *, success: bool = True, message: str | None = None) -> None: ...

    # Run forever loop (for MQTT command listening)
    def loop_forever(self) -> None: ...
    def loop_in_background(self) -> None: ...
```

### 2.8 `AsyncClient` and `AsyncDeviceClient`

Identical signatures, all methods `async def`. Use `aclose()` instead of `close()`.

### 2.9 Logging

- Module logger `yourplatform`. Default WARNING. Users opt in.
- `set_default_logger(level=logging.DEBUG)` enables verbose output.
- Errors logged with `request_id` for correlation.

### 2.10 Quickstart examples (must ship in `examples/`)

Files:
- `examples/python/quickstart_publish_http.py`
- `examples/python/quickstart_publish_mqtt.py`
- `examples/python/listen_for_commands.py`
- `examples/python/batch_publish.py`
- `examples/python/admin_create_device.py`
- `examples/python/series_query_chart.py` (matplotlib)
- `examples/python/async_publish.py`

Each example: ≤30 lines, runs as-is with credentials filled in, includes a `if __name__ == "__main__":` guard.

### 2.11 Type stubs

- All SDK types exported from `yourplatform.types`.
- `py.typed` marker shipped.
- Validated mypy-clean against client code.

### 2.12 Distribution and metadata

- License: AGPL-3.0-or-later (matching platform).
- README in repo + on PyPI.
- Min Python 3.10, max not capped.
- Binary deps: `httpx`, `paho-mqtt`, `pydantic`, `python-ulid`.

---

## 3. JavaScript / Node SDK (`@yourplatform/sdk`)

### 3.1 Install

```bash
npm install @yourplatform/sdk
# or
pnpm add @yourplatform/sdk
```

Targets: Node 18+, modern browsers (ES2022). Bundled as ESM + CJS + UMD.

### 3.2 Public API surface

```typescript
import {
  Client,
  DeviceClient,
  RealtimeClient,        // WebSocket subscriber

  // Errors
  YPError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  QuotaError,
  ConflictError,
  NetworkError,
  TimeoutError,
  ServerError,

  // Types
  Device,
  DeviceProfile,
  Stream,
  Datapoint,
  Dashboard,
  Rule,
  Alert,
  Project,
  APIKey,
  Series,

  VERSION,
} from '@yourplatform/sdk';
```

### 3.3 `Client`

```typescript
interface ClientOptions {
  apiKey?: string;
  accessToken?: string;
  apiBaseUrl?: string;        // default 'https://api.yourplatform.io'
  timeoutMs?: number;          // default 30_000
  maxRetries?: number;         // default 3
  userAgentExtra?: string;
  fetch?: typeof globalThis.fetch;  // override fetch (e.g., undici)
}

export class Client {
  constructor(options?: ClientOptions);

  readonly projects: ProjectsResource;
  readonly devices: DevicesResource;
  readonly streams: StreamsResource;
  readonly dashboards: DashboardsResource;
  readonly rules: RulesResource;
  readonly alerts: AlertsResource;
  readonly apiKeys: APIKeysResource;
  readonly audit: AuditResource;

  close(): void;
}
```

### 3.4 Resource methods (sample: devices)

```typescript
interface ListDevicesParams {
  status?: DeviceStatus;
  label?: string;
  search?: string;
  sort?: 'name' | 'created_at' | 'last_seen_at';
  limit?: number;
  cursor?: string;
}

interface CreateDeviceInput {
  name: string;
  profileId?: string;
  labels?: Record<string, string>;
  description?: string;
}

class DevicesResource {
  list(projectId: string, params?: ListDevicesParams): Promise<Page<Device>>;
  iter(projectId: string, params?: ListDevicesParams): AsyncIterableIterator<Device>;
  get(projectId: string, deviceId: string): Promise<Device>;
  create(projectId: string, input: CreateDeviceInput): Promise<DeviceCreated>;
  update(projectId: string, deviceId: string, input: Partial<CreateDeviceInput>): Promise<Device>;
  disable(projectId: string, deviceId: string): Promise<Device>;
  enable(projectId: string, deviceId: string): Promise<Device>;
  rotateCredentials(projectId: string, deviceId: string): Promise<DeviceCredentials>;
  delete(projectId: string, deviceId: string): Promise<void>;
}
```

### 3.5 `DeviceClient`

```typescript
interface DeviceClientOptions {
  token: string;                         // device HTTP token
  transport?: 'http' | 'mqtt';           // default 'http'
  apiBaseUrl?: string;
  mqttUrl?: string;
  mqttUsername?: string;
  mqttPassword?: string;
  clientId?: string;
  keepaliveSeconds?: number;
  cleanSession?: boolean;
  timeoutMs?: number;
  onCommand?: (cmd: Command) => void;
  onConnect?: () => void;
  onDisconnect?: (err?: Error) => void;
}

export class DeviceClient {
  constructor(opts: DeviceClientOptions);

  connect(): Promise<void>;                                          // MQTT only
  disconnect(): Promise<void>;
  isConnected(): boolean;

  publish(values: Record<string, unknown>, opts?: { ts?: Date }): Promise<void>;
  publishBatch(items: Array<{ values: Record<string, unknown>; ts?: Date }>): Promise<void>;
  publishState(state: Record<string, unknown>): Promise<void>;
  publishEvent(name: string, data?: Record<string, unknown>): Promise<void>;
  ack(commandId: string, opts?: { success?: boolean; message?: string }): Promise<void>;
}
```

### 3.6 `RealtimeClient` (WebSocket subscriber)

```typescript
interface RealtimeClientOptions {
  url?: string;                          // default 'wss://realtime.yourplatform.io'
  accessToken: string;
  reconnect?: boolean;                   // default true
  heartbeatSeconds?: number;             // default 30
  onConnect?: () => void;
  onDisconnect?: (err?: Error) => void;
  onWarning?: (warning: { code: string; message: string }) => void;
}

interface RealtimeSubscription {
  id: string;
  unsubscribe(): void;
}

export class RealtimeClient {
  constructor(opts: RealtimeClientOptions);

  connect(): Promise<void>;
  disconnect(): void;

  subscribeToStream(
    projectId: string,
    streamIds: string[],
    onData: (datapoint: Datapoint) => void,
  ): RealtimeSubscription;

  subscribeToAlerts(
    projectId: string,
    onAlert: (alert: AlertEvent) => void,
  ): RealtimeSubscription;
}
```

### 3.7 Errors

Each Error class extends `YPError` and carries `.code`, `.requestId`, `.details?`.

### 3.8 Browser usage notes

- `Client` works in browser (CORS allowing).
- `DeviceClient` MQTT in browser uses `mqtts` over WebSocket (`wss://mqtt.<host>/mqtt`).
- `RealtimeClient` works in browser natively.

### 3.9 Tree-shaking

Each surface is in its own entry: `@yourplatform/sdk/client`, `@yourplatform/sdk/device`, `@yourplatform/sdk/realtime`. The umbrella export re-exports all but is heavier.

### 3.10 Examples directory

- `examples/node/quickstart-publish-http.ts`
- `examples/node/quickstart-publish-mqtt.ts`
- `examples/node/listen-for-commands.ts`
- `examples/node/series-query.ts`
- `examples/browser/realtime-dashboard.html`
- `examples/browser/publish-from-form.html`

### 3.11 Distribution

- License: AGPL-3.0-or-later.
- README + JSDoc in source.
- Generated `.d.ts` type definitions shipped.

---

## 4. Arduino Library (`YourPlatform`)

Distribution: Arduino Library Manager + PlatformIO Registry. Repo at `packages/sdk-arduino/`.

### 4.1 Supported boards

- ESP32 (all variants: WROOM, S2, S3, C3)
- ESP8266
- Raspberry Pi Pico W (RP2040)
- Arduino UNO R4 WiFi (best-effort)

### 4.2 Public API surface

```cpp
// YourPlatform.h
#include <YPClient.h>     // primary client
#include <YPDevice.h>     // typed device-state helper
#include <YPCommand.h>    // command struct + helpers
```

### 4.3 `YPClient`

```cpp
namespace yp {

class Client {
 public:
  // Constructor
  // host:    e.g. "mqtt.yourplatform.io"
  // port:    8883 (TLS) or 1883 (plain)
  // username, password: device credentials
  // useTLS:  true to use TLS
  Client(const char* host, uint16_t port,
         const char* username, const char* password,
         bool useTLS = true);

  // Setup
  void setRootCA(const char* pemRootCA);          // for TLS
  void setKeepAlive(uint16_t seconds);            // default 60
  void setCleanSession(bool clean);               // default true
  void setClientId(const char* clientId);
  void setBufferSize(uint16_t size);              // default 1024 bytes
  void setBackoffPolicy(uint16_t initialMs, uint16_t maxMs);

  // Lifecycle
  bool begin();                                    // wifi must be connected first
  bool isConnected() const;
  void loop();                                     // call in main loop()

  // Publish telemetry
  bool publish(const char* key, float value);
  bool publish(const char* key, int value);
  bool publish(const char* key, bool value);
  bool publish(const char* key, const char* value);
  bool publishJson(const char* json);              // raw JSON body
  bool publishMulti(const char* json);             // {"values":{...}}

  // Publish state (retained)
  bool publishState(const char* json);

  // Publish event
  bool publishEvent(const char* name, const char* json = nullptr);

  // Subscribe to commands
  using CommandCallback = void (*)(const Command& cmd);
  void onCommand(CommandCallback cb);
  bool ack(const char* commandId, bool success = true, const char* message = nullptr);

  // Connection events
  using ConnectCallback = void (*)();
  using DisconnectCallback = void (*)(int reasonCode);
  void onConnect(ConnectCallback cb);
  void onDisconnect(DisconnectCallback cb);
};

}  // namespace yp
```

### 4.4 `Command`

```cpp
namespace yp {

struct Command {
  const char* id;
  const char* type;       // user-defined
  const char* payload;    // raw JSON or string
};

}
```

### 4.5 Memory and limits

- Library footprint: < 16 KB SRAM (ESP8266 hard limit).
- Default publish buffer: 1024 bytes (configurable).
- Uses `PubSubClient` underneath for ESP8266; `AsyncMqttClient` for ESP32 by default (configurable).

### 4.6 Examples (every example must compile and run on its target board)

```
examples/
  ESP32_BasicPublish/
    ESP32_BasicPublish.ino
  ESP32_Multi_DHT22/
    ESP32_Multi_DHT22.ino
  ESP32_OTA/
    ESP32_OTA.ino
  ESP32_DeepSleep/
    ESP32_DeepSleep.ino
  ESP32_LoRa/                       (Phase 3, with TTGO LoRa32)
    ESP32_LoRa.ino
  ESP8266_BasicPublish/
    ESP8266_BasicPublish.ino
  ESP8266_DHT11/
    ESP8266_DHT11.ino
  RP2040_PicoW_Basic/
    RP2040_PicoW_Basic.ino
```

Each `.ino` includes a header comment block:
- Description of what it does
- Required hardware
- Wiring diagram (ASCII)
- Required libraries
- Configuration constants the user must change (clearly marked)

### 4.7 Library metadata

`library.properties`:
```ini
name=YourPlatform
version=1.0.0
author=...
maintainer=...
sentence=Connect IoT devices to the yourplatform IoT platform.
paragraph=High-performance MQTT client with auto-reconnect, command listening, batch publishing.
category=Communication
url=https://github.com/.../sdk-arduino
architectures=esp32,esp8266,rp2040,renesas_uno
includes=YourPlatform.h
depends=PubSubClient,ArduinoJson
license=AGPL-3.0-or-later
```

`library.json` for PlatformIO mirrors above.

### 4.8 Tests

- Unit tests in `test/native/` — runnable with `pio test -e native`.
- Tests target protocol logic, not hardware.
- Hardware-in-loop nightly: ESP32 wired to a CI runner publishes a known sequence; runner verifies arrival.

---

## 5. CLI (`yp`)

### 5.1 Install

```bash
pip install yourplatform              # CLI ships with the Python package
# OR standalone:
pip install yp-cli
# OR a single binary (Phase 2):
curl -sSL https://get.yourplatform.io | sh
```

### 5.2 Top-level structure

```
yp                                                Show help
yp --version                                      Print version
yp completion {bash|zsh|fish}                     Shell completion
yp config {get|set|unset|list|edit}               Local config (~/.yp/config.toml)

yp login [--api-base-url URL]                     Browser-based login flow → stores token
yp logout
yp whoami

yp project {list|use|create|delete}
yp device  {list|create|get|update|disable|enable|rotate-credentials|delete|simulate}
yp profile {list|create|get|update|delete}
yp stream  {list|get|export|series}
yp ingest  {publish|publish-file}
yp dashboard {list|get|create|update|delete|export|import}
yp rule    {list|get|create|update|enable|disable|delete|preview}
yp alert   {list|get|acknowledge|resolve|snooze}
yp key     {list|create|revoke}
yp audit   {list|export}

yp tail    [--device dev_... | --stream str_...] [--follow]
yp logs    {api|ingest|worker|...}                Self-host: docker logs wrapper

yp open dashboard <id>                            Open in browser
yp open device <id>
yp open project

yp self-host {init|start|stop|status|update|backup|restore}    For self-hosters
```

### 5.3 Global flags

| Flag | Description |
|---|---|
| `--api-base-url URL` | Override server |
| `--api-key KEY` | Override credentials |
| `--project ID` | Override active project (else from config) |
| `--output FORMAT` | `table` (default), `json`, `yaml`, `csv` |
| `--no-color` | Disable color |
| `--quiet` | Errors only |
| `--verbose` / `-v`, `-vv` | Increase log level |
| `--help` / `-h` | Help |

### 5.4 Configuration file (`~/.yp/config.toml`)

```toml
[default]
api_base_url = "https://api.yourplatform.io"
project_id   = "prj_..."

[default.auth]
type         = "access_token"           # or "api_key"
access_token = "eyJ..."
refresh_token = "..."
expires_at   = "..."

[profiles.work]
api_base_url = "https://yp.mycompany.internal"
project_id   = "prj_..."
[profiles.work.auth]
type    = "api_key"
api_key = "yp_live_..."
```

Switch profiles: `yp --profile work device list`.

### 5.5 Selected command details

#### `yp login`

```
yp login [--method browser|magic|password] [--api-base-url URL]
```
- `browser` (default): opens browser to `https://app.<host>/login?cli=1&port=<local>`. After login, app POSTs the token back to a local listener.
- `magic`: prompts for email; sends magic link.
- `password`: prompts for email + password (no echo).

Stores tokens encrypted via OS keyring when available; falls back to `0600` config file.

#### `yp device create`

```
yp device create --name greenhouse-1-temp \
  [--profile dpf_...] \
  [--label location=greenhouse-1] [--label type=sensor] \
  [--description "..."] \
  [--output json]
```
On success, prints credentials in human-readable form (or JSON) with the warning that they cannot be shown again.

#### `yp ingest publish`

```
yp ingest publish --device dev_... --key temperature --value 23.5
yp ingest publish --device dev_... --json '{"values":{"t":23.5,"h":58}}'
yp ingest publish --device dev_... --file payload.json
```

#### `yp device simulate`

```
yp device simulate --device dev_... --pattern sine \
  --key temperature --min 18 --max 28 --period 60 --rate 1
```
- Patterns: `constant`, `sine`, `random_walk`, `step`, `noise`.
- Useful for demos and development.

#### `yp tail`

```
yp tail --device dev_...
yp tail --stream str_...
yp tail --project prj_... --json
```

Connects to realtime WebSocket, prints datapoints as they arrive. Uses tablular format unless `--json`.

```
2025-01-15T10:30:00.123Z  dev_abc  temperature   23.5
2025-01-15T10:30:01.123Z  dev_abc  temperature   23.6
```

Press `Ctrl+C` to stop.

#### `yp dashboard export / import`

```
yp dashboard export dsh_... > dashboard.json
yp dashboard import --file dashboard.json --project prj_...
```

For backup, sharing, version control.

#### `yp rule preview`

```
yp rule preview rul_... --lookback 24h
```
Prints datapoints in the lookback window that would have triggered the rule.

#### `yp self-host init`

```
yp self-host init [--directory ./yp-data]
```
- Generates `docker-compose.yml`, `.env`, secrets, certificates.
- Walks user through admin setup interactively.
- Prints next-step commands.

### 5.6 Output formatting

- `table` (default): aligned columns, color (status colors per [08_UI_UX_SPEC §1.1]).
- `json`: pretty-printed by default; compact with `--compact`.
- `yaml`: human-friendly.
- `csv`: for piping into spreadsheets.

Tables use Unicode box-drawing on terminals that support it; ASCII fallback otherwise.

### 5.7 Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Generic error |
| 2 | Usage error (bad args) |
| 3 | Auth error |
| 4 | Not found |
| 5 | Permission denied |
| 6 | Validation error |
| 7 | Quota exceeded |
| 8 | Server error |
| 9 | Network error |
| 10 | Configuration error |

### 5.8 Help text quality

- Every subcommand: `--help` shows usage, description, all flags with defaults, 1-2 examples.
- Errors include suggested fix where possible (e.g., "Did you mean `yp device list`? Run `yp device --help`").

### 5.9 Tests

- Unit tests for argument parsing.
- Integration tests against a docker-compose fixture spinning up `api`.
- Snapshot tests for output formatting.

---

## 6. Versioning Policy

### 6.1 SemVer

All SDKs and CLI use SemVer 2.0:
- **MAJOR**: breaking change to public API.
- **MINOR**: new functionality, backward-compatible.
- **PATCH**: bug fixes, no API change.

### 6.2 Compatibility matrix

The platform's HTTP API is versioned in URL (`/v1`). SDKs target a specific API major version.

| SDK version range | Targets API |
|---|---|
| `1.x.x` | `v1` |
| `2.x.x` | `v2` (when introduced) |

SDKs warn on console if connected server reports a newer major version available.

### 6.3 Deprecation

- Deprecations marked in code with `@deprecated` (Python `warnings.warn(DeprecationWarning)`, TS `@deprecated` JSDoc, C++ `[[deprecated("reason")]]`).
- Deprecation period: minimum 2 minor releases or 6 months, whichever longer, before removal.
- Removal in next MAJOR.

### 6.4 Changelog

Each SDK ships `CHANGELOG.md` following Keep-a-Changelog format. Generated from Conventional Commits via `semantic-release`.
