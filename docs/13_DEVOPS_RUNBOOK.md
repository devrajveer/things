# DevOps Runbook

The complete operational manual for running yourplatform across **dev**, **staging**, and **prod** environments. Every procedure here is meant to be executed by a human (or AI agent) without needing to think.

> Conventions: All commands assume bash on Linux/macOS. Substitute paths with your repo root. Service names match [02_ARCHITECTURE §4]. Env vars defined in [11_CONFIGURATION_REFERENCE].

---

## Table of contents

- §1 Environments and machines
- §2 Local development setup
- §3 Daily development workflow
- §4 Database operations
- §5 Build and release pipeline
- §6 Staging environment
- §7 Production environment (Hetzner Tier A)
- §8 Deployment procedures
- §9 Backups and restore
- §10 Monitoring and alerting
- §11 Incident runbooks
- §12 Secret management
- §13 DNS, domains, TLS
- §14 Scaling procedures
- §15 Disaster recovery plan
- §16 Routine maintenance schedule

---

## 1. Environments and machines

### 1.1 Environment matrix

| Environment | Purpose | Machines | Domain | Data |
|---|---|---|---|---|
| `dev` | Local development on developer laptop | 1 (laptop) | `localhost`, `*.localtest.me` | Synthetic/seeded |
| `staging` | Integration testing, customer demos | 1 × Hostinger KVM 8 (or Hetzner CX32) | `staging.<your-domain>` | Synthetic + opt-in |
| `prod` | Customer-facing production | 2 × Hetzner CPX31 + 1 × CCX13 + LB + Storage Box | `app.<your-domain>`, `api.<your-domain>` | Real customer data |

### 1.2 Branch-to-environment mapping

| Branch | Auto-deploys to |
|---|---|
| Pull request | (no deploy; runs CI only) |
| `main` | `staging` (on every merge) |
| Tag `v*` (e.g., `v0.4.0`) | `prod` (manual approval gate) |

### 1.3 Region

All production resources in **Hetzner Falkenstein (fsn1)** for v1. Add second region in Phase 4.

---

## 2. Local development setup

Goal: a fresh laptop becomes a fully running platform in **≤ 15 minutes** with one command.

### 2.1 Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop / Docker Engine | ≥ 24.0 | https://docs.docker.com/engine/install/ |
| Docker Compose | ≥ 2.20 | bundled with Docker Desktop |
| Git | ≥ 2.40 | platform package manager |
| Node.js | 22 LTS | use `mise` or `nvm` |
| pnpm | 9.x | `npm i -g pnpm@9` |
| Python | 3.12 | use `mise` or `uv python install 3.12` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh | sh` |
| make | any | platform default |
| direnv | optional but recommended | `brew install direnv` |

### 2.2 First-time clone

```bash
git clone git@github.com:<org>/yourplatform.git
cd yourplatform
make setup            # one command — see §2.3 for what it does
```

### 2.3 What `make setup` does

`Makefile` target `setup` runs in order:

1. Verify prerequisites are installed (fails with friendly message if missing).
2. Copy `.env.example` → `.env` if not already present.
3. Generate dev secrets (JWT secret, MinIO keys, Postgres password) into `.env` if blank.
4. `pnpm install --frozen-lockfile` at root (installs all workspace JS deps).
5. `uv sync` in `services/api`, `services/ingest`, `services/worker`, `services/ai-worker`, `services/scheduler`, `apps/cli`.
6. `docker compose pull` (pulls Postgres, Redis, NATS, EMQX, MinIO, ChirpStack images).
7. `docker compose up -d postgres redis nats minio emqx chirpstack` (data plane only, not app services).
8. Wait for Postgres healthy.
9. `make migrate` (runs Alembic migrations).
10. `make seed` (creates demo org, project, devices, dashboards).
11. Print success banner with next-step commands.

### 2.4 Developer URLs (after setup)

| Service | URL | Credentials |
|---|---|---|
| Web app | http://localhost:3000 | `demo@yourplatform.local` / `demo123!` |
| API | http://localhost:8000 | use SDK/CLI |
| API docs (Swagger) | http://localhost:8000/docs | — |
| Postgres | `postgresql://yp:devpass@localhost:5432/yourplatform` | — |
| Redis | `redis://localhost:6379` | — |
| NATS | `nats://localhost:4222` | — |
| EMQX dashboard | http://localhost:18083 | `admin` / `public` |
| MinIO console | http://localhost:9001 | `minioadmin` / `minioadmin` |
| ChirpStack | http://localhost:8090 | `admin` / `admin` |
| Mailhog (dev SMTP) | http://localhost:8025 | — |

### 2.5 Running services in dev

Three terminal panes (use `tmux`, `zellij`, or VS Code split terminals):

```bash
# Pane 1: backend services
make dev-backend
# Spawns: api, ingest, realtime, worker, ai-worker, scheduler in honcho/foreman
# All with hot reload via watchfiles + tsx watch

# Pane 2: web
make dev-web
# Runs: cd apps/web && pnpm dev (Next.js)

# Pane 3: free for git, tests, ad-hoc
```

Stop everything: `make stop` (down all containers) or `Ctrl+C` in each pane.

### 2.6 Resetting local state

```bash
make reset            # destroys volumes, re-runs migrate + seed (preserves .env)
make clean            # destroys volumes AND .env (full nuke)
```

---

## 3. Daily development workflow

### 3.1 Starting a feature

```bash
git checkout main
git pull --rebase
git checkout -b feat/T-1234-add-csv-export   # ticket id from playbook
```

### 3.2 Pre-commit hooks

Installed automatically by `make setup`. Run on every commit:

- `ruff check --fix` and `ruff format` on staged Python files
- `prettier --write` on staged JS/TS/MD files
- `eslint` on staged JS/TS files
- `markdownlint` on staged MD files
- Forbid commits that include strings matching secret patterns (uses `gitleaks`)
- Forbid `.env` files (only `.env.example` allowed)

To bypass (emergency only): `git commit --no-verify`.

### 3.3 Running tests

```bash
make test             # all unit + integration tests
make test-unit        # only unit (fast, no Docker)
make test-py          # only Python tests
make test-ts          # only TypeScript tests
make test-e2e         # Playwright (requires services running)
make coverage         # coverage report; fails if < threshold ([10_TEST_PLAN §3])
```

### 3.4 Linting and type-checking

```bash
make lint             # all linters
make typecheck        # mypy + tsc --noEmit
```

CI runs `make ci` which is `lint && typecheck && test && coverage`.

### 3.5 Pushing and PR

```bash
git push -u origin feat/T-1234-add-csv-export
gh pr create --fill   # uses PR template (see [05_CODING_STANDARDS §4])
```

CI must be green before merge. PR requires self-review using checklist in PR template.

---

## 4. Database operations

### 4.1 Creating a migration

```bash
cd services/api
uv run alembic revision --autogenerate -m "add device_groups table"
# edit the generated file in services/api/migrations/versions/
# verify upgrade() and downgrade() are both correct
uv run alembic upgrade head    # apply locally
uv run alembic downgrade -1    # test rollback
uv run alembic upgrade head    # re-apply
```

Migration rules (enforced in CI):

- Every migration has a working `downgrade()`. No `pass`-only downgrades.
- Migrations are idempotent (use `IF NOT EXISTS` / `IF EXISTS` clauses where supported).
- No `DROP COLUMN` or `DROP TABLE` in same release as code changes that stop using them — use a two-step deprecation: release N marks unused, release N+1 drops.
- Hypertable creation (`SELECT create_hypertable(...)`) only via raw SQL in migration; declare with `if_not_exists => TRUE`.
- Index creation on tables > 1M rows uses `CREATE INDEX CONCURRENTLY` (requires `op.execute` and autocommit).
- Continuous aggregates and retention policies declared via raw SQL.

### 4.2 Migrations in production

Never edited or skipped manually. Run only via deployment pipeline.

```bash
# What CI/CD runs against prod:
docker run --rm \
  -e POSTGRES_DSN="$PROD_POSTGRES_DSN" \
  ghcr.io/<org>/yourplatform-api:$VERSION \
  uv run alembic upgrade head
```

Migrations run **before** new app version starts serving traffic. Rolling deploys block until migration completes.

### 4.3 Connecting to prod DB (read-only)

For investigation only. Never run writes. Use a personal read-only role:

```bash
ssh deploy@db.prod.internal -L 6543:localhost:5432 -N
# in another shell:
psql "postgresql://reader:$PASS@localhost:6543/yourplatform"
```

All read-only sessions are audit-logged via Postgres `log_statement = 'all'` for the `reader` role.

### 4.4 Seeding

```bash
make seed             # idempotent: creates demo data if absent, leaves alone if present
make seed-fresh       # truncates non-system tables and re-seeds (DEV ONLY)
```

Seed source: `services/api/seeds/dev.py`. See [10_TEST_PLAN §6.1] for what it creates.

---

## 5. Build and release pipeline

### 5.1 Versioning

CalVer: `YYYY.MM.PATCH` (e.g., `2026.04.0`, `2026.04.1`, `2026.05.0`).

- Bump on every release.
- `PATCH` resets to 0 each new month.
- Tag is `v2026.04.1`.

### 5.2 Container image build

Each service has a `Dockerfile` at `services/<name>/Dockerfile`. All inherit the base patterns from [05_CODING_STANDARDS §15].

CI builds and pushes to **GitHub Container Registry** (ghcr.io):

```
ghcr.io/<org>/yourplatform-api:<version>
ghcr.io/<org>/yourplatform-api:latest
ghcr.io/<org>/yourplatform-ingest:<version>
ghcr.io/<org>/yourplatform-realtime:<version>
ghcr.io/<org>/yourplatform-worker:<version>
ghcr.io/<org>/yourplatform-ai-worker:<version>
ghcr.io/<org>/yourplatform-scheduler:<version>
ghcr.io/<org>/yourplatform-web:<version>
ghcr.io/<org>/yourplatform-edge-agent:<version>
```

Multi-arch: `linux/amd64` and `linux/arm64` (the latter for Raspberry Pi / Apple Silicon).

### 5.3 Image signing and verification

Every image signed with `cosign` keyless (OIDC via GitHub Actions).

Production deploy script verifies before pulling:

```bash
cosign verify ghcr.io/<org>/yourplatform-api:$VERSION \
  --certificate-identity-regexp "https://github.com/<org>/yourplatform/.github/workflows/release.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

### 5.4 Release procedure

1. Merge all PRs targeted for release into `main`.
2. Update `CHANGELOG.md` under "Unreleased" → rename to `v2026.04.1 — 2026-04-15`.
3. Run `make release VERSION=2026.04.1`. This:
   - Creates an annotated git tag `v2026.04.1`.
   - Pushes the tag.
   - Triggers GitHub Actions release workflow.
4. Workflow builds all images, signs, pushes, generates SBOM, attaches to GitHub Release.
5. Workflow runs full e2e suite against staging.
6. If e2e green, posts to `#releases` Slack/Discord with "Ready to deploy" button.
7. A human (or AI agent with prod scope) approves → triggers prod deploy.

---

## 6. Staging environment

### 6.1 Topology

Single **Hetzner CX32** VPS (4 vCPU, 8 GB RAM, 80 GB SSD, ~€7/mo). Runs everything via `docker compose`. **Not** for paying customers, never. Used for:

- Verifying releases pre-prod
- Customer demos
- Reproducing production bugs

### 6.2 Initial provisioning

```bash
# From your laptop, in the repo:
cd infra/staging
./bootstrap.sh <staging-host-ip>
```

Bootstrap script (idempotent) does:
1. SSH in as `root`, create `deploy` user with sudo, install SSH key, disable root login.
2. `apt update && apt upgrade -y`.
3. Install Docker, Docker Compose, Caddy, ufw, fail2ban, prometheus-node-exporter.
4. Configure ufw: allow 22, 80, 443, 1700/udp (LoRa), 8883 (MQTT TLS); deny all else.
5. Clone repo to `/opt/yourplatform`.
6. Copy `.env.staging.template` → `.env`, prompt for required secrets.
7. Pull images, run migrations, start stack.
8. Configure Caddy with auto-HTTPS for `staging.<your-domain>`.
9. Install systemd service `yourplatform.service` that runs `docker compose up`.
10. Print URLs and admin credentials.

### 6.3 Deploying to staging

Auto-deploy on every merge to `main`:

```yaml
# .github/workflows/deploy-staging.yml
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: deploy
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/yourplatform
            git fetch --all
            git reset --hard origin/main
            export VERSION=$(git rev-parse --short HEAD)
            ./infra/staging/deploy.sh
```

`deploy.sh` does: `docker compose pull && docker compose run --rm api alembic upgrade head && docker compose up -d --remove-orphans`.

### 6.4 Resetting staging

```bash
ssh deploy@staging.<your-domain>
cd /opt/yourplatform
./infra/staging/reset.sh   # wipes DB volumes, re-seeds; ASKS FOR CONFIRMATION
```

---

## 7. Production environment (Hetzner Tier A)

### 7.1 Topology

```
                       Cloudflare (DNS, CDN, DDoS, WAF)
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
                    app.<domain>          api.<domain>
                    mqtt.<domain>         lora.<domain>
                                     │
                                     ▼
                       Hetzner Load Balancer (LB-1)
                          │              │
                ┌─────────┘              └─────────┐
                ▼                                  ▼
         ┌──────────────┐                   ┌──────────────┐
         │   app-1      │                   │   app-2      │
         │   CPX31      │                   │   CPX31      │
         │ 4 vCPU/8GB   │  ◄── private  ──► │ 4 vCPU/8GB   │
         │              │     network       │              │
         │ caddy        │                   │ caddy        │
         │ web          │                   │ web          │
         │ api          │                   │ api          │
         │ ingest       │                   │ ingest       │
         │ realtime     │                   │ realtime     │
         │ worker       │                   │ worker       │
         │ ai-worker    │                   │ ai-worker    │
         │ scheduler*   │                   │ (standby)    │
         │ emqx (node1) │ ◄─── cluster ───► │ emqx (node2) │
         │ nats (n1)    │ ◄─── cluster ───► │ nats (n2)    │
         │ minio (n1)   │ ◄─── erasure ───► │ minio (n2)   │
         │ chirpstack   │                   │ (standby)    │
         └──────┬───────┘                   └──────┬───────┘
                │                                  │
                └────────────────┬─────────────────┘
                                 ▼
                       ┌──────────────────┐
                       │      db          │
                       │      CCX13       │
                       │ 2 ded vCPU/8GB   │
                       │                  │
                       │ postgres+timescale+pgvec │
                       │ valkey (redis)   │
                       │ pgbackrest       │
                       └────────┬─────────┘
                                │
                                ▼
                  Hetzner Storage Box (1 TB, backups)
                                │
                                ▼
                   Backblaze B2 (off-site, encrypted)
```

* `scheduler` runs only on `app-1` (leader-elected via NATS KV lock); `app-2` is standby.

### 7.2 Initial provisioning

All infra defined as code in `infra/prod/`. Tool: **OpenTofu** (open-source Terraform fork). Hetzner Cloud provider.

```bash
cd infra/prod
cp terraform.tfvars.example terraform.tfvars
# fill in: hcloud_token, ssh_keys, domain, cloudflare_token
tofu init
tofu plan
tofu apply
```

Resources created:
- 2 × CPX31 (`app-1`, `app-2`) in fsn1
- 1 × CCX13 (`db`) in fsn1
- 1 × Hetzner Load Balancer (LB-1) in fsn1
- 1 × Private Network 10.0.0.0/16
- 1 × Storage Box BX21 (1 TB)
- Cloudflare DNS records pointing to LB-1
- Cloudflare WAF rules

After `tofu apply` completes, run:

```bash
ansible-playbook -i inventory.ini playbooks/site.yml
```

Ansible playbook installs:
- OS hardening (CIS-Lite baseline): SSH key only, disable root, ufw, fail2ban, automatic security updates via `unattended-upgrades`.
- Docker, K3s (single-node per machine for now; cluster mode in Phase 3).
- Postgres 16 + TimescaleDB extension + pgvector + pgBackRest on `db`.
- Valkey on `db`.
- All app services on `app-1`, `app-2` via systemd-managed `docker compose`.
- Caddy on each app node with auto-HTTPS (uses Cloudflare DNS challenge for wildcards).
- Prometheus node_exporter on every host.
- Loki promtail on every host shipping to monitoring host.

### 7.3 Production secret bootstrap

Secrets are NOT in Terraform state. Generated separately and stored in **age-encrypted** files in `infra/prod/secrets/` (committed to git as ciphertext only).

```bash
# Generate fresh prod secrets:
./infra/prod/scripts/gen-secrets.sh
# Edits secrets.age, commit it.
# To use during deploy:
age -d -i ~/.age/yourplatform.key infra/prod/secrets/secrets.age > /tmp/.env.prod
# Ansible reads from /tmp/.env.prod, never logs the contents.
```

Recipients (people who can decrypt) listed in `infra/prod/secrets/.recipients`. Solo dev: just you for now.

---

## 8. Deployment procedures

### 8.1 Production deploy (zero-downtime)

Triggered by approved release tag (§5.4). GitHub Actions runs `deploy-prod.yml`.

```
Step 1: Pre-deploy checks
   ├─ Verify image signatures (cosign)
   ├─ Verify all migrations are idempotent and have downgrade paths (lint)
   ├─ Run final smoke test against staging
   └─ Post "Deploying v<x>" to status page

Step 2: Database migration
   ├─ SSH to db box, take pre-deploy snapshot (instant ZFS-style snapshot via pgBackRest)
   ├─ Run alembic upgrade head against prod DB
   └─ Abort entire deploy if migration fails (snapshot is restore point)

Step 3: Roll app-1
   ├─ Drain app-1 from LB-1 (LB stops sending NEW traffic; existing connections finish)
   ├─ Wait 30s for in-flight requests
   ├─ docker compose pull on app-1
   ├─ docker compose up -d on app-1 (recreates changed containers)
   ├─ Wait for /healthz=200 from app-1 (timeout 60s)
   ├─ Add app-1 back to LB
   └─ Smoke test against app-1 directly (skip LB)

Step 4: Roll app-2 (same as app-1)

Step 5: Post-deploy
   ├─ Run e2e tests against prod (read-only paths only)
   ├─ Mark release on Sentry / Grafana for change-correlation
   └─ Post "Deployed v<x>" to status page
```

If any step fails: deploy halts, on-call alerted, runbook §11.1 applies.

### 8.2 Manual rollback

If the deploy succeeded but bad behavior is observed:

```bash
# From your laptop (or GitHub Actions "rollback" workflow):
./infra/prod/scripts/rollback.sh <previous-version>
# Pulls previous image, runs alembic downgrade to that version's revision, re-rolls app-1 then app-2.
```

If migration cannot be downgraded (e.g., destructive op happened): restore from pre-deploy snapshot per §9.5. This is why the snapshot in §8.1 step 2 exists.

### 8.3 Hotfix deploy (skip staging)

For a P0 (active customer impact): allowed to bypass staging.

```bash
git checkout main
git checkout -b hotfix/T-XXXX-fix-thing
# fix
git push
# Open PR, merge after self-review
make release VERSION=$(date +%Y.%m).hotfix.1
# Approves prod deploy via GitHub Actions immediately
```

After hotfix: open follow-up ticket to backport to staging path and add regression test.

### 8.4 Deploy windows

- **Default**: Tuesday–Thursday 14:00–17:00 UTC (avoid Mondays, Fridays, weekends).
- **Hotfix**: any time.
- **Major version change** (e.g., `v2026.04.0` → `v2027.01.0`): announce 7 days in advance via status page + email.

---

## 9. Backups and restore

### 9.1 Backup strategy summary

| Layer | Tool | Frequency | Retention | Destination |
|---|---|---|---|---|
| Postgres WAL (continuous) | pgBackRest | Continuous (every WAL segment, ~16MB) | 30 days | Hetzner Storage Box (primary) |
| Postgres full | pgBackRest | Daily 02:00 UTC | 30 days daily, 12 weeks weekly, 12 months monthly | Hetzner Storage Box |
| Postgres full (off-site) | pgBackRest | Weekly Sunday 03:00 UTC | 12 weeks | Backblaze B2 (encrypted with age) |
| MinIO objects | `mc mirror` | Daily 04:00 UTC | 30 days | Backblaze B2 |
| Configuration / secrets | git (age-encrypted) | On change | Forever (git history) | GitHub |
| Container images | ghcr.io | On build | Last 50 versions | GitHub Container Registry |

### 9.2 RPO and RTO targets

| Scenario | RPO target | RTO target |
|---|---|---|
| App node failure | 0 (no data loss) | 5 min (LB removes node, other handles) |
| DB failure (recoverable, e.g., reboot) | 0 | 10 min |
| DB total loss, restore from latest WAL | < 1 minute of telemetry | 60 min |
| Region-wide Hetzner outage (catastrophic) | < 24 hours of telemetry | 4 hours (restore B2 backup to fresh region) |

### 9.3 pgBackRest config

`/etc/pgbackrest/pgbackrest.conf` on `db` host:

```ini
[global]
repo1-path=/var/lib/pgbackrest
repo1-type=cifs
repo1-cifs-host=<storage-box-host>
repo1-cifs-share=backups
repo1-retention-full=30
repo1-retention-full-type=time
repo1-bundle=y
repo1-block=y
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=<from secrets>

repo2-type=s3
repo2-path=/yourplatform-pg
repo2-s3-endpoint=s3.us-west-002.backblazeb2.com
repo2-s3-region=us-west-002
repo2-s3-bucket=<bucket>
repo2-s3-key=<from secrets>
repo2-s3-key-secret=<from secrets>
repo2-cipher-type=aes-256-cbc
repo2-cipher-pass=<different from repo1>
repo2-retention-full=12

archive-async=y
archive-push-queue-max=2GiB
process-max=4
log-level-console=info
log-level-file=detail

[yourplatform]
pg1-path=/var/lib/postgresql/16/main
```

Cron entries:

```cron
0 2 * * * postgres pgbackrest --stanza=yourplatform --type=full --repo=1 backup
0 3 * * 0 postgres pgbackrest --stanza=yourplatform --type=full --repo=2 backup
0 4 * * * postgres pgbackrest --stanza=yourplatform expire
```

### 9.4 Verifying backups (automated weekly)

`infra/prod/scripts/verify-backup.sh` runs every Sunday 06:00 UTC via cron on a separate ephemeral Hetzner CX22 (provisioned just for the test):

1. Provision fresh CX22.
2. Install Postgres + pgBackRest.
3. Restore latest backup from Storage Box.
4. Run validation queries: row counts per major table, latest timestamp on `telemetry_data` hypertable.
5. Compare row counts to a sentinel snapshot from prod (≥ 99% match expected).
6. If pass: destroy the CX22, post green to status page internal panel.
7. If fail: page on-call.

This is the **only** way to know backups work. Untested backups don't exist.

### 9.5 Restore procedure (Postgres total loss)

```bash
# 1. Provision new db host (or reuse if salvageable)
cd infra/prod
tofu apply -target=hcloud_server.db

# 2. SSH in, install Postgres + pgBackRest from playbook
ansible-playbook -i inventory.ini playbooks/db.yml --limit=db

# 3. Restore from latest backup
sudo -u postgres pgbackrest --stanza=yourplatform --delta restore

# 4. Apply WAL forward to latest available
sudo systemctl start postgresql
sudo -u postgres psql -c "SELECT pg_wal_replay_resume();"

# 5. Verify
sudo -u postgres psql -d yourplatform -c "SELECT max(time) FROM telemetry_data;"
# Should be within last few seconds.

# 6. Restart app services pointing at restored DB
ansible all -i inventory.ini -m shell -a "cd /opt/yourplatform && docker compose restart"

# 7. Post incident notice with RPO actually achieved
```

### 9.6 Point-in-time recovery (PITR)

For "restore to 2026-04-15 14:23 UTC, just before bad migration":

```bash
sudo -u postgres pgbackrest --stanza=yourplatform \
  --type=time --target="2026-04-15 14:23:00+00" \
  --delta restore
```

### 9.7 MinIO backup

Cron on `app-1`:

```cron
0 4 * * * deploy /usr/local/bin/mc mirror --overwrite --remove minio/yp-exports b2/yourplatform-objects/exports
0 4 * * * deploy /usr/local/bin/mc mirror --overwrite --remove minio/yp-avatars b2/yourplatform-objects/avatars
```

### 9.8 Restore drill (monthly)

First Saturday of every month, 10:00 UTC. **Calendar invite mandatory.**

1. Page yourself.
2. Pretend prod DB is gone.
3. Provision new Hetzner CX22 (fresh, not the verify-backup one).
4. Restore from yesterday's backup per §9.5.
5. Time the procedure end-to-end.
6. If RTO target (60 min) is missed: open ticket to fix what slowed you down.
7. Document in `runbook/drill-log.md`.

---

## 10. Monitoring and alerting

### 10.1 Stack

All open-source. Runs on a separate **monitoring host** (Hetzner CX22, ~€4/mo) so production failures don't blind observability.

| Component | Role |
|---|---|
| Prometheus | Metrics scraping and storage (15-day retention) |
| Grafana | Dashboards |
| Loki + promtail | Log aggregation (30-day retention) |
| Tempo | Distributed traces (7-day retention) |
| Alertmanager | Alert routing |
| Uptime Kuma | External uptime checks (separate provider check) |
| GlitchTip | Sentry-compatible error tracking |

### 10.2 What every service must export

Per [05_CODING_STANDARDS §10] and [02_ARCHITECTURE §11]:

- `/healthz` — liveness (200 if process alive)
- `/readyz` — readiness (200 if ready to serve; checks DB, Redis, NATS connectivity)
- `/metrics` — Prometheus exposition format

Standard metrics every service emits:
- `process_*` (CPU, memory, fds)
- `<service>_requests_total{method,route,status}` counter
- `<service>_request_duration_seconds{method,route}` histogram
- `<service>_in_flight_requests` gauge
- `<service>_dependency_up{dep="postgres|redis|nats|..."}` gauge

Service-specific (defined in [10_TEST_PLAN §8]):
- `ingest_messages_total{source,project_id}`
- `ingest_lag_seconds` — time from device timestamp to ingest receipt
- `nats_publish_total{subject}`
- `worker_jobs_total{queue,status}`
- `worker_job_duration_seconds{queue}`
- `realtime_connections` gauge
- `realtime_subscriptions` gauge

### 10.3 Standard dashboards (in `infra/monitoring/grafana/dashboards/`)

| Dashboard | Audience | Key panels |
|---|---|---|
| Platform Overview | Founder | Active devices, MPS in/out, error rate, latency p95, DB connections, alert count |
| Ingestion Health | Founder | Ingest lag, drop rate, by source (mqtt/http/lora), by project |
| API SLOs | Founder | p50/p95/p99 latency per route, error rate, top slow routes |
| Postgres | Founder | Connections, transactions/sec, replication lag, WAL rate, hypertable size, top queries |
| TimescaleDB | Founder | Chunks per hypertable, compression ratio, continuous aggregate refresh status |
| NATS | Founder | Stream message rate, consumer lag, pending messages |
| EMQX | Founder | Connected clients, message rate, subscription count |
| AI Operations | Founder | LLM calls per day, cost estimate, p95 latency, fallback rate |
| Per-customer (project_id filter) | Customer support | Their device count, MPS, error rate, alert count |

### 10.4 Alert rules

Defined in `infra/monitoring/prometheus/alerts.yml`. Severity → routing in §10.5.

```yaml
groups:
  - name: platform_critical
    rules:
      - alert: APIDown
        expr: up{job="api"} == 0
        for: 2m
        labels: { severity: critical }
        annotations: { runbook: "13_DEVOPS_RUNBOOK §11.1" }

      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels: { severity: critical }
        annotations: { runbook: "13_DEVOPS_RUNBOOK §11.2" }

      - alert: IngestLagHigh
        expr: histogram_quantile(0.95, sum(rate(ingest_lag_seconds_bucket[5m])) by (le)) > 30
        for: 5m
        labels: { severity: critical }
        annotations: { runbook: "13_DEVOPS_RUNBOOK §11.3" }

      - alert: API5xxRateHigh
        expr: |
          sum(rate(api_requests_total{status=~"5.."}[5m]))
            / sum(rate(api_requests_total[5m])) > 0.01
        for: 5m
        labels: { severity: critical }

      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.20
        for: 10m
        labels: { severity: warning }

      - alert: DiskSpaceCritical
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.10
        for: 5m
        labels: { severity: critical }

      - alert: BackupVerificationFailed
        expr: backup_verification_success == 0
        for: 1h
        labels: { severity: critical }

      - alert: TLSCertExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 7 * 86400
        for: 1h
        labels: { severity: warning }
```

### 10.5 Alert routing

Alertmanager → escalation:

- **critical** → Push notification to founder (ntfy.sh or PagerDuty free tier) + email + status page auto-update
- **warning** → Email + Slack/Discord channel
- **info** → Slack/Discord only

Severity SLA:
- `critical`: respond within 15 min, mitigate within 1 hour
- `warning`: respond within 4 business hours
- `info`: review weekly

### 10.6 Status page

`status.<your-domain>` hosted on **Cachet** at a separate provider (e.g., Vultr free tier or Render free tier) so prod failures don't take it down.

Components tracked:
- Web Application
- HTTP API
- MQTT Ingestion
- HTTP Ingestion
- LoRaWAN
- Realtime / WebSockets
- Dashboards
- Rules & Alerts

Auto-updated by Uptime Kuma probes; manual incidents posted by founder.

### 10.7 SLO targets (publicly committed)

| SLO | Target | Measurement |
|---|---|---|
| API availability | 99.5% monthly | successful (non-5xx) HTTP responses |
| Ingestion availability | 99.5% monthly | successful publishes to NATS within 5s |
| Dashboard load p95 | < 1.5s | client-measured TTI |
| Webhook delivery | 99% within 60s | from event published to webhook 2xx |

Error budget = 1 - SLO. When budget burns > 50% in a month, freeze feature deploys, focus on reliability.

---

## 11. Incident runbooks

Every alert annotation points to one of these. Each follows the format: **Symptom → Likely cause → Investigation → Mitigation → Postmortem**.

### 11.1 API is down (alert: APIDown)

**Symptom**: `/healthz` returns non-2xx or no response from one or both app nodes.

**Investigation**:
```bash
# 1. Confirm from outside
curl -i https://api.<domain>/healthz

# 2. Check LB status in Hetzner Cloud console — which targets are unhealthy?

# 3. SSH to affected app node
ssh deploy@app-1.prod
docker compose ps
docker compose logs --tail=200 api

# 4. Check resources
top
df -h
docker stats --no-stream
```

**Likely causes & mitigation**:
- Container OOM-killed → check `dmesg | grep -i kill`. Restart with `docker compose up -d api`. If recurring, increase memory limit in compose file or split workload.
- DB unreachable → check `dependency_up{dep="postgres"}` metric and §11.2.
- Bad deploy → roll back per §8.2.
- Disk full → §11.4.
- Process crashed but not restarted → check `restart: unless-stopped` is set; manually `docker compose up -d api`.

**Mitigation**:
- If only one node affected: drain it from LB (`hcloud load-balancer remove-target lb-1 --server app-1`), let app-2 carry traffic, debug at leisure.
- If both nodes affected: focus on shared dependency (DB, network).

### 11.2 Postgres is down (alert: PostgresDown)

**Symptom**: `pg_up == 0`. Apps logging `connection refused`.

**Investigation**:
```bash
ssh deploy@db.prod
sudo systemctl status postgresql
sudo journalctl -u postgresql --since "1 hour ago"
df -h
free -h
sudo -u postgres psql -c "SELECT 1"     # if responsive at all
```

**Likely causes & mitigation**:
- Disk full (most common) → §11.4. Postgres halts writes when WAL volume fills.
- OOM → check dmesg. Tune `shared_buffers`, `work_mem`. Or upgrade box to CCX23.
- Crashed → `sudo systemctl restart postgresql`. If won't start, check logs for corruption.
- Hung query holding all connections → `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND query_start < now() - interval '5 minutes';`

**Hard recovery**: If DB cannot be restored to working state, restore from backup per §9.5.

### 11.3 Ingestion lag is high (alert: IngestLagHigh)

**Symptom**: p95 of `ingest_lag_seconds` > 30s. Devices' data appears stale on dashboards.

**Investigation**:
```bash
# 1. Where is the bottleneck?
# Check NATS consumer lag:
nats stream report
nats consumer info INGEST telemetry-writer

# 2. Check ingest service throughput
docker compose logs ingest | tail -100

# 3. Check DB write rate
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE state != 'idle' AND query LIKE '%INSERT%telemetry_data%';"
```

**Likely causes & mitigation**:
- One huge customer overwhelming → identify via `ingest_lag_seconds{project_id=...}`. Apply per-project rate limit per [09_SECURITY_SPEC §8].
- DB write saturation → check `pg_stat_io`. If writes are bottleneck, batch size in worker may need tuning. As stopgap, scale worker replicas.
- NATS consumer crashed → restart worker.
- TimescaleDB chunk too large for compression schedule → manually compress: `SELECT compress_chunk(c) FROM show_chunks('telemetry_data', older_than => INTERVAL '1 day') c;`

### 11.4 Disk space critical

**Symptom**: `/` < 10% free.

**Investigation**:
```bash
df -h
sudo du -sh /var/lib/docker/* | sort -h | tail -10
sudo du -sh /var/log/* | sort -h | tail -10
sudo du -sh /var/lib/postgresql/* 2>/dev/null
docker system df
```

**Mitigation (in order)**:
1. `docker system prune -af --volumes` — recovers GBs from old images (be sure no needed images get pruned).
2. `journalctl --vacuum-time=7d` — log truncation.
3. If on `db`: archive old WAL: `sudo -u postgres pgbackrest --stanza=yourplatform expire`. Manually compress old TimescaleDB chunks.
4. Resize Hetzner volume (Hetzner allows online disk resize on Cloud servers): `hcloud volume resize`.
5. If chronic on `db`: schedule larger box upgrade for next maintenance window.

### 11.5 MQTT broker losing clients

**Symptom**: `realtime_connections` drops; customer reports "device disconnected".

**Investigation**:
- EMQX dashboard: http://app-1.prod.internal:18083 → Connections tab.
- `docker compose logs emqx | grep -i "disconnect\|error" | tail -100`.
- Check `node_network_*` metrics for the app node — is bandwidth saturated?

**Likely causes & mitigation**:
- Auth failures (rotated credentials) → check API key validity, see [09_SECURITY_SPEC §6].
- Keepalive too short for device class → publish guidance to customers.
- Broker memory/CPU → scale by adding a third node or upgrade box.
- Network partition between EMQX nodes → restart EMQX cluster (cause of the partition is the real issue).

### 11.6 Webhook deliveries failing

**Symptom**: `worker_jobs_total{queue="webhooks",status="failed"}` rising.

**Investigation**:
- Worker logs filtered to webhooks queue.
- Test target endpoint manually with `curl`.
- Check rate limits per destination.

**Mitigation**:
- If target's fault: backoff is automatic per [07_DATA_CONTRACTS §7]; up to 24h retry. Notify customer.
- If our fault (e.g., bad signing): hotfix per §8.3.

### 11.7 Suspected data breach / unauthorized access

**This is a P0 security incident.** Immediate steps:

1. Do NOT delete logs.
2. Rotate all secrets (DB password, JWT secret, API keys, MinIO keys, SMTP creds): `infra/prod/scripts/rotate-all-secrets.sh`.
3. Force logout all sessions: `UPDATE users SET sessions_invalidated_at = now();`.
4. Review audit logs (`audit_events` table) for the affected period.
5. Snapshot DB and logs for forensics: `pgbackrest backup --type=full --tag=incident-<date>`.
6. If customer data confirmed exposed: trigger breach notification per [09_SECURITY_SPEC §13].
7. Write incident report; publish externally if customer impact confirmed.

### 11.8 LoRaWAN gateway not forwarding

**Symptom**: ChirpStack shows gateway offline; customer's LoRa devices not appearing.

**Investigation**:
- ChirpStack UI → Gateways → status.
- `docker compose logs chirpstack | grep <gateway-id>`.
- Network: gateway must reach `<lb-ip>:1700/udp`. Test from gateway side.

**Mitigation**:
- Ufw blocking 1700/udp on app node → check, allow.
- Gateway misconfigured (wrong server address) → customer fix.
- LB does not forward UDP → confirm LB has UDP rule for 1700 (Hetzner LB supports TCP+UDP).

---

## 12. Secret management

### 12.1 Categories

- **Build secrets** (CI signing keys, registry tokens) → GitHub Actions secrets.
- **Runtime secrets** (DB passwords, JWT secrets, MinIO keys, SMTP, etc.) → age-encrypted file in repo, decrypted at deploy time, written to `/etc/yourplatform/.env` on each host (mode 600, owned by `deploy`).
- **Per-tenant secrets** (customer API keys, LLM provider keys for self-hosted, etc.) → encrypted in DB column with envelope encryption (master key in env).
- **Customer-uploaded secrets** (webhook signing secrets they choose) → hashed, never stored plaintext.

### 12.2 Rotation schedule

| Secret | Rotation cadence | How |
|---|---|---|
| JWT signing key | Quarterly (or on suspected leak) | Generate new, set as `JWT_SECRET`, move old to `JWT_SECRET_PREVIOUS`, deploy. After 7 days remove old. |
| DB password | Quarterly | Create new role with same grants, switch `POSTGRES_DSN`, drop old role. |
| MinIO root | Quarterly | Generate new, deploy, MinIO accepts both during 24h overlap. |
| Customer API keys | On-demand by customer (UI button) | API rotates server-side. |
| TLS certificates | Auto via Caddy ACME (per 60d renewal) | Automatic; alert if renewal fails. |

### 12.3 Suspected leak procedure

§11.7 step 2.

---

## 13. DNS, domains, TLS

### 13.1 Records

Managed in Cloudflare via Terraform (`infra/prod/cloudflare.tf`).

| Type | Name | Value | Proxied | Purpose |
|---|---|---|---|---|
| A | app | LB-1 IPv4 | Yes | Web app |
| AAAA | app | LB-1 IPv6 | Yes | |
| A | api | LB-1 IPv4 | Yes | HTTP API |
| AAAA | api | LB-1 IPv6 | Yes | |
| A | mqtt | LB-1 IPv4 | No (Cloudflare doesn't proxy MQTT) | MQTT broker |
| A | lora | LB-1 IPv4 | No | LoRa gateway endpoint |
| A | status | <separate-vps-ip> | No | Status page |
| A | docs | LB-1 IPv4 | Yes | Public docs |
| MX | (root) | configured to email provider | — | Transactional email |
| TXT | (root) | SPF, DKIM, DMARC | — | Email auth |

### 13.2 TLS

Caddy on each app node handles automatic Let's Encrypt issuance via Cloudflare DNS-01 challenge (so wildcards work, and ports don't need to be open for HTTP-01).

```
# Caddyfile (excerpt)
*.<domain> {
  tls {
    dns cloudflare {env.CLOUDFLARE_API_TOKEN}
  }
  @api host api.<domain>
  reverse_proxy @api api:8000

  @web host app.<domain>
  reverse_proxy @web web:3000

  @ws host realtime.<domain>
  reverse_proxy @ws realtime:8001
}
```

For MQTT (port 8883) Caddy doesn't help — EMQX manages its own TLS via cert files mounted from `/etc/yourplatform/tls/` (renewed by certbot in cron, restart EMQX gracefully on rotation).

### 13.3 Domain admin access

Cloudflare account is on a dedicated email with hardware 2FA. Recovery codes printed and stored in fire safe.

---

## 14. Scaling procedures

### 14.1 Vertical scale (single host)

Hetzner allows online resize for CPU/RAM (requires reboot 30–60s). Disk resize is online.

```bash
hcloud server change-type app-1 cpx41
# Reboot is automatic during type change.
```

Order of preference when resources exhausted:
1. Identify which dependency is the bottleneck via dashboards.
2. Vertical scale that one component first (cheapest, fastest).
3. Horizontal only when vertical exhausted.

### 14.2 Horizontal scale (add app node)

```bash
cd infra/prod
# Edit terraform.tfvars: app_node_count = 3
tofu apply
ansible-playbook -i inventory.ini playbooks/site.yml --limit=app-3
# LB auto-discovers via Hetzner LB target by label.
```

Considerations:
- EMQX cluster: new node auto-joins via cluster discovery DNS.
- NATS cluster: same.
- MinIO: requires manual `mc admin server-side mirror` to rebalance.
- `scheduler`: still leader-elected, no change.

### 14.3 Scale Postgres

Stages, in order:
1. **CCX13 → CCX23** (vertical, online): handles ~10× more telemetry. ~€55/mo.
2. **Add read replica** for dashboard queries. Configure app to route SELECT queries (not telemetry writes) to replica. ~€80/mo.
3. **Move telemetry hypertables to dedicated TimescaleDB instance** (Phase 3+). API and Timescale split.
4. **Consider TimescaleDB multi-node** (Phase 4+) when single node exhausted.

### 14.4 Scale ingestion

When `ingest_lag_seconds` p95 > 5s persistently:
1. Add another `ingest` replica on existing app nodes.
2. If still lagging, dedicate a node to ingestion only.
3. If still lagging, partition NATS streams by project_id ranges and run consumer per partition.

---

## 15. Disaster recovery plan

### 15.1 Defined disasters

| Disaster | Probability | RTO | Plan |
|---|---|---|---|
| Single app node loss | High | 5 min | LB auto-fails over; replace via Terraform |
| DB node loss (recoverable) | Medium | 30 min | Reboot/repair; no data loss |
| DB node loss (unrecoverable) | Low | 60 min | Restore from backup §9.5 |
| Hetzner Falkenstein region outage | Low | 4 hours | Restore B2 backups to Nuremberg region |
| Hetzner total provider outage | Very low | 24 hours | Provision on Vultr/DO from B2 backups |
| Founder unavailable / incapacitated | — | — | §15.3 |
| GitHub down (cannot deploy) | Low | hours | Wait it out; production keeps running |
| Domain registrar account loss | Very low | days | Hardware 2FA + recovery codes mitigate |

### 15.2 Region failover playbook (Hetzner outage)

```bash
# 1. Provision in nbg1 region
cd infra/prod
tofu apply -var hetzner_region=nbg1 -var disaster_mode=true
# Creates fresh app-1, app-2, db in Nuremberg.

# 2. Restore latest backup to new db
ansible-playbook playbooks/db.yml --limit=db-disaster
ansible db-disaster -m shell -a "pgbackrest --stanza=yourplatform --repo=2 restore"

# 3. Update DNS to new LB
# (Terraform does this; takes effect within Cloudflare TTL = 60s)

# 4. Notify customers via status page
# 5. Post-recovery: reconcile any data that was in-flight at outage start.
```

### 15.3 Bus factor (solo dev)

This must be addressed before reaching 10 paying customers:

- Document where every credential is stored (in this runbook §12 + a sealed envelope to a trusted person).
- Have at least one trusted person with break-glass access:
  - Cloudflare account (TOTP delegate)
  - Hetzner account (email-based recovery to a shared address)
  - Domain registrar
  - GitHub org owner
- Maintain a "if I'm gone for 7 days" doc in `OPS/CONTINUITY.md` explaining what to wind down gracefully and how to refund customers.

---

## 16. Routine maintenance schedule

| Cadence | Task |
|---|---|
| Daily | Review alerts dashboard 10 min |
| Daily | Verify backup ran (automated alert if not) |
| Weekly | Review SLO burn rate; review error budget |
| Weekly | Rotate Loki/Tempo old data (auto, but verify) |
| Weekly | Read Hetzner status page, GitHub status, Cloudflare status — proactive incident detection |
| Monthly | Restore drill (§9.8) |
| Monthly | Apt security updates verification (`unattended-upgrades` does it; verify) |
| Monthly | Review user access (anyone left team? rotate their access) |
| Quarterly | JWT secret rotation |
| Quarterly | DB password rotation |
| Quarterly | Postgres `VACUUM FULL` on small lookup tables (off-peak) |
| Quarterly | Review and prune unused container images |
| Annually | Renew TLS certs (auto, but verify and remove old) |
| Annually | Renew domain registration |
| Annually | Pen-test (when revenue justifies, see [09_SECURITY_SPEC §15]) |
| Annually | Disaster recovery full simulation (region failover §15.2 in non-prod) |

---

## Appendix A: Common commands cheatsheet

```bash
# Local
make setup            # first-time
make dev              # run everything for dev
make stop             # stop everything
make test             # run tests
make migrate          # apply migrations
make seed             # seed dev data
make reset            # nuke + reseed
make lint             # all linters
make typecheck        # mypy + tsc

# Staging (from laptop)
ssh deploy@staging.<domain>
gh workflow run deploy-staging.yml

# Prod
ssh deploy@app-1.prod
ssh deploy@app-2.prod
ssh deploy@db.prod
gh workflow run deploy-prod.yml -f version=v2026.04.1
gh workflow run rollback-prod.yml -f version=v2026.03.5

# Postgres ops
ssh deploy@db.prod 'sudo -u postgres pgbackrest --stanza=yourplatform info'
ssh deploy@db.prod 'sudo -u postgres pgbackrest --stanza=yourplatform backup --type=full'

# Logs
ssh deploy@app-1.prod 'docker compose logs -f --tail=100 api'
# Or via Loki:
logcli query '{service="api",environment="prod"} |~ "ERROR"' --since=1h
```

## Appendix B: Network ports

| Port | Protocol | Purpose | Exposed |
|---|---|---|---|
| 22 | TCP | SSH | Public (key-only) |
| 80 | TCP | HTTP (redirects to 443) | Public |
| 443 | TCP | HTTPS | Public |
| 1700 | UDP | LoRa gateway uplink | Public |
| 8883 | TCP | MQTT/TLS | Public |
| 1883 | TCP | MQTT (plain) | **Disabled in prod**; dev only |
| 4222 | TCP | NATS | Internal only (private network) |
| 5432 | TCP | Postgres | Internal only |
| 6379 | TCP | Redis | Internal only |
| 9000 | TCP | MinIO API | Internal only |
| 9001 | TCP | MinIO console | Internal only (SSH tunnel for access) |
| 18083 | TCP | EMQX dashboard | Internal only (SSH tunnel) |
| 9100 | TCP | Prometheus node_exporter | Monitoring host only |

## Appendix C: File and directory layout (production hosts)

```
/opt/yourplatform/             # repo checkout
/etc/yourplatform/             # config and secrets
  .env                         # decrypted runtime env
  tls/                         # certs for non-Caddy services
/var/lib/docker/               # docker volumes, big
/var/lib/postgresql/16/main/   # DB data (db host only)
/var/lib/pgbackrest/           # backup staging area (db host only)
/var/log/yourplatform/         # app logs (rotated by logrotate, also shipped to Loki)
/srv/minio/                    # MinIO data
```

---

> When in doubt, follow this rule: **the only way to know it works is to try it.** Untested backups, untested failovers, untested runbooks — they're not real. Drill regularly.
