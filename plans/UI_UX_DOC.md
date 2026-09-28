# UI_UX_DOC.md — Operational Dashboard Design System

**Project:** AETHER-BUST (SIH26079)
**Binds to:** `PRD.md` §0/§2.6 (bands), `TRD.md` §1.2 (frontend stack), §5 (API).
**Document Version:** 1.0.0
**Design language:** "Operational Meteorological Console" — dark, high-contrast, WMO-aligned, information-dense but scannable.

---

## 0. DESIGN TOKENS (SINGLE SOURCE OF TRUTH)

All tokens live in `frontend/tailwind.config.js` `theme.extend`. Coding agent MUST use token names, never raw hex, in components (except inside the WMO scale definitions in §3, which are canonical arrays).

### 0.1 Base Palette (dark ops theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `bg.base` | `#0B1220` | App background |
| `bg.panel` | `#121C2E` | Panel surfaces |
| `bg.elevated` | `#1A2740` | Cards, popovers |
| `bg.inset` | `#0E1626` | Map container, inputs |
| `border.subtle` | `#233049` | Dividers |
| `border.strong` | `#33507A` | Focus / active |
| `text.primary` | `#E6EDF7` | Primary text |
| `text.secondary` | `#9FB0C9` | Labels |
| `text.muted` | `#5F7291` | Hints |
| `accent.primary` | `#2F81F7` | Interactive / links |
| `accent.focus` | `#58A6FF` | Focus ring |

### 0.2 Semantic Status

| Token | Hex | Meaning |
|-------|-----|---------|
| `status.ok` | `#2EA043` | Healthy / high confidence |
| `status.warn` | `#D29922` | Degraded |
| `status.crit` | `#F85149` | Critical / bust alert |
| `status.info` | `#388BFD` | Informational |

### 0.3 Typography

| Token | Value |
|-------|-------|
| `font.sans` | `"Inter", system-ui, sans-serif` |
| `font.mono` | `"JetBrains Mono", ui-monospace, monospace` (numeric telemetry) |
| `text-xs` | 12px / 16 | `text-sm` 14/20 | `text-base` 16/24 | `text-lg` 18/28 | `text-xl` 20/28 | `text-2xl` 24/32 |

Numeric fields (RMSE, probabilities, lat/lon) MUST use `font.mono` with tabular-nums.

### 0.4 Spacing / Radius / Elevation

- Spacing scale: 4-px base (`1`=4, `2`=8, `3`=12, `4`=16, `6`=24, `8`=32).
- Radius: `rounded-md`=6px (controls), `rounded-lg`=10px (panels), `rounded-xl`=14px (cards).
- Shadow: `shadow-panel` = `0 2px 8px rgba(0,0,0,0.45)`; `shadow-pop` = `0 8px 24px rgba(0,0,0,0.55)`.

---

## 1. LAYOUT ARCHITECTURE — 3-COLUMN OPERATIONAL CONSOLE

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR  (h=56px)  logo · run selector · source(GFS/ECMWF/SYN) · UTC clock ·   │
│                    global mean-confidence pill · health status dot · export ▾  │
├───────────────┬───────────────────────────────────────────────┬────────────────┤
│ LEFT (320px)  │ CENTER (fluid)                                  │ RIGHT (380px)  │
│ COL A         │ COL B — GLOBAL RISK MAP                         │ COL C          │
│ Layer & Var   │  ┌───────────────────────────────────────────┐ │ Deep-Dive +    │
│ Controls      │  │ Leaflet base + deck.gl grid/heatmap overlay│ │ XAI            │
│               │  │  · bust polygons  · legend  · scale bar    │ │                │
│ · Variable    │  └───────────────────────────────────────────┘ │ ┌────────────┐ │
│   selector    │  DAY 1───2───3───4───5───6───7───8───9──10      │ │ Region     │ │
│ · Layer toggle│  ◄ lead-time scrubber (slider) ►  ▶ play        │ │ Telemetry  │ │
│ · Opacity     │  timeline: mini confidence sparkline per day    │ └────────────┘ │
│ · Confidence  │                                                 │ ┌────────────┐ │
│   band filter │                                                 │ │ XAI Factor │ │
│ · Baseline    │                                                 │ │ Breakdown  │ │
│   compare     │                                                 │ └────────────┘ │
├───────────────┴───────────────────────────────────────────────┴────────────────┤
│ BOTTOM STRIP (h=40px) — alerts ticker · inference latency · grid readout (lat,lon,val) │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Column Responsibilities

- **COL A — Control Rail (320px, fixed):** variable selector (t2m/tp/z500/ws850), layer toggle group (Confidence, Bust Probability, Error, + optional predictor overlays Precipitation/Wind/Geopotential), opacity slider, confidence-band filter (multi-select of 5 bands from PRD §2.6), baseline-compare toggle (anomaly vs `historical_baselines`).
- **COL B — Global Risk Map (fluid, min 640px):** Leaflet base map (dark tiles) + deck.gl overlay for the 128×128 grid, bust-blob polygons (GeoJSON), map legend, WMO scale bar, and the **Day 1–10 lead-time scrubber** with play/pause animation.
- **COL C — Deep-Dive + XAI (380px, fixed):** on map click/region select → Region Telemetry card (RMSE/MAE/BF vs baseline) + XAI Factor Breakdown (horizontal bar chart of 10 drivers + Grad-CAM thumbnail + narrative text).

---

## 2. INTERACTION MODEL

### 2.1 Lead-Time Scrubber (core control)

- Discrete slider, 10 stops (Day 1..10). Keyboard: `←`/`→` step, `Home`/`End` jump, `Space` play/pause.
- Playing animates Day 1→10 at 900 ms/frame (configurable 300–2000 ms); loops.
- Each stop shows a mini confidence sparkline (mean confidence per day) above the track; current day highlighted with `accent.focus`.
- Changing the day updates the map overlay AND (if a region is selected) COL C telemetry/XAI for that lead time via `GET /confidence-map`, `POST /bust-probability`, `GET /attribution`.

### 2.2 Map Interactions

- **Hover:** bottom strip shows `lat, lon, value(layer), confidence` (mono, tabular).
- **Click cell:** selects nearest grid cell → snaps lat/lon to grid (PRD §0.1) → drives COL C.
- **Click/drag bbox (shift+drag):** region selection → aggregate RMSE/MAE/BF over bbox → COL C region mode.
- **Bust polygon click:** opens detection popover (peak/mean prob, area, dominant driver, "Explain" → XAI).
- Layer toggles use deck.gl layer visibility; opacity slider maps to layer `opacity` 0.15–0.95.

### 2.3 State Management

- `zustand` store `useConsoleStore`: `{ runId, source, variable, layer, leadTime(1..10), opacity, activeBands[], selection{mode:'none'|'cell'|'region', lat, lon, bbox}, baselineCompare, playing }`.
- `@tanstack/react-query` for server state (runs, confidence-map, bust-probability, attribution, baselines, telemetry) with `staleTime=60s`; query keys include `runId+variable+leadTime+bbox`.

---

## 3. METEOROLOGICAL COLOR SCALES (WMO-ALIGNED, CANONICAL)

Defined once in `frontend/src/theme/colormaps.ts`. Each scale is an ordered array of `{stop:0..1, rgba}` control points; the app interpolates with `d3-scale` `scaleLinear` in RGB. Cool = low risk/high confidence; hot magenta/red = severe bust risk.

### 3.1 `SCALE_CONFIDENCE` (0–100 confidence index; PRD §2.6 bands)

Domain 0→100 mapped to stop 0→1. Higher confidence = cooler/greener; low confidence = red.

| Band | Range | Stop | HEX | RGBA |
|------|-------|------|-----|------|
| VERY_LOW | 0–30 | 0.00 | `#7A0C2E` | `rgba(122,12,46,1)` |
| VERY_LOW | | 0.15 | `#B21E3B` | `rgba(178,30,59,1)` |
| LOW | 30–50 | 0.30 | `#E4572E` | `rgba(228,87,46,1)` |
| MODERATE | 50–70 | 0.50 | `#F2C14E` | `rgba(242,193,78,1)` |
| HIGH | 70–85 | 0.70 | `#8FD14F` | `rgba(143,209,79,1)` |
| VERY_HIGH | 85–100 | 0.85 | `#2EA043` | `rgba(46,160,67,1)` |
| VERY_HIGH | | 1.00 | `#1B6E9B` | `rgba(27,110,155,1)` |

> Rationale: confidence is "good when cool"; the scale runs deep-red (untrustworthy) → amber → green → calm blue (fully trusted), consistent with WMO uncertainty conventions where alarm hues denote low reliability.

### 3.2 `SCALE_BUST_RISK` (0–1 bust probability; the alarm scale)

Domain 0→1. Low risk = cool blue/green; severe = high-alert magenta/red. This is the primary alarm ramp.

| Stop | Level | HEX | RGBA |
|------|-------|-----|------|
| 0.00 | negligible | `#0D3B66` | `rgba(13,59,102,1)` |
| 0.15 | low | `#1B7FA8` | `rgba(27,127,168,1)` |
| 0.30 | low-mod | `#2EB398` | `rgba(46,179,152,1)` |
| 0.45 | moderate | `#9BD64A` | `rgba(155,214,74,1)` |
| 0.55 | elevated | `#F4D03F` | `rgba(244,208,63,1)` |
| 0.70 | high | `#F39C12` | `rgba(243,156,18,1)` |
| 0.82 | severe | `#E8412E` | `rgba(232,65,46,1)` |
| 0.92 | extreme | `#C2185B` | `rgba(194,24,91,1)` |
| 1.00 | extreme+ | `#FF1FA0` | `rgba(255,31,160,1)` |

> The magenta terminus (`#FF1FA0`) is the WMO-style "high-alert" hue reserved for the most severe bust probability, ensuring the worst cells are perceptually dominant.

### 3.3 `SCALE_ERROR_DIVERGING` (signed error δ, for predictor/error overlays)

Diverging around 0 (blue = under-forecast, red = over-forecast). Symmetric domain `[-3τ_v, +3τ_v]` per variable.

| Stop | HEX | RGBA |
|------|-----|------|
| 0.00 | `#053061` | `rgba(5,48,97,1)` |
| 0.25 | `#4393C3` | `rgba(67,147,195,1)` |
| 0.50 | `#F7F7F7` | `rgba(247,247,247,1)` |
| 0.75 | `#D6604D` | `rgba(214,96,77,1)` |
| 1.00 | `#67001F` | `rgba(103,0,31,1)` |

### 3.4 Predictor Overlay Ramps (layer toggles)

| Layer | Scale | Domain | Notes |
|-------|-------|--------|-------|
| Precipitation (`tp`) | `SCALE_PRECIP` | 0–100 mm | `#FFFFFF00`→`#A6D96A`→`#1A9850`→`#313695`→`#762A83` (WMO precip greens→blues→purple) |
| Wind (`ws850`) | `SCALE_WIND` | 0–40 m/s | `#EDF8FB`→`#2CA25F`→`#006D2C`→`#99000D` |
| Geopotential (`z500`) | `SCALE_GEOPOT` | 5400–5900 gpm | `#313695`→`#74ADD1`→`#FFFFBF`→`#F46D43`→`#A50026` |
| Bust Probability | `SCALE_BUST_RISK` | 0–1 | §3.2 |

### 3.5 Accessibility

- All map overlays default `opacity ≤ 0.85` over the dark base to preserve coastline/border legibility.
- A colorblind-safe toggle swaps `SCALE_BUST_RISK` for a viridis-like monotone-luminance ramp (`#440154`→`#31688E`→`#35B779`→`#FDE725`) so severity is decodable by luminance alone.
- Legends always show numeric tick labels (not color alone). Focus rings `accent.focus`, 2px, on all interactive elements. Contrast ≥ WCAG AA for text on `bg.*`.

---

## 4. VISUAL COMPONENT SPECIFICATIONS (per-panel)

### 4.1 Top Bar (`<TopBar/>`)

- Left: logo mark + "AETHER-BUST".
- Center: `<RunSelector/>` (dropdown of `forecast_runs`, shows init_time + source badge), UTC clock (`font.mono`, updates every 1 s).
- Right: `<ConfidencePill/>` (global mean confidence, colored by `SCALE_CONFIDENCE`), `<HealthDot/>` (green/amber/red from `/health`), `<ExportMenu/>` (GeoJSON/GeoTIFF/NetCDF).

### 4.2 Control Rail (`<ControlRail/>`, COL A)

- `<VariableSelector/>`: segmented control, 4 options (t2m, tp, z500, ws850), each with unit sublabel.
- `<LayerToggleGroup/>`: radio for primary layer (Confidence | Bust Probability | Error) + checkboxes for predictor overlays (Precipitation, Wind, Geopotential).
- `<OpacitySlider/>`: 0.15–0.95.
- `<ConfidenceBandFilter/>`: 5 toggle chips (colors from §3.1); hides map cells outside selected bands.
- `<BaselineCompare/>`: switch; when on, map shows anomaly = current − baseline (uses `SCALE_ERROR_DIVERGING`).

### 4.3 Global Risk Map (`<RiskMap/>`, COL B)

- `<LeafletBaseMap/>` dark tiles (CARTO dark_nolabels equivalent, bundled offline tiles for demo determinism), bounds locked to domain (PRD §0.1), `minZoom` fit-to-domain, `maxBounds` = domain bbox.
- `<DeckGridLayer/>`: renders 128×128 values as a `GridCellLayer`/`BitmapLayer` colored by active scale.
- `<BustPolygonLayer/>`: GeoJSON detections, stroke `status.crit`, fill by peak probability.
- `<MapLegend/>`: gradient bar + ticks for active scale.
- `<ScrubberBar/>` (see §2.1) docked below the map.
- `<GridReadout/>` feeds the bottom strip on hover.

### 4.4 Region Telemetry (`<RegionTelemetry/>`, COL C top)

- Header: selection label (cell lat/lon or bbox) + variable + Day n.
- Metric tiles (mono, tabular): `RMSE`, `MAE`, `Bust Frequency`, `Confidence`, each with a baseline delta chip (▲/▼ vs `historical_baselines`, colored by whether worse/better than climatology).
- `<ConfidenceByLeadChart/>`: Recharts line, x=Day 1–10, y=confidence, current day marked.

### 4.5 XAI Factor Breakdown (`<XaiPanel/>`, COL C bottom)

- `<DriverBarChart/>`: Recharts horizontal bar, 10 drivers sorted desc by `score`, bar color by sign (+ = `status.crit`-ish warm, − = `status.info` cool), value labels in %.
- `<GradcamThumb/>`: 128×128 Grad-CAM rendered to a `<canvas>` with `SCALE_BUST_RISK`, overlaid mini-map outline.
- `<NarrativeCard/>`: renders `attribution.narrative` (PRD §3.3.1) in `text-sm`, with the top-2 drivers bolded.

### 4.6 Alerts Ticker (`<AlertsTicker/>`, bottom strip)

- Horizontally scrolling list of latest `system_telemetry` `ALERT` events; `CRITICAL` in `status.crit`, auto-refresh every 15 s.

---

## 5. RESPONSIVE BREAKPOINTS

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| `2xl` | ≥1536px | Full 3-column, both rails fixed (320 / fluid / 380). |
| `xl` | 1280–1535px | Rails 300 / fluid / 340. |
| `lg` | 1024–1279px | COL C collapses to a right drawer (toggle button); map + COL A remain. |
| `md` | 768–1023px | Single column: map full-width; COL A → top sheet; COL C → bottom sheet on selection. |
| `sm` | <768px | Stacked; map first, controls in a modal; scrubber becomes a compact stepper. Not a primary target (ops use ≥ `lg`). |

Primary evaluation target is `xl`/`2xl` (ops workstation). Layout MUST NOT break down to `md` without functional loss of the map.

---

## 6. COMPONENT TREE (`frontend/src/`)

```
src/
├── main.tsx
├── App.tsx
├── theme/
│   ├── tokens.ts            # exports design tokens (mirrors §0)
│   └── colormaps.ts         # SCALE_CONFIDENCE, SCALE_BUST_RISK, SCALE_ERROR_DIVERGING, predictor ramps (§3)
├── store/
│   └── useConsoleStore.ts   # zustand (state §2.3)
├── api/
│   ├── client.ts            # axios instance (baseURL /api/v1)
│   ├── queries.ts           # react-query hooks: useRuns, useConfidenceMap, useBustProbability, useAttribution, useBaselines, useTelemetry, useHealth
│   └── types.ts             # TS types mirroring TRD §5.3 pydantic models
├── layout/
│   ├── TopBar.tsx
│   ├── ThreeColumnLayout.tsx
│   └── BottomStrip.tsx
├── components/
│   ├── controls/
│   │   ├── RunSelector.tsx
│   │   ├── VariableSelector.tsx
│   │   ├── LayerToggleGroup.tsx
│   │   ├── OpacitySlider.tsx
│   │   ├── ConfidenceBandFilter.tsx
│   │   └── BaselineCompare.tsx
│   ├── map/
│   │   ├── RiskMap.tsx
│   │   ├── LeafletBaseMap.tsx
│   │   ├── DeckGridLayer.tsx
│   │   ├── BustPolygonLayer.tsx
│   │   ├── MapLegend.tsx
│   │   ├── ScrubberBar.tsx
│   │   └── GridReadout.tsx
│   ├── telemetry/
│   │   ├── RegionTelemetry.tsx
│   │   ├── MetricTile.tsx
│   │   └── ConfidenceByLeadChart.tsx
│   ├── xai/
│   │   ├── XaiPanel.tsx
│   │   ├── DriverBarChart.tsx
│   │   ├── GradcamThumb.tsx
│   │   └── NarrativeCard.tsx
│   ├── alerts/
│   │   └── AlertsTicker.tsx
│   └── common/
│       ├── Pill.tsx
│       ├── StatusDot.tsx
│       ├── Card.tsx
│       └── SegmentedControl.tsx
└── utils/
    ├── colorScale.ts        # d3-scale interpolation over §3 control points
    ├── grid.ts              # lat/lon <-> (i,j) per PRD §0.1
    └── format.ts            # tabular number/units formatting
```

---

## 7. EMPTY / LOADING / ERROR STATES

| State | Component behavior |
|-------|--------------------|
| Loading run | Skeleton shimmer on map + panels; scrubber disabled. |
| No selection | COL C shows "Select a grid cell or draw a region to inspect drivers." |
| No busts at lead | Map shows uniform confidence; legend notes "No bust polygons at Day n." |
| API error | Inline error card with retry (react-query `refetch`); bottom strip shows `status.crit` dot. |
| Health degraded | Top-bar `HealthDot` amber; tooltip lists `mongo`/`model_loaded` from `/health`. |

---

## 8. ACCEPTANCE (verified in BUILD_PLAN Phases 4–5)

- UX-1: `npm run build` exits 0; bundle produced.
- UX-2: Three-column layout renders at `xl` with map + both rails; Playwright asserts presence of `#risk-map`, `#control-rail`, `#xai-panel`.
- UX-3: Scrubber changes `leadTime` state and triggers a confidence-map refetch (Playwright intercepts the request).
- UX-4: Color scales in `colormaps.ts` match §3 control points exactly (unit test on array values).
- UX-5: Clicking a mock bust polygon opens the detection popover and populates the XAI panel with 10 driver bars.

*End of UI_UX_DOC.md — color scales in §3 are canonical.*
