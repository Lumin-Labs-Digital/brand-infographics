#!/usr/bin/env python3
"""
Cross-Platform Multi-Format Responsive Infographic Renderer (Editorial & Hybrid Modes).

Renders declarative JSON specs (or folders of JSON specs) paired with any brand.json
across Pinterest (2:3), Facebook/IG Portrait (4:5), Instagram Square (1:1), Stories (9:16),
and Blog Headers (16:9) via Headless Chrome/Chromium + Pillow PNG/JPEG export.

Usage:
  python3 render.py --input examples/sample_infographic.json --brand presets/brands/editorial-warm.json --formats pinterest facebook ig-square --out dist/
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BRAND = SKILL_DIR / "presets" / "brands" / "editorial-warm.json"

PLATFORM_FORMATS = {
    "pinterest":   {"css_w": 1000, "css_h": 1500, "out_w": 2000, "out_h": 3000, "scale": 2, "compact": False},
    "facebook":    {"css_w": 1200, "css_h": 1500, "out_w": 1440, "out_h": 1800, "scale": 2, "compact": False},
    "ig-portrait": {"css_w": 1200, "css_h": 1500, "out_w": 1080, "out_h": 1350, "scale": 2, "compact": False},
    "linkedin":    {"css_w": 1200, "css_h": 1500, "out_w": 1440, "out_h": 1800, "scale": 2, "compact": False},
    "ig-square":   {"css_w": 1080, "css_h": 1080, "out_w": 1080, "out_h": 1080, "scale": 2, "compact": True},
    "story":       {"css_w": 1000, "css_h": 1778, "out_w": 1080, "out_h": 1920, "scale": 2, "compact": False},
    "blog":        {"css_w": 1440, "css_h": 810,  "out_w": 1600, "out_h": 900,  "scale": 2, "compact": True},
}


def find_browser() -> str:
    env_bin = os.environ.get("CHROME_BIN", "").strip()
    if env_bin and Path(env_bin).exists():
        return env_bin
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("msedge"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    raise SystemExit("Chrome / Chromium / Edge binary not found. Install Chrome or set CHROME_BIN env var.")


def clean_serif_title(text: str) -> str:
    """Display serif fonts like Playfair often map Unicode right-arrow to '»'."""
    if "→" in text:
        return text.replace("→", " to ")
    return text


def font_css(brand: dict) -> str:
    fonts = brand.get("fonts", {})
    local_dir = fonts.get("local_dir", "").strip()
    if local_dir and Path(local_dir).is_dir():
        ld = Path(local_dir).resolve()
        rules = []
        mapping = [
            ("Playfair Display", 700, "PlayfairDisplay-Bold.ttf"),
            ("Playfair Display", 900, "PlayfairDisplay-Black.ttf"),
            ("Inter", 400, "Inter-Regular.ttf"),
            ("Inter", 500, "Inter-Medium.ttf"),
            ("Inter", 600, "Inter-SemiBold.ttf"),
            ("Inter", 700, "Inter-Bold.ttf"),
            ("Inter", 800, "Inter-ExtraBold.ttf"),
            ("Space Grotesk", 700, "SpaceGrotesk-Bold.ttf"),
        ]
        for fam, wt, fn in mapping:
            fp = ld / fn
            if fp.exists():
                rules.append(
                    f"@font-face {{ font-family: '{fam}'; font-weight: {wt}; font-style: normal; "
                    f"src: url('file://{fp}') format('truetype'); }}"
                )
        if rules:
            return "\n".join(rules)

    gf = fonts.get("google_fonts", "").strip()
    if gf:
        return f"@import url('https://fonts.googleapis.com/css2?{gf}&display=swap');"
    return ""


def accent(brand: dict, idx: int) -> str:
    acc = brand["colors"]["accents"]
    return acc[idx % len(acc)]


def render_media_uri(media_path: str, base_dir: Path) -> str:
    if not media_path:
        return ""
    p = Path(media_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    return f"file://{p}" if p.exists() else ""


def hex_to_rgba(hx: str, alpha: float) -> str:
    h = hx.strip().lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_chart_svg(chart: dict, brand: dict) -> str:
    x_labels = chart.get("x_labels", [])
    series = chart.get("series", [])
    y_min = float(chart.get("y_min", 0))
    y_max = float(chart.get("y_max", 100))
    if y_max <= y_min:
        y_max = y_min + 1.0

    w, h = 840, 210
    pad_l, pad_r, pad_t, pad_b = 54, 24, 20, 34
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    grid_lines = []
    for step in range(4):
        frac = step / 3.0
        y = pad_t + plot_h * (1.0 - frac)
        val = int(round(y_min + (y_max - y_min) * frac))
        grid_lines.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" stroke="#E2DFD5" stroke-width="1"/>')
        grid_lines.append(f'<text x="{pad_l - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#5B6775" font-family="Inter,sans-serif">{val}</text>')

    x_ticks = []
    n_pts = max((len(s.get("points", [])) for s in series), default=2)
    for i, lbl in enumerate(x_labels):
        x = pad_l + plot_w * (i / max(1, len(x_labels) - 1))
        x_ticks.append(f'<text x="{x:.1f}" y="{h - 10}" text-anchor="middle" font-size="11" font-weight="600" fill="#475569" font-family="Inter,sans-serif">{html.escape(str(lbl))}</text>')

    paths = []
    legend = []
    for idx, s in enumerate(series):
        pts = s.get("points", [])
        col = accent(brand, int(s.get("color_idx", idx)))
        coords = []
        for i, val in enumerate(pts):
            x = pad_l + plot_w * (i / max(1, len(pts) - 1))
            frac = max(0.0, min(1.0, (float(val) - y_min) / (y_max - y_min)))
            y = pad_t + plot_h * (1.0 - frac)
            coords.append((x, y))
        d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
        dash = ' stroke-dasharray="7 5"' if idx % 2 == 1 else ""
        paths.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linecap="round"{dash}/>')
        for x, y in coords:
            paths.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#FFFFFF" stroke="{col}" stroke-width="2.5"/>')
        legend.append(f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;color:#243447;"><i style="display:inline-block;width:14px;height:4px;background:{col};border-radius:2px;"></i>{html.escape(s.get("label", ""))}</span>')

    return f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <div style="font-size:13px;font-weight:700;letter-spacing:0.9px;text-transform:uppercase;color:{brand['colors']['ink_secondary']};">{html.escape(chart.get('title', 'Benchmark Comparison'))}</div>
      <div style="display:flex;gap:14px;">{''.join(legend)}</div>
    </div>
    <svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block;">
      {''.join(grid_lines)}{''.join(x_ticks)}{''.join(paths)}
    </svg>"""


def build_body_sections(spec: dict, brand: dict, media_uri: str, fmt_cfg: dict) -> str:
    arch = spec.get("archetype", "hero-compare")
    c = brand["colors"]
    compact = fmt_cfg["compact"]

    # Media banner / strip helper (clean fallback gradient when no photo supplied)
    def hero_strip_html() -> str:
        kicker = html.escape(spec.get("media_kicker", brand["brand_name"]))
        cap = clean_serif_title(spec.get("media_caption", spec.get("subtitle", "")))
        if media_uri:
            img_tag = f'<img src="{media_uri}" alt="">'
            ov_bg = f"linear-gradient(90deg, {hex_to_rgba(c['banner_bg'], 0.92)} 0%, {hex_to_rgba(c['banner_bg'], 0.50)} 68%, {hex_to_rgba(c['banner_bg'], 0.14)} 100%)"
        else:
            img_tag = ""
            ov_bg = f"linear-gradient(120deg, {c['banner_bg']} 0%, {accent(brand, 0)} 100%)"
        return f"""
        <div class="photo-strip">
          {img_tag}
          <div class="strip-ov" style="background:{ov_bg};">
            <div><span>{kicker}</span><strong>{cap}</strong></div>
          </div>
        </div>"""

    def cards_grid_html(cards: list[dict], cols: int = 3, top_bar: bool = True) -> str:
        items = []
        for i, item in enumerate(cards):
            col = accent(brand, int(item.get("tone", i)))
            border_css = f"border-top:6px solid {col};" if top_bar else f"border-left:7px solid {col};"
            tag_html = f'<div class="ctag" style="color:{col};">{html.escape(item["kicker"])}</div>' if item.get("kicker") else ""
            items.append(
                f'<div class="gcard ao-card" style="{border_css}">'
                f'{tag_html}<h3>{clean_serif_title(item["title"])}</h3><p>{item["desc"]}</p></div>'
            )
        return f'<div class="ggrid" style="grid-template-columns:repeat({cols},1fr);">{"".join(items)}</div>'

    if arch == "ranked-split":
        rows = []
        for i, r in enumerate(spec.get("rows", [])):
            col = accent(brand, int(r.get("tone", i)))
            rows.append(
                f'<div class="erow"><span class="badge" style="background:{hex_to_rgba(col, 0.12)};color:{col};">{html.escape(r["badge"])}</span>'
                f'<div><strong>{r["title"]}:</strong> {r["desc"]}</div></div>'
            )
        side = (
            f'<div class="side-photo"><img src="{media_uri}" alt="">'
            f'<div class="side-cap"><span>{html.escape(spec.get("media_kicker", ""))}</span>{html.escape(spec.get("media_caption", ""))}</div></div>'
            if media_uri else
            f'<div class="side-photo" style="background:linear-gradient(155deg,{c["banner_bg"]},{accent(brand,0)});display:flex;align-items:flex-end;">'
            f'<div class="side-cap" style="background:none;"><span>{html.escape(spec.get("media_kicker", brand["brand_name"]))}</span>{html.escape(spec.get("media_caption", ""))}</div></div>'
        )
        bento = f"""
        <div class="top-bento ao-card">
          <div>
            <div class="tb-h">{html.escape(spec.get("bento_heading", "Key Breakdown"))}</div>
            <div class="elist">{"".join(rows)}</div>
          </div>
          {side}
        </div>"""
        sec_h = f'<div class="sec-h">{clean_serif_title(spec.get("section_heading", ""))}</div>' if spec.get("section_heading") else ""
        cards = spec.get("cards", [])
        cols = 2 if len(cards) == 4 or compact else min(3, max(1, len(cards)))
        return bento + sec_h + (cards_grid_html(cards, cols=cols) if cards else "")

    if arch == "step-pipeline":
        steps = cards_grid_html(spec.get("steps", []), cols=min(3, max(1, len(spec.get("steps", [])))))
        cards = spec.get("cards", [])
        card_block = cards_grid_html(cards, cols=2 if len(cards) >= 4 else len(cards), top_bar=False) if cards else ""
        top_h = f'<div class="sec-h">{clean_serif_title(spec.get("top_heading", ""))}</div>' if spec.get("top_heading") else ""
        sec_h = f'<div class="sec-h">{clean_serif_title(spec.get("section_heading", ""))}</div>' if spec.get("section_heading") else ""
        return hero_strip_html() + top_h + steps + sec_h + card_block

    if arch == "checklist-grid":
        grid_items = cards_grid_html(spec.get("grid_items", []), cols=2, top_bar=False)
        cards = spec.get("cards", [])
        card_block = cards_grid_html(cards, cols=min(3, max(1, len(cards)))) if cards else ""
        top_h = f'<div class="sec-h">{clean_serif_title(spec.get("top_heading", ""))}</div>' if spec.get("top_heading") else ""
        sec_h = f'<div class="sec-h">{clean_serif_title(spec.get("section_heading", ""))}</div>' if spec.get("section_heading") else ""
        strip = hero_strip_html() if (spec.get("media_caption") or media_uri) else ""
        return strip + top_h + grid_items + sec_h + card_block

    if arch == "chart-insight":
        chart_box = f'<div class="chart-card ao-card">{build_chart_svg(spec.get("chart", {}), brand)}</div>'
        lp = spec.get("left_panel", {})
        rp = spec.get("right_panel", {})
        panels = []
        for p_idx, pan in enumerate((lp, rp)):
            if not pan:
                continue
            col = accent(brand, int(pan.get("tone", p_idx)))
            lis = "".join(f"<li>{it}</li>" for it in pan.get("items", []))
            panels.append(
                f'<div class="panel ao-card" style="border-top:6px solid {col};">'
                f'<div class="ptag" style="color:{col};">{html.escape(pan.get("kicker", ""))}</div>'
                f'<h2>{clean_serif_title(pan.get("title", ""))}</h2><ul>{lis}</ul></div>'
            )
        return chart_box + f'<div class="cols">{"".join(panels)}</div>'

    # Default: hero-compare
    lp = spec.get("left_panel", {})
    rp = spec.get("right_panel", {})
    panels = []
    for p_idx, pan in enumerate((lp, rp)):
        if not pan:
            continue
        col = accent(brand, int(pan.get("tone", p_idx)))
        lis = "".join(f"<li>{it}</li>" for it in pan.get("items", []))
        panels.append(
            f'<div class="panel ao-card" style="border-top:6px solid {col};">'
            f'<div class="ptag" style="color:{col};">{html.escape(pan.get("kicker", ""))}</div>'
            f'<h2>{clean_serif_title(pan.get("title", ""))}</h2><ul>{lis}</ul></div>'
        )
    sec_h = f'<div class="sec-h">{clean_serif_title(spec.get("section_heading", ""))}</div>' if spec.get("section_heading") else ""
    cards = spec.get("cards", [])
    card_block = cards_grid_html(cards, cols=min(3, max(1, len(cards)))) if cards else ""
    return hero_strip_html() + f'<div class="cols">{"".join(panels)}</div>' + sec_h + card_block


def build_html(spec: dict, brand: dict, fmt_name: str, base_dir: Path) -> str:
    fmt = PLATFORM_FORMATS[fmt_name]
    w, h = fmt["css_w"], fmt["css_h"]
    c = brand["colors"]
    fonts = brand.get("fonts", {})
    head_font = fonts.get("heading", "'Playfair Display', Georgia, serif")
    body_font = fonts.get("body", "'Inter', sans-serif")
    label_font = fonts.get("label", "'Space Grotesk', sans-serif")

    media_uri = render_media_uri(spec.get("media_path", ""), base_dir)
    logo_uri = render_media_uri(brand.get("logo_path", ""), base_dir)

    footer_h = 68 if fmt["compact"] else 84
    main_h = h - footer_h
    pad_v = 26 if fmt["compact"] else 44
    pad_h = 48 if fmt["compact"] else 68
    h1_size = 36 if fmt_name == "blog" else (40 if fmt["compact"] else 47)
    strip_h = 104 if fmt["compact"] else 140

    bottom_html = ""
    if spec.get("bottom_points") or spec.get("bottom_title"):
        pts = "".join(f"<div>• {p}</div>" for p in spec.get("bottom_points", []))
        bottom_html = f"""
        <div class="bottom-banner ao-dark" style="background:{c['banner_bg']};">
          <div class="bb-t" style="color:{c['banner_kicker']};">{html.escape(spec.get('bottom_title', 'Key Takeaways'))}</div>
          <div class="bb-b" style="color:{c['banner_ink']};">{pts}</div>
        </div>"""

    logo_img = f'<img src="{logo_uri}" alt="Brand Logo">' if logo_uri else ""
    body_sections = build_body_sections(spec, brand, media_uri, fmt)

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><style>
{font_css(brand)}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: {w}px; height: {h}px; overflow: hidden;
  font-family: {body_font}; -webkit-font-smoothing: antialiased;
}}
.frame {{ width: {w}px; height: {h}px; position: relative; overflow: hidden; background: {c['ground']}; }}
.global-light {{
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: radial-gradient(circle at 22% 8%, rgba(255,255,255,0.68) 0%, rgba(255,255,255,0) 56%);
}}
.paper-grain {{
  position: absolute; inset: 0; pointer-events: none; z-index: 2; opacity: 0.032;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}}
.main-col {{
  position: relative; z-index: 4; width: {w}px; height: {main_h}px;
  padding: {pad_v}px {pad_h}px {max(22, pad_v - 10)}px;
  display: flex; flex-direction: column; justify-content: space-between; gap: {12 if fmt['compact'] else 16}px;
}}
.hero {{ text-align: center; }}
.hero h1 {{
  font-family: {head_font}; font-weight: 900; font-size: {h1_size}px;
  line-height: 1.10; letter-spacing: -0.9px; color: {c['ink_primary']};
}}
.hero p {{
  margin: 8px auto 0; font-size: {16.5 if fmt['compact'] else 18.5}px;
  font-weight: 500; line-height: 1.35; color: {c['ink_secondary']};
}}
.ao-card {{
  box-shadow: 0 1px 2px rgba(20,32,48,0.04), 0 8px 24px rgba(20,32,48,0.06), 0 18px 38px rgba(20,32,48,0.05);
}}
.ao-dark {{ box-shadow: 0 4px 12px rgba(10,18,28,0.14), 0 18px 36px rgba(10,18,28,0.16); }}
.photo-strip {{
  position: relative; height: {strip_h}px; border-radius: 18px; overflow: hidden;
  box-shadow: 0 8px 22px rgba(20,32,48,0.11);
}}
.photo-strip img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.strip-ov {{ position: absolute; inset: 0; padding: 0 26px; display: flex; align-items: center; color: #FFF; }}
.strip-ov span {{ display: block; font-size: 11px; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; color: {c['banner_kicker']}; margin-bottom: 4px; }}
.strip-ov strong {{ font-family: {head_font}; font-size: {20 if fmt['compact'] else 24}px; font-weight: 900; line-height: 1.16; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
.panel {{ background: {c['card']}; border: 1px solid rgba(20,32,48,0.08); border-radius: 18px; padding: {16 if fmt['compact'] else 21}px 22px; }}
.ptag {{ font-size: 11.5px; font-weight: 800; letter-spacing: 0.9px; text-transform: uppercase; }}
.panel h2 {{ font-family: {head_font}; font-weight: 900; font-size: {19.5 if fmt['compact'] else 22.5}px; color: {c['ink_primary']}; margin: 4px 0 10px; }}
.panel ul {{ list-style: none; display: flex; flex-direction: column; gap: {7 if fmt['compact'] else 9.5}px; font-size: {13.5 if fmt['compact'] else 14.5}px; color: {c['ink_secondary']}; line-height: 1.38; }}
.sec-h {{ text-align: center; font-family: {head_font}; font-weight: 900; font-size: {21 if fmt['compact'] else 25}px; color: {c['ink_primary']}; }}
.ggrid {{ display: grid; gap: 14px; }}
.gcard {{ background: {c['card']}; border: 1px solid rgba(20,32,48,0.08); border-radius: 18px; padding: {15 if fmt['compact'] else 20}px 18px; }}
.ctag {{ font-size: 11px; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 4px; }}
.gcard h3 {{ font-family: {head_font}; font-weight: 900; font-size: {17.5 if fmt['compact'] else 20}px; color: {c['ink_primary']}; margin-bottom: 6px; }}
.gcard p {{ font-size: {13.5 if fmt['compact'] else 14.5}px; color: {c['ink_secondary']}; line-height: 1.40; }}
.top-bento {{
  background: {c['card']}; border: 1px solid rgba(20,32,48,0.08); border-radius: 20px; padding: 18px 20px;
  display: grid; grid-template-columns: 1fr 220px; gap: 18px; align-items: stretch;
}}
.tb-h {{ font-family: {label_font}; font-size: 12.5px; font-weight: 700; letter-spacing: 1px; color: {c['ink_secondary']}; text-transform: uppercase; margin-bottom: 10px; }}
.elist {{ display: flex; flex-direction: column; gap: 9px; }}
.erow {{ display: grid; grid-template-columns: 96px 1fr; gap: 11px; align-items: center; background: #FFFFFF; border: 1px solid rgba(20,32,48,0.07); border-radius: 11px; padding: 10px 13px; font-size: 14px; color: {c['ink_primary']}; line-height: 1.36; }}
.badge {{ display: inline-block; text-align: center; padding: 5px 7px; border-radius: 8px; font-size: 10.5px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; }}
.side-photo {{ position: relative; border-radius: 14px; overflow: hidden; min-height: 220px; }}
.side-photo img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.side-cap {{ position: absolute; left: 0; right: 0; bottom: 0; padding: 30px 14px 12px; background: linear-gradient(180deg, rgba(16,28,36,0) 0%, rgba(16,28,36,0.92) 66%); color: #FFF; font-size: 13px; font-weight: 700; line-height: 1.28; }}
.side-cap span {{ display: block; font-size: 10.5px; font-weight: 700; letter-spacing: 0.9px; text-transform: uppercase; color: {c['banner_kicker']}; margin-bottom: 3px; }}
.chart-card {{ background: {c['card']}; border: 1px solid rgba(20,32,48,0.08); border-radius: 18px; padding: 18px 22px; }}
.bottom-banner {{ border-radius: 20px; padding: {16 if fmt['compact'] else 22}px 28px; display: flex; flex-direction: column; justify-content: center; }}
.bb-t {{ font-family: {label_font}; font-size: 13.5px; font-weight: 700; letter-spacing: 1.1px; text-transform: uppercase; margin-bottom: 8px; }}
.bb-b {{ display: flex; flex-direction: column; gap: {6 if fmt['compact'] else 8}px; font-size: {14 if fmt['compact'] else 15.5}px; line-height: 1.42; }}
.bb-b strong {{ color: #FFFFFF; }}
.footer {{
  position: absolute; left: 0; right: 0; bottom: 0; height: {footer_h}px; z-index: 6;
  background: {c['footer_bg']}; border-top: 1px solid rgba(20,32,48,0.08);
  display: flex; align-items: center; justify-content: center;
}}
.footer-domain {{ font-family: {label_font}; font-weight: 700; font-size: 14.5px; letter-spacing: 3px; color: {c['footer_ink']}; }}
.footer img {{ position: absolute; right: 30px; width: 56px; height: 56px; object-fit: contain; }}
</style></head><body><div class="frame">
  <div class="global-light"></div><div class="paper-grain"></div>
  <div class="main-col">
    <div class="hero">
      <h1>{clean_serif_title(spec['title'])}</h1>
      <p>{spec.get('subtitle', '')}</p>
    </div>
    {body_sections}
    {bottom_html}
  </div>
  <footer class="footer">
    <span class="footer-domain">{html.escape(brand['footer_label'])}</span>
    {logo_img}
  </footer>
</div></body></html>"""


def render_spec(spec_path: Path, brand: dict, formats: list[str], out_root: Path, browser: str) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    slug = spec.get("slug") or spec_path.stem
    base_dir = spec_path.parent

    with tempfile.TemporaryDirectory(prefix="brand_infog_") as tmpdir:
        for fmt_name in formats:
            fmt = PLATFORM_FORMATS[fmt_name]
            fmt_dir = out_root / fmt_name
            html_dir = fmt_dir / "html"
            png_dir = fmt_dir / "png"
            jpg_dir = fmt_dir / "jpg"
            for d in (html_dir, png_dir, jpg_dir):
                d.mkdir(parents=True, exist_ok=True)

            html_str = build_html(spec, brand, fmt_name, base_dir)
            html_file = html_dir / f"{slug}.html"
            html_file.write_text(html_str, encoding="utf-8")

            raw_png = Path(tmpdir) / f"{slug}_{fmt_name}_raw.png"
            subprocess.run([
                browser,
                "--headless=new",
                "--no-sandbox",
                f"--user-data-dir={tmpdir}/profile_{fmt_name}",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--screenshot={raw_png}",
                f"--window-size={fmt['css_w']},{fmt['css_h']}",
                f"--force-device-scale-factor={fmt['scale']}",
                f"file://{html_file.resolve()}",
            ], check=True, capture_output=True)

            im = Image.open(raw_png).convert("RGB")
            target_sz = (fmt["out_w"], fmt["out_h"])
            if im.size != target_sz:
                im = im.resize(target_sz, Image.Resampling.LANCZOS)
            png_out = png_dir / f"{slug}.png"
            jpg_out = jpg_dir / f"{slug}.jpg"
            im.save(png_out, format="PNG")
            im.save(jpg_out, format="JPEG", quality=95, subsampling=0)
            print(f"[{fmt_name}] Rendered {jpg_out} ({im.size[0]}x{im.size[1]})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render brand infographics across multiple social aspect ratios.")
    parser.add_argument("--input", required=True, help="JSON infographic spec file OR directory of .json specs")
    parser.add_argument("--brand", default=str(DEFAULT_BRAND), help="Path to brand.json")
    parser.add_argument("--formats", nargs="+", default=["pinterest", "facebook"], choices=list(PLATFORM_FORMATS.keys()), help="Target platforms/aspect ratios")
    parser.add_argument("--out", default="dist", help="Output root directory")
    args = parser.parse_args()

    brand = json.loads(Path(args.brand).read_text(encoding="utf-8"))
    in_path = Path(args.input)
    specs = sorted(in_path.glob("*.json")) if in_path.is_dir() else [in_path]
    if not specs:
        raise SystemExit(f"No .json specs found at {in_path}")

    browser = find_browser()
    out_root = Path(args.out)
    for sp in specs:
        render_spec(sp, brand, args.formats, out_root, browser)


if __name__ == "__main__":
    main()
