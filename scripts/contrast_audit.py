#!/usr/bin/env python3
"""
Standalone WCAG 2.1 + APCA (Lc) Contrast Auditor for brand.json profiles.
Zero external dependencies — pure Python sRGB / APCA W3 math.

Usage:
  python3 contrast_audit.py --brand presets/brands/editorial-warm.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def hex_to_rgb(hx: str) -> tuple[int, int, int]:
    hx = hx.strip().lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    return int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)


def rel_lum(rgb: tuple[int, int, int]) -> float:
    def lin(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def wcag_ratio(fg: str, bg: str) -> float:
    l1 = rel_lum(hex_to_rgb(fg))
    l2 = rel_lum(hex_to_rgb(bg))
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def apca_lc(fg: str, bg: str) -> float:
    """Simplified SAPC / APCA 0.0.98G-4g contrast lightness difference (Lc)."""
    def y_apca(rgb: tuple[int, int, int]) -> float:
        r, g, b = (c / 255.0 for c in rgb)
        y = 0.2126729 * (r ** 2.4) + 0.7151522 * (g ** 2.4) + 0.0721750 * (b ** 2.4)
        return y if y >= 0.022 else y + ((0.022 - y) ** 1.414)

    y_txt = y_apca(hex_to_rgb(fg))
    y_bg = y_apca(hex_to_rgb(bg))
    if abs(y_bg - y_txt) < 0.0005:
        return 0.0

    if y_bg > y_txt:  # dark text on light bg
        sapc = ((y_bg ** 0.56) - (y_txt ** 0.57)) * 1.14
        return 0.0 if sapc < 0.1 else (sapc - 0.027) * 100.0
    else:             # light text on dark bg
        sapc = ((y_bg ** 0.65) - (y_txt ** 0.62)) * 1.14
        return 0.0 if sapc > -0.1 else (sapc + 0.027) * 100.0


def audit_brand(data: dict) -> int:
    c = data["colors"]
    checks = [
        ("Headline on Ground", c["ink_primary"], c["ground"], 60.0),
        ("Subhead on Ground", c["ink_secondary"], c["ground"], 75.0),
        ("Headline on Card", c["ink_primary"], c["card"], 75.0),
        ("Body on Card", c["ink_secondary"], c["card"], 75.0),
        ("Footer Text on Footer Bg", c["footer_ink"], c["footer_bg"], 60.0),
        ("Banner Kicker on Dark Banner", c["banner_kicker"], c["banner_bg"], 60.0),
        ("Banner Body on Dark Banner", c["banner_ink"], c["banner_bg"], 75.0),
    ]
    for i, acc in enumerate(c.get("accents", [])):
        checks.append((f"Accent #{i+1} Label on Card", acc, c["card"], 60.0))
        checks.append((f"White Text on Accent #{i+1} Pill", "#FFFFFF", acc, 60.0))

    failures = 0
    print(f"Auditing Brand: {data.get('brand_name', 'Unknown')}")
    print(f"{'Pair':<34} {'FG':<9} {'BG':<9} {'WCAG':>7} {'APCA Lc':>9}  {'Status'}")
    print("-" * 82)
    for name, fg, bg, min_lc in checks:
        ratio = wcag_ratio(fg, bg)
        lc = apca_lc(fg, bg)
        ok = abs(lc) >= min_lc and ratio >= 4.5
        if not ok:
            failures += 1
        tag = "PASS" if ok else f"FAIL (<|{min_lc:.0f}| / 4.5:1)"
        print(f"{name:<34} {fg:<9} {bg:<9} {ratio:>6.2f}:1 {lc:>8.1f}  {tag}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit brand.json color contrast via WCAG 2.1 & APCA Lc.")
    parser.add_argument("--brand", required=True, help="Path to brand.json")
    args = parser.parse_args()

    data = json.loads(Path(args.brand).read_text(encoding="utf-8"))
    failures = audit_brand(data)
    if failures:
        print(f"\nFound {failures} contrast warning(s) above.")
        sys.exit(1)
    print("\nAll brand pairs passed WCAG 2.1 and APCA contrast thresholds.")


if __name__ == "__main__":
    main()
