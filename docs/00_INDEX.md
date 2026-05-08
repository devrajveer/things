# Documentation Index

This is the map of every document in the project. Read in this order on first pass.

## Document hierarchy

```
TIER 0 — STRATEGY (read once, refer rarely)
  01_STRATEGIC_BLUEPRINT.md    Why this product exists, business model, GTM, phases
  02_ARCHITECTURE.md            System architecture, monorepo, layered design

TIER 1 — FOUNDATION (every other doc depends on these)
  00_INDEX.md                   This file (the entry point)
  04_GLOSSARY.md                Terms, IDs, enums (single source of truth)
  05_CODING_STANDARDS.md        How code is written across all languages

TIER 2 — CONTRACTS (the agent must obey these literally)
  06_PRD.md                     What gets built (features + acceptance criteria)
  07_DATA_CONTRACTS.md          API endpoints, DB schema, event schemas
  08_UI_UX_SPEC.md              Design system + every page

TIER 3 — CROSS-CUTTING (referenced by all build work)
  09_SECURITY_SPEC.md           Auth, authz, hardening, threat model
  10_TEST_PLAN.md               What to test, how, where
  11_CONFIGURATION_REFERENCE.md All environment variables and config

TIER 4 — INTERFACES (consumed by external developers)
  12_CLIENT_INTERFACES_SPEC.md  SDK + CLI APIs

TIER 5 — OPERATIONS
  13_DEVOPS_RUNBOOK.md          Dev setup, staging deploy, prod deploy, ops

TIER 6 — EXECUTION PLAN (for the AI coding agent)
  14_IMPLEMENTATION_PLAYBOOK.md Sprint-by-sprint, ticket-by-ticket build order
```

## How an AI coding agent should use this

For any task, consult docs in this order:

1. **`14_IMPLEMENTATION_PLAYBOOK.md`** — find the current ticket, read its acceptance criteria
2. **`04_GLOSSARY.md`** — confirm naming for any entity, ID, or enum used
3. **`05_CODING_STANDARDS.md`** — apply code conventions for the language
4. **`06_PRD.md`** — confirm the feature behavior expected
5. **`07_DATA_CONTRACTS.md`** — for any API endpoint, DB table, or event involved
6. **`08_UI_UX_SPEC.md`** — for any UI work
7. **`09_SECURITY_SPEC.md`** — for any auth, authz, or sensitive data work
8. **`10_TEST_PLAN.md`** — write tests matching the layer's standard
9. **`11_CONFIGURATION_REFERENCE.md`** — for any new env var or config

If a contradiction is found between docs: stop and surface it. Do not invent a resolution.

## Documentation conventions

- **Markdown only.** All docs in `.md`. Diagrams in ASCII for source readability; renderable Mermaid for visual.
- **Fenced code blocks always typed:** ` ```python `, ` ```sql `, ` ```typescript `, ` ```yaml `, ` ```bash `, ` ```json `.
- **Cross-references** use the form `[06_PRD §3.2]`. Section numbers stay stable across versions.
- **Versioning:** docs are versioned in git with the code they describe. Breaking changes to contracts go in CHANGELOG.md with a `BREAKING:` prefix.
- **Authority order on conflict:** Glossary > Data Contracts > PRD > UI/UX > Implementation Playbook > Architecture > everything else.

  Rationale: the Glossary defines terminology, the Contracts define the wire-level agreements, the PRD defines what gets built, the UI/UX spec defines how it looks. The Playbook sits above Architecture because it describes the concrete build order and paths the agent will follow — Architecture illustrates intent, Playbook commits to specifics.

## Canonical monorepo directory convention

**This section is the single source of truth for top-level directory placement.** If any doc disagrees, it is wrong — fix the doc, not the convention.

The monorepo uses a **three-way top-level split**:

| Directory | Purpose | What goes here | What does NOT go here |
|---|---|---|---|
| `services/` | Backend processes — headless daemons deployed as containers, communicating over NATS/HTTP. Mostly Python. | `api`, `ingest`, `realtime`, `worker`, `ai-worker`, `scheduler`, `_shared` (Python base package) | Anything a human runs directly; anything distributed to end users |
| `apps/` | User-facing surfaces — things humans or external consumers interact with directly. | `web` (Next.js), `cli` (Typer), `docs` (Astro Starlight) | Background processes; libraries; SDKs |
| `packages/` | Libraries — code consumed by other code, not run standalone. Published to PyPI, npm, Arduino Library Manager, etc. | `sdk-py`, `sdk-js`, `sdk-arduino`, `shared-ts`, `shared-types`, `ui-components`, `codecs` | Deployable processes; executables; anything with a `main` entrypoint that runs a server |

**Import rules (enforced by lint):**

- `packages/*` can be imported by anyone.
- `apps/*` and `services/*` never import from each other (cross-layer coupling is forbidden).
- `apps/*` and `services/*` are both free to import from `packages/*`.
- Internal Python package names use the `yp_` prefix (e.g., `yp_api`, `yp_shared`, `yp_cli`) to avoid collisions with community packages.
- Internal TypeScript packages use the `@yourplatform/` npm scope.

**If a new top-level concept is proposed** (e.g., `tools/`, `scripts/`): it is scaffolding, not one of the three primary dirs. Keep it clearly distinct in name and never mix with `services/`, `apps/`, or `packages/`.

## Status of each document

| # | Document | Status | Owner |
|---|---|---|---|
| 00 | Index | Living | All |
| 01 | Strategic Blueprint | Locked | Founder |
| 02 | Architecture | Locked | Founder |
| 04 | Glossary | Locked v1 | Founder |
| 05 | Coding Standards | Locked v1 | Founder |
| 06 | PRD | Locked v1 (Phase 1), Outline (Phase 2+) | Founder |
| 07 | Data Contracts | Locked v1 (Phase 1) | Founder |
| 08 | UI/UX Spec | Locked v1 | Founder |
| 09 | Security Spec | Locked v1 | Founder |
| 10 | Test Plan | Locked v1 | Founder |
| 11 | Configuration Reference | Locked v1 | Founder |
| 12 | Client Interfaces Spec | Locked v1 | Founder |
| 13 | DevOps Runbook | Locked v1 | Founder |
| 14 | Implementation Playbook | Locked v1 (Phase 1) | Founder |

"Locked" = no changes without ADR. "Living" = updated as needed with PRs.