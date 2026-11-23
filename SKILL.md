---
name: brand-infographics
description: >-
  Create crisp, brand-consistent multi-platform infographics for ANY website,
  newsletter, or social account (Pinterest 2:3, Facebook/IG 4:5, Square/LinkedIn
  1:1, Stories 9:16, Blog 16:9). Supports toggling or combining three engines
  (--engine editorial | ai | hybrid): responsive HTML/CSS + stock photography
  with OKLCH/APCA contrast auditing, pure AI generation with iterative review,
  or hybrid zero-text AI illustration composited into vector HTML typography.
allowed-tools: Read Write Edit Bash
metadata:
  version: 2.0.0
---

# Brand Infographics (`editorial | ai | hybrid`)

## Why This Skill Beats Generic Image-Gen Prompts

Standard "generate an infographic" skills prompt a diffusion model directly for the entire graphic. That breaks down fast on real brand & social workflows: dense bullets warp, percentages misspell, brand hex codes drift, footers morph, and resizing a `2:3` Pinterest pin to `4:5` Facebook chops content off.

This skill upgrades that workflow in **four concrete ways**:
1. **Declarative Brand Onboarding (`brand.json`)**: Lock any site's colors, typography, handle/URL footer, logo, and compliance/disclaimer note once cleanly.
2. **Engine Switching (`editorial | ai | hybrid`)**: Choose crisp deterministic browser typography (`editorial`), creative AI visual metaphors (`ai`), or **both combined (`hybrid`)** — zero-text AI artwork framed inside pixel-exact HTML/CSS grids.
3. **True Multi-Format Layout Reflow**: Flex-column templates re-flow natively across `2:3`, `4:5`, `1:1`, `9:16`, and `16:9` from one JSON spec with an automated Chrome DOM overflow gate (`scrollHeight <= canvasHeight`).
4. **Built-In Accessibility & Visual QA**: Offline Python WCAG 2.1 + APCA `|Lc| >= 75` contrast auditing (`contrast_audit.py`) and batch contact-sheet inspection (`make_contact_sheet.py`).

---

## Operating Modes & Toggle Guide

Always clarify or choose the best `--engine` for the user's goal (and switch or combine freely):

| Flag / Mode | Best Use Cases | Pipeline |
|---|---|---|
| **`--engine editorial`** *(default)* | Data cards, comparisons, checklists, SEO pins, multi-post carousels, strict compliance niches (health/finance/B2B) | Curated stock photo (`stock_search.py`) + responsive HTML/CSS archetype + SVG chart → Chrome `@2x` + Pillow export |
| **`--engine ai`** | Conceptual art, narrative visual metaphors, isometric/illustrated explainers, stylized mood boards | Research (`search_web`) → `ai_prompt.py --engine ai` → native `image-generator` subagent (or Gemini Image CLI) → 10-point multimodal review loop |
| **`--engine hybrid`** *(apply both)* | High-authority pillar posts needing **custom artwork/diagrams/mascots** paired with **razor-sharp small text & brand footer** | `ai_prompt.py --engine hybrid` generates **zero-text artwork** matching card hex → embedded into HTML/CSS JSON spec → Chrome `@2x` multi-platform render |

> **Rule of Thumb**: Never let a pure AI image model render dense paragraphs or multi-column tables (`>35 words`) if crisp readability matters — use **`editorial`** or **`hybrid`** instead. Never ship an **`editorial`** photo strip with baked-in text/watermarks — always inspect thumbnails first!

---

## Interactive Walkthrough (How to Operate Step-by-Step)

### Phase 1 — Onboard the Target Brand (`brand.json`)
Before generating visuals for a user:
1. Ask or inspect the workspace for an existing `brand.json`.
2. If none exists, match a preset (`presets/brands/editorial-warm.json`, `saas-modern.json`, `creator-bold.json`, `clinical-clean.json`) or run `brand_init.py` using the brand's domain/handle, primary/secondary hex colors, fonts, optional logo file, and tone:
   ```bash
   python3 <skill_dir>/scripts/brand_init.py \
     --name "Brand Name" \
     --footer "YOURDOMAIN.COM" \
     --preset editorial-warm \
     --accent "#1B5E52" \
     --logo path/to/logo.png \
     -o brand.json
   ```
3. Audit every foreground/background and badge pair before rendering batches:
   ```bash
   python3 <skill_dir>/scripts/contrast_audit.py --brand brand.json
   ```
   Verify body copy hits **`APCA |Lc| >= 75`** (WCAG `>= 4.5:1`) and headings/pills hit **`|Lc| >= 60`**.

---

### Phase 2 — Gather Verified Facts & Visual Assets
1. **Fact Grounding**: If the topic relies on clinical numbers, market stats, or benchmarks, research first (via `search_web` or verified user docs) and preserve exact figures/limits.
2. **Choose Visual Source by Engine**:
   - **Stock Photography (`editorial` or `hybrid`)**:
     ```bash
     python3 <skill_dir>/scripts/stock_search.py "<clean visual scene query>" \
       --source pexels --orientation portrait --count 3 --download assets/stock/
     ```
     Inspect candidates visually (`read_file` or `make_contact_sheet.py`) to confirm zero baked-in product labels, watermarks, or distracting text.
   - **AI Art Generation (`ai` or `hybrid`)**:
     - If `--engine ai`:
       Build an engineered full-infographic prompt scoped to `brand.json` and platform aspect ratio:
       ```bash
       python3 <skill_dir>/scripts/ai_prompt.py "<topic>" \
         --brand brand.json --type comparison --format pinterest --engine ai --build-prompt
       ```
       Generate via Antigravity's `image-generator` subagent (or standalone CLI `--execute` when `GEMINI_API_KEY` is configured), then run the **10-Point Multimodal Review Rubric** (below) via `read_file`.
     - If `--engine hybrid`:
       Build a **zero-text spot/hero art prompt** locked to the exact `brand.json` card background color:
       ```bash
       python3 <skill_dir>/scripts/ai_prompt.py "<visual subject metaphor>" \
         --brand brand.json --engine hybrid --build-prompt
       ```
       Save the generated clean art PNG/JPG and reference its path inside `"media_path"` of your infographic JSON spec!

---

### Phase 3 — Render & Reflow Across Platforms (`editorial` / `hybrid`)
Use `scripts/render.py` on a single JSON spec or directory of JSON specs (`references/infographic_types.md` documents all 5 responsive archetypes: `ranked-split`, `hero-compare`, `step-pipeline`, `checklist-grid`, `chart-insight`):

```bash
python3 <skill_dir>/scripts/render.py \
  --input path/to/specs/ \
  --brand brand.json \
  --formats pinterest facebook ig-square \
  --out output/
```

**Built-in Layout Safeguards in `render.py`**:
- **Responsive Flex-Column Engine**: Adapts spacing dynamically between `2:3` (`2000×3000`), `4:5` (`1440×1800`), `1:1` (`1080×1080`), `9:16` (`1080×1920`), and `16:9` (`1600×900`) — never stretches fonts or clips footers.
- **Playfair Arrow Guardrail**: Automatically warns or normalizes Unicode `→` inside serif display titles (many editorial serif fonts render `→` as `»`), keeping arrows confined to clean sans-serif body text.
- **Bullet Deduplication**: Never places `•` before `✓` or `✗`.
- **DOM Overflow Check**: Headless Chrome evaluates actual rendered `scrollHeight` vs target canvas height and reports any overflowing pin cleanly before shipping.

---

### Phase 4 — Multimodal QA Verification (Required Before Delivery)
1. For batches (`>= 4` graphics), build a thumbnail contact sheet:
   ```bash
   python3 <skill_dir>/scripts/make_contact_sheet.py --input output/facebook/jpg --out output/qa_sheet.jpg
   ```
2. Visually inspect outputs via `read_file` against the **5-Category / 10-Point Quality Rubric** (pass threshold: `8.5/10` marketing, `7.5/10` social/general):
   - **Visual Hierarchy & Balance (0–2)**: Clean 2-line max display title, scannable focal point, healthy negative space above footer.
   - **Typography & Crispness (0–2)**: Zero text clipping, zero orphan single words, zero AI spelling artifacts.
   - **Data & Accuracy (0–2)**: Exact user/research stats preserved, clear units and labels.
   - **Color & APCA Contrast (0–2)**: Faithful `brand.json` `60-30-10` balance, readable badges, colorblind safety.
   - **Framing & Brand Integrity (0–2)**: Photo crops cleanly (`object-fit: cover`), zero text-on-text collisions, crisp single footer domain/handle + logo.

---

## Script Quick Reference

| Script | Purpose |
|---|---|
| `scripts/brand_init.py` | Create a customized `brand.json` from presets, hex codes, fonts, and footer handle/URL |
| `scripts/contrast_audit.py` | Standalone WCAG 2.1 + APCA (`Lc`) contrast auditor for any `brand.json` |
| `scripts/stock_search.py` | Multi-source Pexels/Pixabay/Unsplash downloader (uses env vars cleanly — zero committed keys) |
| `scripts/ai_prompt.py` | Dual-mode prompt builder (`--engine ai` full graphic vs. `--engine hybrid` zero-text spot art) + optional Gemini API execution |
| `scripts/render.py` | Responsive Chrome `@2x` + Pillow renderer across 5 archetypes and 5 social aspect ratios + DOM overflow check |
| `scripts/make_contact_sheet.py` | Builds labeled QA grid contact sheets from any folder of rendered images |

## Reference Files
- **[references/brand_schema.md](./references/brand_schema.md)** — Full `brand.json` specification & niche adaptation guide
- **[references/platform_formats.md](./references/platform_formats.md)** — Dimensions, safe margins & multi-channel export defaults
- **[references/infographic_types.md](./references/infographic_types.md)** — JSON schema & examples for all 5 responsive archetypes + SVG chart options
- **[references/design_principles.md](./references/design_principles.md)** — `60-30-10` OKLCH tokens, APCA targets, lighting/grain rules, typography pitfalls
