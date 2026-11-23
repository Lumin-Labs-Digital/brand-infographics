# Infographic Archetypes & JSON Input Schema

`scripts/render.py` supports **5 responsive HTML/CSS archetypes**. Every archetype adapts cleanly across `pinterest` (`2:3`), `facebook`/`ig-portrait` (`4:5`), `ig-square` (`1:1`), `story` (`9:16`), and `blog` (`16:9`).

---

## Common Top-Level JSON Fields

```json
{
  "slug": "hydration_science_guide",
  "archetype": "hero-compare",
  "title": "How Much Water Daily?<br>Busting the Strict '8 Glasses' Myth",
  "subtitle": "Pale-straw urine cues, produce & coffee credits, and sweat sodium balance",
  "media_path": "assets/stock/lemon_water.jpg",
  "media_kicker": "Physiology Myth Check",
  "media_caption": "Coffee, Produce & Electrolytes All Count Toward Daily Hydration",
  "bottom_title": "Taper Fluids 90m Pre-Bed · Medical Caps",
  "bottom_points": [
    "<strong>Front-Load Before 6 PM:</strong> Drinking ~70% of fluids earlier stops nighttime wakeups.",
    "<strong>Clinical Exception:</strong> Heart failure or dialysis plans require physician fluid caps."
  ]
}
```

---

## The 5 Supported Archetypes (`"archetype"`)

### 1. `ranked-split`
Best for ranking tiers, evidence strength, priority lists, or tool audits alongside a tall portrait image.
- **`bento_heading`**: Section label above ranked items.
- **`rows`**: `[{ "badge": "STRONG", "title": "...", "desc": "...", "tone": 0 }]` (`tone` indexes into `brand.colors.accents`).
- **`section_heading`** + **`cards`**: `3–4` bottom rule/action cards `[{ "title": "...", "desc": "...", "tone": 1 }]`.

### 2. `hero-compare`
Best for Myth vs. Fact, Before vs. After, Old Way vs. New Way, or Tool A vs. Tool B comparisons.
- **`media_path`** renders inside a wide top photo strip with crisp gradient caption overlay (`media_kicker`, `media_caption`).
- **`left_panel`** & **`right_panel`**: `{ "kicker": "...", "title": "...", "tone": 3, "items": ["✓ ...", "✗ ..."] }`.
- **`section_heading`** + **`cards`**: `3` horizontal summary cards `[{ "title": "...", "desc": "...", "tone": 0 }]`.

### 3. `step-pipeline`
Best for 3-stage protocols, morning/evening routines, onboarding checklists, or numbered workflows.
- Top wide **`hero_strip`** (`media_path`, `media_kicker`, `media_caption`).
- **`top_heading`** + **`steps`**: `3` top stage cards `[{ "kicker": "STEP 1", "title": "...", "desc": "...", "tone": 0 }]`.
- **`section_heading`** + **`cards`**: `4` grid follow-up rules `[{ "title": "...", "desc": "...", "tone": 1 }]`.

### 4. `checklist-grid`
Best for "Top 6 Signals", "6-Step Routine", or modular symptom/feature audits.
- Optional **`media_path`** wide strip at top.
- **`top_heading`** + **`grid_items`**: `6` numbered 2-column matrix cards `[{ "title": "...", "desc": "...", "tone": 0 }]`.
- **`section_heading`** + **`cards`**: `3` takeaway pillars below.

### 5. `chart-insight`
Best for time-series curves, benchmark bars, or comparative trends without relying on hallucinated AI chart labels.
- **`chart`**: Inline vector SVG data spec rendered crisply in HTML:
  ```json
  "chart": {
    "title": "Overnight Curve vs. Benchmark",
    "series": [
      { "label": "Baseline", "color_idx": 0, "points": [100, 100, 102, 118, 145] },
      { "label": "Rebound", "color_idx": 3, "points": [100, 82, 62, 105, 148] }
    ],
    "x_labels": ["12 AM", "1:30 AM", "3 AM", "5:30 AM", "8 AM"],
    "y_min": 50,
    "y_max": 160
  }
  ```
- Followed by side-by-side **`left_panel`** / **`right_panel`** breakdown cards + **`bottom_points`**.
