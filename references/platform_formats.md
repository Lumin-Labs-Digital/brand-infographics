# Multi-Platform Format & Aspect Ratio Guide

Cropping a tall `2:3` infographic into `4:5` or `1:1` destroys footers, splits charts, and reduces mobile text size. Instead, `render.py` reflows the **exact same content JSON** at native canvas aspect ratios using responsive flex-column grids.

---

## Supported Format Presets (`--formats`)

| Preset Name | Social Channels | Ratio | CSS Canvas | Export Output (`PNG` & `JPG`) | Typical Height Rule |
|---|---|---|---|---|---|
| **`pinterest`** | Pinterest Standard Pins, Idea Pins | `2:3` | `1000 × 1500` | `2000 × 3000` | Full 3–4 section vertical narrative |
| **`facebook`** | Facebook Vertical Feed (`4:5`) | `4:5` | `1200 × 1500` | `1440 × 1800` | Widened `1200px` cards unwrap long lines neatly without dropping sections |
| **`ig-portrait`** | Instagram Feed Portrait (`4:5`) | `4:5` | `1200 × 1500` | `1080 × 1350` | Same native `4:5` reflow exported at exact `1080 × 1350` IG feed spec |
| **`ig-square`** | Instagram Carousel, LinkedIn Feed, X/Threads | `1:1` | `1080 × 1080` | `1080 × 1080` *(or `1440 × 1440`)* | Compact padding; best paired with `ranked-split`, `hero-compare`, or 3-card grids |
| **`linkedin`** | LinkedIn Document/Carousel Slide | `4:5` | `1200 × 1500` | `1440 × 1800` | High-contrast scannable executive summary |
| **`story`** | Instagram Stories, Reels Covers, TikTok Slides | `9:16` | `1000 × 1778` | `1080 × 1920` | Extra safe margins top/bottom (`120px`) for mobile UI overlays |
| **`blog`** | Blog Hero, OpenGraph (`og:image`), Newsletter Header | `16:9` | `1440 × 810` | `1600 × 900` | Compact 2-column horizontal bento + footer |

---

## How Responsive Reflow Prevents Cropping Defects

1. **Zero Hardcoded Y-Coordinates**: Templates use `.main-col { display: flex; flex-direction: column; justify-content: space-between; }` instead of brittle `top: 640px`.
2. **Automated DOM Overflow Check**: After Chrome loads the adapted layout, `render.py` injects an invisible DOM probe checking `mainCol.scrollHeight <= mainCol.clientHeight`. Any density overflow prints an explicit warning naming the overflowing slug and format so you never ship cut-off cards.
3. **One Content JSON -> All Sizes**: A single `.json` topic file can export simultaneously to `pinterest/`, `facebook/`, and `ig-square/` folders in one pass.
