# UI/UX Specification

The visual contract. Every screen, component, interaction, and state. **An AI agent building the frontend treats this as authoritative.** UI references PRD feature IDs; layout references API contracts.

> Tech stack: Next.js 15 (App Router) + React 19 + Tailwind + shadcn/ui + Apache ECharts + MapLibre. See [05_CODING_STANDARDS §4].

---

## Table of contents

- §1 Design system (tokens, components)
- §2 Layout shell
- §3 Authentication pages
- §4 Project overview
- §5 Devices pages
- §6 Streams page
- §7 Dashboards
- §8 Rules pages
- §9 Alerts page
- §10 Settings pages
- §11 Common UI patterns (states, modals, toasts)
- §12 Responsive behavior

---

## 1. Design System

### 1.1 Color tokens (Tailwind config + shadcn theme)

Defined in `tailwind.config.ts` and `app/globals.css` as CSS variables. All colors HSL.

| Token | Light value | Dark value | Usage |
|---|---|---|---|
| `--background` | `0 0% 100%` | `222 47% 8%` | Page background |
| `--foreground` | `222 47% 11%` | `210 40% 98%` | Body text |
| `--card` | `0 0% 100%` | `222 47% 11%` | Card surfaces |
| `--card-foreground` | `222 47% 11%` | `210 40% 98%` | Text on cards |
| `--popover` | `0 0% 100%` | `222 47% 11%` | Popover bg |
| `--primary` | `221 83% 53%` | `217 91% 60%` | Brand primary (blue) |
| `--primary-foreground` | `210 40% 98%` | `222 47% 11%` | Text on primary |
| `--secondary` | `210 40% 96%` | `217 33% 18%` | Secondary surface |
| `--muted` | `210 40% 96%` | `217 33% 17%` | Muted surface |
| `--muted-foreground` | `215 16% 47%` | `215 20% 65%` | Muted text |
| `--accent` | `210 40% 96%` | `217 33% 17%` | Hover accent |
| `--destructive` | `0 84% 60%` | `0 62% 50%` | Errors / destructive |
| `--success` | `142 71% 45%` | `142 71% 45%` | Success / online |
| `--warning` | `38 92% 50%` | `38 92% 50%` | Warning / inactive |
| `--info` | `199 89% 48%` | `199 89% 48%` | Info / neutral |
| `--border` | `214 32% 91%` | `217 33% 18%` | Borders |
| `--input` | `214 32% 91%` | `217 33% 18%` | Input borders |
| `--ring` | `221 83% 53%` | `217 91% 60%` | Focus ring |
| `--chart-1` through `--chart-8` | (palette below) | | Chart series |

**Chart palette (light):** `#3b82f6 #10b981 #f59e0b #ef4444 #8b5cf6 #06b6d4 #ec4899 #84cc16`

**Status colors:**
- Active / online: `--success`
- Inactive / offline: `--warning`
- Disabled: `--muted-foreground`
- Firing alert: `--destructive`
- Acknowledged: `--info`
- Resolved: `--success`
- Snoozed: `--muted-foreground`

### 1.2 Typography

Font stack: Inter (variable, loaded from `next/font`). Mono: JetBrains Mono.

| Token | Size | Line height | Weight | Usage |
|---|---|---|---|---|
| `text-xs` | 12px | 16px | 400 | Captions, labels |
| `text-sm` | 14px | 20px | 400 | Body, table cells |
| `text-base` | 16px | 24px | 400 | Default body |
| `text-lg` | 18px | 28px | 500 | Card titles |
| `text-xl` | 20px | 28px | 600 | Section headers |
| `text-2xl` | 24px | 32px | 600 | Page titles |
| `text-3xl` | 30px | 36px | 700 | Marketing H1 |
| `font-mono` | inherit | inherit | 400 | IDs, code, tokens |

### 1.3 Spacing

Tailwind scale: `0, 1 (4px), 2 (8px), 3 (12px), 4 (16px), 6 (24px), 8 (32px), 12 (48px), 16 (64px)`.

Page-level: `p-6` body padding, `gap-6` between major sections, `gap-4` within cards.

### 1.4 Border radius

| Token | Value | Usage |
|---|---|---|
| `rounded` | 4px | Inputs, badges |
| `rounded-md` | 6px | Buttons |
| `rounded-lg` | 8px | Cards, modals |
| `rounded-xl` | 12px | Hero elements |
| `rounded-full` | 9999px | Avatars, pills |

### 1.5 Elevation (shadows)

| Token | Usage |
|---|---|
| `shadow-sm` | Resting cards |
| `shadow` | Hover state |
| `shadow-md` | Dropdowns |
| `shadow-lg` | Modals |
| `shadow-xl` | Toasts |

### 1.6 Iconography

`lucide-react` exclusively. Standard size: `h-4 w-4` for inline, `h-5 w-5` for buttons, `h-6 w-6` for headers.

Reserved icons:
- `Plus` — create
- `Pencil` — edit
- `Trash2` — delete
- `MoreHorizontal` — overflow menu
- `Eye` / `EyeOff` — show/hide
- `Copy` — copy to clipboard
- `Check` — success
- `X` — close / dismiss
- `AlertCircle` — error
- `AlertTriangle` — warning
- `Info` — info
- `Loader2` (with `animate-spin`) — loading
- `ChevronRight` — navigate
- `ArrowUpRight` — external link

### 1.7 Component library (shadcn/ui)

**Install these primitives** (vendor into `components/ui/`, do not import from npm):

```
button | input | textarea | label | card | dialog | sheet | dropdown-menu
popover | tooltip | toast | tabs | table | badge | avatar | separator
checkbox | radio-group | select | switch | slider | skeleton | alert
form | command | calendar | breadcrumb | scroll-area | progress
```

**Variants standardised:**
- Button variants: `default`, `secondary`, `outline`, `ghost`, `destructive`, `link`
- Button sizes: `default` (h-10), `sm` (h-9), `lg` (h-11), `icon` (h-10 w-10)
- Badge variants: `default`, `secondary`, `outline`, `destructive`, `success`, `warning`

### 1.8 Custom components (project-specific, in `components/`)

Built on top of primitives:

| Component | Path | Purpose |
|---|---|---|
| `<EmptyState>` | `layout/empty-state.tsx` | Standard empty UI |
| `<ErrorState>` | `layout/error-state.tsx` | Error UI with retry |
| `<LoadingState>` | `layout/loading-state.tsx` | Skeletons / spinner |
| `<PageHeader>` | `layout/page-header.tsx` | Title + description + actions |
| `<DataTable>` | `data-table/data-table.tsx` | Tanstack-table wrapper |
| `<StatusBadge>` | `status-badge.tsx` | Device/alert status pill |
| `<RelativeTime>` | `relative-time.tsx` | "5 min ago" auto-updating |
| `<CodeBlock>` | `code-block.tsx` | Copyable code |
| `<CopyButton>` | `copy-button.tsx` | Copy with checkmark feedback |
| `<TimeRangePicker>` | `time-range-picker.tsx` | Relative + absolute |
| `<StreamPicker>` | `stream-picker.tsx` | Searchable multi-select |
| `<DevicePicker>` | `device-picker.tsx` | Searchable multi-select |
| `<ChartLine>` | `charts/chart-line.tsx` | ECharts line chart wrapper |
| `<ChartGauge>` | `charts/chart-gauge.tsx` | Gauge wrapper |
| `<ChartMap>` | `charts/chart-map.tsx` | MapLibre wrapper |
| `<WidgetFrame>` | `widgets/widget-frame.tsx` | Card around any widget with title + menu |
| `<RuleBuilder>` | `rules/rule-builder.tsx` | Rule editor form |
| `<DashboardGrid>` | `dashboards/dashboard-grid.tsx` | react-grid-layout wrapper |

### 1.9 States that every interactive element handles

Every action button, input, list, and card must explicitly handle:

| State | Example |
|---|---|
| `default` | normal resting |
| `hover` | mouse over (subtle bg change) |
| `focus` | keyboard focus (ring) |
| `active` | pressed |
| `disabled` | greyed, no pointer events |
| `loading` | spinner, label may change |
| `error` | red ring + message below |
| `success` | brief checkmark feedback |

For data containers (lists, tables, panels):

| State | Behavior |
|---|---|
| `loading` | Skeleton shapes matching final layout |
| `empty` | `<EmptyState>` with icon, title, action button |
| `error` | `<ErrorState>` with retry button |
| `populated` | Real data |

---

## 2. Layout Shell

### 2.1 Top-level routing

```
/                                  marketing home
/login                             login
/signup                            signup
/forgot-password                   password reset request
/auth/reset                        password reset confirm (?token=)
/verify-email                      email verification (?token=)
/auth/magic                        magic link (?token=)
/onboarding                        first-run tour (post-signup)

/projects/[projectId]              project overview ──┐
/projects/[projectId]/devices                         │
/projects/[projectId]/devices/[deviceId]              │
/projects/[projectId]/dashboards                      │ all under app shell
/projects/[projectId]/dashboards/[dashboardId]        │
/projects/[projectId]/rules                           │
/projects/[projectId]/rules/[ruleId]                  │
/projects/[projectId]/alerts                          │
/projects/[projectId]/alerts/[alertId]                │
/projects/[projectId]/settings                        │
/settings/profile                                     │
/settings/api-keys                                    │
/settings/audit                                       │
/settings/billing                       (Phase 5)     │
```

### 2.2 App shell layout

```
┌────────────────────────────────────────────────────────────────┐
│ TopBar  [Logo]  [Project switcher]    [Search] [Notif] [Avatar]│   ← h-14, sticky
├──────────┬─────────────────────────────────────────────────────┤
│ Sidebar  │  Main content                                       │
│          │                                                     │
│ Nav      │  <PageHeader />                                     │
│ items    │                                                     │
│          │  <PageBody />                                       │
│ w-60     │                                                     │
│          │                                                     │
│ Settings │                                                     │
│ at bottom│                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

**TopBar (h-14, full width, sticky):**
- Left: brand logo + name (links to `/projects/[currentProjectId]`).
- Center-left: project switcher dropdown (Phase 1: shows just the one project, dropdown disabled or hidden).
- Center: command palette trigger (`⌘K`) — opens `<Command>` modal with global search.
- Right: notifications bell (badge with unread count), user avatar (dropdown: profile, settings, logout, theme toggle).

**Sidebar (w-60, fixed left, hidden on mobile):**
Navigation items, top to bottom:
1. Overview (`Home` icon)
2. Devices (`Cpu` icon) + count badge
3. Dashboards (`LayoutDashboard` icon)
4. Rules (`Bell` icon)
5. Alerts (`AlertCircle` icon) + active count badge (red if >0)
6. Insight Console (`Sparkles` icon) — Phase 2
7. Spacer (flex-1)
8. Settings (`Settings` icon) at bottom

Active item: bg `--accent`, left border `--primary` 2px, weight 500.

**Mobile (<768px):**
Sidebar collapses to bottom nav (4 most-used items: Overview, Devices, Dashboards, Alerts). Settings access via TopBar avatar menu.

---

## 3. Authentication Pages

### 3.1 `/login`

```
                       ┌──────────────────────┐
                       │  [Logo]              │
                       │                      │
                       │  Welcome back        │
                       │  Log in to continue  │
                       │                      │
                       │  [Email____________] │
                       │  [Password_________] │
                       │                                                     ☐ Remember me
                       │  [    Log in    ]    │
                       │                      │
                       │  ─── or ───          │
                       │                      │
                       │  [📧 Email magic link]│
                       │                      │
                       │  Forgot password?    │
                       │  Don't have an       │
                       │  account? Sign up    │
                       └──────────────────────┘
```

- Centered card, max-w-md.
- On mobile: full-width with 16px padding.
- Error states: inline below the relevant field, red text, `AlertCircle` icon.
- Loading: button shows `Loader2` + "Logging in...".
- After success: redirect to `/projects/[defaultProjectId]`.

### 3.2 `/signup`

Same shape as login, with fields: Name, Email, Password (with strength meter), Terms checkbox.

Password strength meter:
- 4 segments, fills as criteria met:
  1. ≥12 chars
  2. mixed case
  3. number
  4. symbol

Below: "By signing up you agree to the Terms of Service and Privacy Policy."

### 3.3 `/forgot-password`

Single field (email) + submit button. Always shows "If an account exists, you'll receive an email" regardless of result.

### 3.4 `/auth/reset?token=...`

Two fields (new password, confirm) + same strength meter. On success: "Password updated", auto-redirect to login.

### 3.5 `/verify-email?token=...`

Auto-validates on load. Shows checkmark + "Email verified, redirecting…" on success, error message + "Resend" button on failure.

---

## 4. Project Overview

Route: `/projects/[projectId]`

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│ <PageHeader>                                                │
│   My Project                                  [+ New Device]│
│   12 devices · 1.4M datapoints today · 1 active alert       │
├─────────────────────────────────────────────────────────────┤
│ ┌──── Stat tiles row ─────────────────────────────────────┐ │
│ │ [Devices: 12]  [Active 24h: 11]  [Datapoints: 1.4M]    │ │
│ │ [Active Alerts: 1]                                     │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌──── Recent activity (left) ─── Recent alerts (right) ──┐ │
│ │ • dev_abc sent...           • Cold storage breach     │ │
│ │ • dev_def offline           • Door open >5min         │ │
│ │ • Rule "X" fired                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌──── Quick actions ─────────────────────────────────────┐ │
│ │ [Add Device]  [Create Dashboard]  [Set up Alert]      │ │
│ │ [API Keys]    [Open Docs]                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌──── Welcome / quickstart (collapsible, dismissable) ──┐ │
│ │ Get connected in 4 steps:                             │ │
│ │ ✓ Create account                                      │ │
│ │ ☐ Add your first device                               │ │
│ │ ☐ Send first datapoint                                │ │
│ │ ☐ Create a dashboard widget                           │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

- Stat tiles: 4 columns desktop, 2 columns mobile.
- Recent activity feed: last 20 events.
- Welcome wizard: only visible if any step incomplete; persists to user preferences.

### 4.2 Empty state (no devices yet)

Replace tiles + activity with single call-to-action card:

```
┌─────────────────────────────────────────┐
│            [Cpu icon, large]            │
│      Add your first device              │
│  Connect a sensor to start collecting   │
│  data. Takes about 5 minutes.           │
│                                         │
│        [+ Add Device]                   │
│                                         │
│  Or try the simulator [link]            │
└─────────────────────────────────────────┘
```

---

## 5. Devices Pages

### 5.1 Devices list — `/projects/[projectId]/devices`

```
┌─────────────────────────────────────────────────────────────────────┐
│ Devices                                            [+ Add Device]   │
│ 12 devices · 11 active                                              │
├─────────────────────────────────────────────────────────────────────┤
│ [🔎 Search...]  Status:[All▾]  Label:[Any▾]   Sort:[Last seen▾]  ⚙  │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ●  greenhouse-1-temp                                             │ │
│ │    dev_01H8XGN8R3M2W7Z1B5K8C2N6X4 · 5s ago · 1,440 dp/24h        │ │
│ │    [location: greenhouse-1] [type: sensor]            [Open ▸]   │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ ●  greenhouse-1-humid    ...                                     │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ ⚪ pump-2 (inactive)     ...                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ [Load more...]                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

- Status dot: ● green = active, ⚪ amber = inactive, ⚫ grey = disabled, ✕ red = deleted.
- Each row clickable → device detail.
- Right-click / `⋮` on hover: Quick actions (Disable, Rotate Creds, Delete).
- Search debounced 300ms. Filters update URL params (sharable).
- Pagination: cursor-based. "Load more" or auto-load on scroll bottom.

### 5.2 Add Device modal (sheet from right on desktop, full-screen on mobile)

Multi-step wizard:

**Step 1 — Basics:**
- Name (required, validated for uniqueness as user types)
- Description (optional)
- Labels (key-value editor, can add/remove rows)
- Device profile (dropdown, defaults to "Default JSON")

**Step 2 — Confirm + Generate Credentials:**
- Review summary
- [Create Device] button

**Step 3 — Credentials displayed (one-time):**

```
┌─────────────────────────────────────────────────┐
│ ⚠ Save these credentials now                    │
│   They cannot be shown again. You can rotate    │
│   them later if needed.                         │
├─────────────────────────────────────────────────┤
│ MQTT Username                                   │
│   dev_01H8XGN8R3M2W7Z1B5K8C2N6X4    [Copy]      │
│                                                 │
│ MQTT Password                                   │
│   ••••••••••••••••••••••••••• [👁] [Copy]      │
│                                                 │
│ HTTP Token                                      │
│   ••••••••••••••••••••••••••• [👁] [Copy]      │
│                                                 │
│ Endpoints                                       │
│   MQTT:  mqtt.host.com:8883                     │
│   HTTP:  https://api.host.com/v1/ingest         │
│   Topic up:    v1/prj_.../dev_.../up    [Copy]  │
│   Topic down:  v1/prj_.../dev_.../down  [Copy]  │
├─────────────────────────────────────────────────┤
│ ┌── Quick start: pick a language ──────────────┐│
│ │ [Python] [Node] [Arduino] [HTTP curl]        ││
│ │                                              ││
│ │ ```python                                    ││
│ │ from yourplatform import Client              ││
│ │ client = Client(token="<filled>")            ││
│ │ client.publish({"temperature": 23.5})        ││
│ │ ```                                          ││
│ │ [Copy code]                                  ││
│ └──────────────────────────────────────────────┘│
│                                                 │
│ [I've saved these — Continue]                   │
└─────────────────────────────────────────────────┘
```

### 5.3 Device detail — `/projects/[projectId]/devices/[deviceId]`

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Devices                                                       │
│                                                                 │
│ ● greenhouse-1-temp                          [⋮ Actions]        │
│   dev_01H8...  [📋]   Active · last seen 5s ago                 │
│   Profile: DHT22 · Labels: location=greenhouse-1                │
├─────────────────────────────────────────────────────────────────┤
│  [ Overview ]  [ Streams ]  [ Settings ]  [ Activity ]          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ === Overview tab ===                                            │
│                                                                 │
│ ┌─ Live readings ───┬─ 24h trend (mini-chart) ────────────────┐│
│ │ Temperature 23.5C │  [line chart, last 24h all streams]     ││
│ │ Humidity    58%   │                                          ││
│ │                   │                                          ││
│ └───────────────────┴──────────────────────────────────────────┘│
│                                                                 │
│ ┌─ Recent telemetry table ───────────────────────────────────┐  │
│ │ Time         | Stream      | Value                         │  │
│ │ 10:30:15.234 | temperature | 23.5                          │  │
│ │ 10:30:15.234 | humidity    | 58                            │  │
│ │ ...                                                        │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Streams tab:** table of streams with edit-in-place for `display_name`, `unit`. Click row → stream detail.

**Settings tab:** form with name/description/labels, danger zone (Disable, Rotate Credentials, Delete) at bottom.

**Activity tab:** audit events filtered to this device.

**Actions menu (⋮):** Disable / Enable, Rotate credentials, Copy MQTT topics, Delete.

---

## 6. Streams Page

Route: `/projects/[projectId]/streams/[streamId]`

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Device greenhouse-1-temp                                      │
│ Stream: temperature                                             │
│ str_01H... [📋]   Type: number · Unit: C                        │
├─────────────────────────────────────────────────────────────────┤
│ <TimeRangePicker>     [Bucket▾]   [Aggregation▾]   [Export ▾]   │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────┐  │
│ │                                                            │  │
│ │           [Large line chart, full width]                   │  │
│ │                                                            │  │
│ │                                                            │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│ ┌─ Stats ────────────────┐                                      │
│ │ Min:  -2.1   Max: 28.5 │                                      │
│ │ Avg:  18.3   Last: 23.5│                                      │
│ │ Count: 1,440           │                                      │
│ └────────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

- TimeRangePicker presets: 15m, 1h, 6h, 24h, 7d, 30d, custom (calendar).
- Bucket auto-selected from range; user can override.
- Export: CSV download of points in current view (Phase 1: 10K row limit).

---

## 7. Dashboards

### 7.1 Dashboards list — `/projects/[projectId]/dashboards`

Grid of cards (3-col desktop, 1-col mobile). Each card shows: dashboard name, widget count thumbnail (4 mini-tiles), last updated. Click → dashboard view.

Action: `[+ New Dashboard]` opens modal (name, description) → on create, redirects to dashboard view in edit mode.

### 7.2 Dashboard view — `/projects/[projectId]/dashboards/[dashboardId]`

```
┌─────────────────────────────────────────────────────────────────┐
│ Dashboard name                       [▷ View / ✎ Edit] [⋮]      │
├─────────────────────────────────────────────────────────────────┤
│ <TimeRangePicker> (applies to all widgets)        [⟳ Refresh]   │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────┬─────────┐  ┌──────────────────────────────────┐  │
│ │            │         │  │                                  │  │
│ │  Line chart│ Gauge   │  │  Map (greenhouse positions)      │  │
│ │            │         │  │                                  │  │
│ │  6 cols    │ 3 cols  │  │           3 cols                 │  │
│ │  4 rows    │ 4 rows  │  │           4 rows                 │  │
│ └────────────┴─────────┘  └──────────────────────────────────┘  │
│ ┌──────────────────┬────────────┬────────────────────────────┐  │
│ │                  │            │                            │  │
│ │  Single value    │ Single val │  Table (last 50)           │  │
│ │  4 cols × 2 rows │ 4×2        │  4 cols × 2 rows           │  │
│ └──────────────────┴────────────┴────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Edit mode adds:**
- Each widget gets a drag handle, resize handle, and `[⋮]` menu (Edit / Duplicate / Delete).
- A floating `[+ Add Widget]` button bottom-right.
- Auto-save indicator top-right ("Saved 2s ago" / "Saving…" / "Unsaved").

### 7.3 Add widget flow

Modal:
1. **Pick type**: grid of 5 cards (Line, Gauge, Single Value, Table, Map). Phase 2 adds Bar, Heatmap, Status, Text.
2. **Configure**: form fields specific to the type (see 7.4–7.8).
3. **Preview** (live, on the right of the form on desktop).
4. **[Add to dashboard]**.

### 7.4 Widget config: Line Chart

Fields:
- Title (default "Line chart")
- Streams (multi-pick, ≥1)
- Aggregation: avg/min/max/sum/count/last
- Time range mode: "Use dashboard range" (default) | "Override"
- Override range: (TimeRangePicker)
- Bucket: Auto | 1m | 5m | 1h | 1d
- Show legend: switch (default on)
- Y-axis: Auto | Manual (min/max inputs)
- Color: per-stream picker

### 7.5 Widget config: Gauge

- Title
- Stream (single)
- Min, Max (numeric)
- Color zones (rows of: from, to, color). Default: green up to 70%, amber to 90%, red beyond.
- Show value: switch
- Decimal places: number

### 7.6 Widget config: Single Value

- Title
- Stream (single)
- Label override (default = stream display_name)
- Unit override (default = stream unit)
- Decimal places
- Show sparkline: switch (default on)
- Color thresholds (optional)

### 7.7 Widget config: Table

- Title
- Streams (multi)
- Columns: time, stream, value (toggleable)
- Page size: 10/25/50/100

### 7.8 Widget config: Map

- Title
- Mode: "Single location stream" | "Lat + Lng pair"
- If single: pick location-type stream
- If pair: pick lat stream, lng stream
- Show trail: switch + history length
- Map style: Streets | Satellite | Dark

### 7.9 Dashboard interaction

- Hovering any data point on a chart highlights matching timestamps in other widgets (cross-hair sync, Phase 2).
- WebSocket updates: new datapoints stream into widgets; charts append point and shift x-axis.
- "Pause live updates" toggle in time range picker for stable inspection.

---

## 8. Rules Pages

### 8.1 Rules list — `/projects/[projectId]/rules`

Table view:
| Status | Name | Trigger | Last fired | Fires (24h) | Actions |
|---|---|---|---|---|---|
| ● Enabled | Cold storage breach | temp > -15 | 10m ago | 3 | [⋮] |
| ⚪ Disabled | Test rule | ... | never | 0 | [⋮] |

Top right: `[+ New Rule]`.

### 8.2 Rule builder — `/projects/[projectId]/rules/new` and `/[ruleId]/edit`

Two-pane layout (form left, live preview right):

```
┌─────────────────────────────┬───────────────────────────────┐
│  Rule details               │  Preview                      │
│                             │                               │
│  Name [____________]        │  Last 24h matching this rule: │
│  Description [_____]        │                               │
│                             │  ┌───────────────────────┐    │
│  Scope                      │  │ [chart with overlays  │    │
│  Devices [picker]           │  │  showing where rule   │    │
│  Stream keys [chips]        │  │  would have fired]    │    │
│                             │  └───────────────────────┘    │
│  Trigger                    │                               │
│  Type [Threshold ▾]         │  3 fires would have occurred  │
│  Stream key [temperature ▾] │  in the last 24h.             │
│  Comparator [> ▾] [-15  ]   │                               │
│  Window [10 min ▾]          │                               │
│  Aggregation [all ▾]        │                               │
│                             │                               │
│  Actions                    │                               │
│  [+ Add action]             │                               │
│  ┌───────────────────────┐  │                               │
│  │ ✉ Email               │  │                               │
│  │ to: [_____________]   │  │                               │
│  │ [Test send]  [Remove] │  │                               │
│  └───────────────────────┘  │                               │
│  ┌───────────────────────┐  │                               │
│  │ 🔗 Webhook            │  │                               │
│  │ URL: [____________]   │  │                               │
│  │ Secret: [auto-gen][↻] │  │                               │
│  │ [Test send]  [Remove] │  │                               │
│  └───────────────────────┘  │                               │
│                             │                               │
│  Debounce [30 min ▾]        │                               │
│  Auto-resolve [Off ▾]       │                               │
│                             │                               │
│  [Save & Enable]            │                               │
│  [Save as Disabled]         │                               │
└─────────────────────────────┴───────────────────────────────┘
```

Validation:
- Show inline errors as user moves between fields.
- "Save" disabled until all required fields valid.
- Preview updates 1s after last edit (debounced API call).

---

## 9. Alerts Page

### 9.1 Alerts list — `/projects/[projectId]/alerts`

```
┌─────────────────────────────────────────────────────────────────┐
│ Alerts                                                          │
│ 1 firing · 4 acknowledged · 287 resolved (last 30d)             │
├─────────────────────────────────────────────────────────────────┤
│ State:[All▾] Rule:[Any▾] Time:[Last 24h▾]                       │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔴 Cold storage breach                  10 min ago          │ │
│ │ Rule: Cold storage breach · Temp -10.5C > -15 (5 readings)  │ │
│ │ Device: dev_abc                                             │ │
│ │ [Acknowledge]  [Resolve]  [Snooze ▾]  [Open ▸]              │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ 🟡 Door open >5min (acknowledged)        1h ago             │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ 🟢 Tank level low (resolved)             yesterday          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

Click row → opens alert detail in slide-over panel (sheet from right).

### 9.2 Alert detail panel

Sections:
- Header: state badge, rule name, fired time
- Trigger info: triggering value, threshold, device, stream
- Mini-chart: stream values around fire time (±15 min)
- Actions: Acknowledge / Resolve / Snooze (with duration picker)
- Delivery log: each delivery attempt with channel, status, time, error
- Related alerts: same rule, same device, last 30d

---

## 10. Settings Pages

### 10.1 Profile — `/settings/profile`

Form: Name, Email (with "Change email" button), Timezone (autodetect, editable), Locale, Theme (light/dark/system), Change Password section.

### 10.2 API Keys — `/settings/api-keys`

Table: Name, Prefix (yp_live_AbCd...), Scopes (chips), Created, Last used, Expires, Actions ([Revoke]).

`[+ New API Key]` opens modal: Name, Scopes (checkboxes: read/write/admin), Expires (Never/Custom).

After creation, one-time display of full key with `[Copy]` button and warning.

### 10.3 Audit Log — `/settings/audit`

Table: Time, Actor, Action, Target, Details (expandable JSON). Filters: Action type, Actor, Date range.

### 10.4 Project Settings — `/projects/[projectId]/settings`

Sections:
- General (name, description)
- Retention (days, slider 1-365 or per tier max)
- Webhooks (Phase 2)
- Members (Phase 3)
- Danger zone (Delete project, requires text confirmation)

---

## 11. Common UI Patterns

### 11.1 Toasts

Position: bottom-right desktop, top mobile.
Variants: `default`, `success`, `error`, `warning`.
Auto-dismiss: 5s for default/success, 8s for warning, manual for error.
Action button optional ("Undo", "View").

### 11.2 Modals vs sheets

- **Modal (centered)**: confirmations, single-step forms, displaying credentials.
- **Sheet (slide-in from right)**: multi-step forms, detail panels, anything wider than 600px on desktop.
- **Mobile**: both render as bottom sheets.

### 11.3 Confirmation dialogs

For destructive actions:
- Title: action verb + object ("Delete device greenhouse-1-temp?")
- Description: consequences ("This will stop ingestion. Telemetry data will be retained for 30 days then permanently deleted.")
- For high-stakes: typed confirmation (user types device name).
- Cancel button left, destructive button (red) right.

### 11.4 Loading patterns

- **Initial page load**: full-page skeleton matching final layout.
- **Filtered/refetched data**: skeleton replaces only the changing section; rest remains interactive.
- **Inline action (button)**: spinner in button, button disabled.
- **Save/auto-save**: small "Saving…" indicator near the affected section, becomes "Saved" on success.

### 11.5 Empty states

Pattern (from `<EmptyState>`):
```
[Icon, large, muted]
Title (text-lg, semibold)
One-line description (text-sm, muted)
[Primary action button]
[Secondary link if applicable]
```

Each major surface has a designed empty state. No "No data" plain strings.

### 11.6 Error states

Pattern (from `<ErrorState>`):
```
[AlertCircle icon, large, destructive]
Something went wrong (text-lg)
[Specific error message] (text-sm, muted)
[Try again]   [Report issue]
```

For 404: "Page not found" + link to dashboard. For 403: "You don't have access".

### 11.7 Keyboard shortcuts

Global:
- `⌘K` / `Ctrl+K` — command palette
- `g d` — go to devices
- `g h` — go to dashboards
- `g r` — go to rules
- `g a` — go to alerts
- `g s` — go to settings
- `?` — show shortcut help

Within editors:
- `⌘S` — save (also auto-saves on blur)
- `Esc` — close modal / cancel edit

### 11.8 Copy-to-clipboard

`<CopyButton>` component:
- Default: copy icon, hover tooltip "Copy".
- On click: icon swaps to checkmark for 1.5s, tooltip "Copied!".
- Used for: IDs, tokens, URLs, code snippets.

### 11.9 Status badges

`<StatusBadge>` colors per status enum from [04_GLOSSARY §3]:
- `active` / `firing` (when negative): destructive bg, white text
- `active` (positive context): success bg, white text
- `inactive` / `acknowledged`: warning bg
- `disabled` / `snoozed`: muted bg
- `resolved`: success bg, subtle

---

## 12. Responsive Behavior

### 12.1 Breakpoints (Tailwind defaults)

| Name | Min width | Layout impact |
|---|---|---|
| `sm` | 640px | Forms become 2-col |
| `md` | 768px | Sidebar appears; 2-col layouts |
| `lg` | 1024px | 3-col grids |
| `xl` | 1280px | Wider max-width content |
| `2xl` | 1536px | Optional 4-col grids |

### 12.2 Mobile adaptations

- Sidebar → bottom navigation bar (4 items).
- Sheets → bottom sheets.
- Tables → cards (each row becomes a card with key:value pairs).
- Action buttons in headers → kebab menu.
- Time range picker → simplified (presets only, "Custom" opens modal).
- Dashboards: widgets stack 1-col; resize/drag disabled; users see "Edit on desktop" hint when tapping edit.

### 12.3 Touch targets

Minimum 44×44px for all interactive elements on mobile.

### 12.4 Print

Dashboards have a `?print=1` mode: hides nav, expands widgets to full width, pagebreak between widgets.
