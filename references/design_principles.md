# Design Principles & Perceptual Color Discipline

These studio standards turn generated graphics from "template clutter" into authoritative editorial media across both **`editorial`** and **`hybrid`** modes.

---

## 1. The `60-30-10` Tonal Rule & OKLCH Calibration
- **60% Quiet Ground**: Use warm parchment (`#F6F3EC`) or cool mist (`#F2F5F7`) — avoid glaring `#FFFFFF` screens or neon gradient backgrounds that fatigue eyes on mobile.
- **30% Elevated Structure**: Crisp alabaster cards (`#FCFBF7` / `#FFFFFF`), `1px` specular top border edges, soft 3-stop ambient shadows, and deep ink charcoal/navy typography (`#152536`).
- **10% Curated Editorial Accents**: 3–4 balanced accents sharing calm saturation (`OKLCH C <= 0.12`, lightness `L ~ 0.35–0.49`) so sibling cards feel part of one visual family.

## 2. Accessibility Targets (WCAG 2.1 + APCA `Lc`)
- **Body Text (`14–18px`)**: Target **`APCA |Lc| >= 75`** (and `WCAG >= 4.5:1`).
- **Display Headlines & Pill Badges**: Target **`APCA |Lc| >= 60`** (`bold >= 700`).
- Verify every token pair automatically with:
  ```bash
  python3 scripts/contrast_audit.py --brand your-brand.json
  ```

## 3. Typography & Micro-Detailing Rules
- **Two-Line Hero Budget**: Size display H1 headings (`44–48px`) and copy length cleanly (`<= 58 characters`) so titles frame crisp **2 lines** without colliding into hero banners.
- **Serif Glyph Guardrail**: Display serif fonts like `Playfair Display` often render Unicode `→` as `»`. Always use words (`"to"`) or hyphens inside serif `<h1>`/`<h2>`/`<h3>` tags; keep `→` confined to `Inter` sans-serif body text.
- **Zero Bullet Stacking**: Use `✓`, `✗`, OR `•` cleanly — never stack `• ✓`.
- **Single Branding Anchor**: Lead cleanly with the headline (skip noisy oval category pills above titles), and anchor brand URL/handle + optional logo once inside the bottom `84px` footer strip.

## 4. Photography & AI Art Integration (`editorial` vs. `hybrid`)
- **Inspect Stock Photos Visually**: Reject images containing baked-in marketing text, bottle slogans, or watermarks.
- **Harmonize AI Spot Illustrations (`hybrid` mode)**: Always instruct the image generator for **`ZERO text, zero letters, flat uniform background matching <card hex>`** and feather/frame cleanly inside `.side-photo` or `.photo-strip` containers.
- **Environmental Depth**: Pair subtle top-left radial illumination (`rgba(255,255,255,0.68)` fading out) with subtle paper grain (`opacity: 0.03`) for print-grade tactility.
