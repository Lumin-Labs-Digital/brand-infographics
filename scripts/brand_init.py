#!/usr/bin/env python3
"""
Initialize a declarative brand.json config for any website, brand, or social handle.

Usage:
  python3 brand_init.py --name "Acme Fitness" --footer "ACMEFIT.COM" --preset creator-bold -o brand.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PRESETS_DIR = SKILL_DIR / "presets" / "brands"


def main() -> None:
    presets = sorted(p.stem for p in PRESETS_DIR.glob("*.json"))
    parser = argparse.ArgumentParser(description="Create a brand.json configuration from a preset.")
    parser.add_argument("--name", required=True, help="Brand or publication name")
    parser.add_argument("--footer", required=True, help="Footer domain or social handle (e.g. YOURSITE.COM or @handle)")
    parser.add_argument("--preset", default="editorial-warm", choices=presets, help="Base visual preset")
    parser.add_argument("--niche", help="Topic domain (e.g. 'B2B SaaS', 'personal finance', 'fitness')")
    parser.add_argument("--tone", help="Editorial voice description")
    parser.add_argument("--accent", help="Override primary accent hex (e.g. #1B5E52)")
    parser.add_argument("--ground", help="Override 60%% background ground hex (e.g. #F6F3EC)")
    parser.add_argument("--banner", help="Override dark takeaway banner hex (e.g. #182B26)")
    parser.add_argument("--logo", default="", help="Optional path to transparent logo PNG/SVG")
    parser.add_argument("--font-dir", default="", help="Optional local folder with TTF/WOFF2 font files")
    parser.add_argument("-o", "--output", default="brand.json", help="Output brand.json path")
    args = parser.parse_args()

    preset_data = json.loads((PRESETS_DIR / f"{args.preset}.json").read_text(encoding="utf-8"))
    preset_data["brand_name"] = args.name
    preset_data["footer_label"] = args.footer.upper() if "." in args.footer and not args.footer.startswith("@") else args.footer
    preset_data["logo_path"] = args.logo

    if args.niche:
        preset_data["niche"] = args.niche
    if args.tone:
        preset_data["tone"] = args.tone
    if args.font_dir:
        preset_data["fonts"]["local_dir"] = args.font_dir
    if args.ground:
        preset_data["colors"]["ground"] = args.ground
    if args.banner:
        preset_data["colors"]["banner_bg"] = args.banner
    if args.accent:
        preset_data["colors"]["accent_primary"] = args.accent
        acc = [c for c in preset_data["colors"]["accents"] if c.lower() != args.accent.lower()]
        preset_data["colors"]["accents"] = [args.accent] + acc[:4]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(preset_data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote brand profile -> {out}")


if __name__ == "__main__":
    main()
