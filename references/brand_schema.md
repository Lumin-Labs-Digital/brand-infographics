# Brand Profile Specification (`brand.json`)

Every graphic created by `brand-infographics` reads a declarative `brand.json` configuration instead of hardcoding domain names, logos, or hex swatches inside Python scripts.

---

## Full `brand.json` Schema

```json
{
  "brand_name": "Northstar Coaching",
  "footer_label": "NORTHSTARCOACH.IO",
  "logo_path": "assets/logo-transparent.png",
  "tone": "calm, data-backed editorial authority",
  "niche": "fitness & nutrition",
  "fonts": {
    "heading": "'Playfair Display', Georgia, serif",
    "body": "'Inter', system-ui, -apple-system, sans-serif",
    "label": "'Space Grotesk', system-ui, sans-serif",
    "google_fonts": "Playfair+Display:wght@700;900&family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@700",
    "local_dir": ""
  },
  "colors": {
    "ground": "#F6F3EC",
    "card": "#FCFBF7",
    "card_subtle": "#F4F1EA",
    "ink_primary": "#182B26",
    "ink_secondary": "#3D5049",
    "footer_bg": "#FAF8F4",
    "footer_ink": "#243447",
    "banner_bg": "#182B26",
    "banner_kicker": "#8BD1C2",
    "banner_ink": "#E8EEF5",
    "accent_primary": "#1B5E52",
    "accents": ["#1B5E52", "#1E3A5F", "#7B4F12", "#8E2B2A", "#5B3256"]
  }
}
```

### Field Notes
- **`footer_label`**: Uppercased brand URL, handle (`@username`), or publication name centered inside the `84px` footer strip. Never duplicate this inside a top banner pill.
- **`logo_path`**: Optional path to a transparent PNG or SVG logo mark (`64×64px` right-aligned inside the footer). If empty or missing on disk, the footer centers `footer_label` cleanly without broken image boxes.
- **`fonts.local_dir`**: If set (e.g., to a folder containing `PlayfairDisplay-Black.ttf`, `Inter-Regular.ttf`, etc.), `render.py` embeds local `@font-face` rules so Chrome works **100% offline** in airgapped sandboxes. If left empty, `render.py` includes Google Fonts `@import` with graceful system fallbacks.
- **`colors.accents`**: An ordered list of 3–5 mid-dark accent hex values calibrated for equal perceived weight (`OKLCH L ~ 0.35–0.49`) so white pill labels and card borders stay accessible (`WCAG >= 4.5:1`, `APCA |Lc| >= 75`). Always run `python3 scripts/contrast_audit.py --brand brand.json` after editing colors.
