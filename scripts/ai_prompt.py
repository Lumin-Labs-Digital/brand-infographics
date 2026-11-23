#!/usr/bin/env python3
"""
Dual-Mode AI Prompt Engine (--engine ai | hybrid) tailored to any brand.json & platform format.

- --engine ai     : Full AI-generated infographic prompt grounded in brand.json colors, tone & aspect ratio.
- --engine hybrid : Zero-text conceptual artwork / spot-illustration prompt locked to card/ground hex
                    so scripts/render.py handles 100% of typography, badges, and brand footers cleanly.

Supports:
  --build-prompt   Prints the engineered prompt (default; ideal for Antigravity image-generator subagent).
  --execute -o     Calls Google Gemini Image API directly when GEMINI_API_KEY is set.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BRAND = SKILL_DIR / "presets" / "brands" / "editorial-warm.json"

TYPE_LAYOUTS = {
    "statistical": "Clear metric callouts, crisp bar/line chart zones, and bold numerical hierarchy.",
    "timeline": "Chronological spine with distinct date nodes and clean directional flow.",
    "process": "Numbered step-by-step sequence with intuitive directional rhythm.",
    "comparison": "Balanced two-column side-by-side layout contrasting benefits vs. tradeoffs.",
    "list": "Structured numbered card grid with balanced whitespace and scannable subheads.",
    "hierarchical": "Tiered pyramid or layered breakdown prioritizing foundational items.",
    "anatomical": "Central conceptual subject cutaway paired with clean outer callout zones.",
    "social": "High-impact mobile headline with clean minimalist visual anchors.",
}

FORMAT_RATIOS = {
    "pinterest": "2:3 tall vertical poster",
    "facebook": "4:5 vertical social feed card",
    "ig-portrait": "4:5 vertical social feed card",
    "ig-square": "1:1 balanced square frame",
    "linkedin": "4:5 executive carousel card",
    "story": "9:16 full-screen vertical story",
    "blog": "16:9 widescreen editorial header",
}

COLORBLIND_NOTES = {
    "none": "",
    "wong": "Ensure categorical distinctions align with Wong colorblind-safe contrast (orange #E69F00, sky #56B4E9, bluish-green #009E73, deep blue #0072B2).",
    "ibm": "Ensure categorical distinctions stay colorblind-safe using high-luminance separation (ultramarine, gold, magenta/slate).",
    "tol": "Maintain clear lightness separation between categorical accents for deuteranopia/protanopia accessibility.",
}


def build_ai_prompt(
    topic: str,
    brand: dict,
    engine: str,
    inf_type: str,
    fmt: str,
    palette: str,
    critique: str,
    facts_file: str | None,
) -> str:
    c = brand["colors"]
    ratio_desc = FORMAT_RATIOS[fmt]
    facts_block = ""
    if facts_file:
        facts_text = Path(facts_file).read_text(encoding="utf-8").strip()
        facts_block = f"\nVERIFIED FACTS & STATS TO INCLUDE ACCURATELY:\n{facts_text}\n"

    cb_note = COLORBLIND_NOTES.get(palette, "")
    crit_block = f"\nREFINEMENT FIXES FROM PRIOR REVIEW:\n{critique}\n" if critique else ""

    if engine == "hybrid":
        return f"""Create a high-craft bespoke editorial illustration / visual artwork for the topic:
"{topic}"

CRITICAL HYBRID COMPOSITING CONSTRAINTS:
- ZERO TEXT: Include NO words, NO letters, NO numbers, NO watermarks, NO labels, and NO fake charts anywhere in the image.
- Canvas & Aspect Ratio: Clean {ratio_desc} editorial illustration bay.
- Seamless Palette Match: Match the surrounding background seamlessly to flat solid hex {c['card']} (or quiet paper parchment {c['ground']}), using calm focal tones inspired by {c['accent_primary']} and {c['ink_primary']}.
- Style & Lighting: Editorial studio craftsmanship, soft top-left daylight illumination, delicate natural shading, uncluttered framing centered cleanly so surrounding HTML/CSS typography and cards pair seamlessly.
{crit_block}""".strip()

    # engine == "ai" (full standalone infographic)
    return f"""Design a publication-grade editorial infographic for {brand['brand_name']} ({brand['footer_label']}):
Topic: "{topic}"

FORMAT & COMPOSITION:
- Aspect Ratio: {ratio_desc}. Keep outer margins generous and legible on mobile screens.
- Infographic Archetype ({inf_type}): {TYPE_LAYOUTS[inf_type]}
- Editorial Tone: {brand.get('tone', 'clear, trustworthy editorial clarity')}.

BRAND COLOR & TYPOGRAPHY SYSTEM:
- Quiet 60% Ground: {c['ground']} with elevated {c['card']} surface cards and subtle thin borders.
- Crisp Ink Hierarchy: Deep charcoal-ink headlines ({c['ink_primary']}) and clear body copy ({c['ink_secondary']}).
- Curated 10% Accents: {', '.join(c['accents'][:4])}. {cb_note}
- Display Serif headlines paired with clean geometric sans-serif body labels — strictly crisp, legible English spelling throughout with zero garbled text.
- Brand Anchor: Include a clean uncluttered bottom footer featuring "{brand['footer_label']}" once (no redundant top badges).
{facts_block}{crit_block}""".strip()


def execute_gemini_image(prompt: str, out_path: Path, model: str) -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("GEMINI_API_KEY env var is required for --execute (or use --build-prompt with a native image subagent).")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini API error ({e.code}): {e.read().decode('utf-8', errors='ignore')[:400]}")

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(base64.b64decode(inline["data"]))
                print(f"Saved AI image -> {out_path}")
                return
    raise SystemExit("Gemini response did not include inline image bytes.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or execute AI / Hybrid infographic prompts aligned to brand.json.")
    parser.add_argument("topic", help="Infographic topic or visual metaphor subject")
    parser.add_argument("--brand", default=str(DEFAULT_BRAND), help="Path to brand.json")
    parser.add_argument("--engine", default="ai", choices=["ai", "hybrid"], help="Full AI infographic ('ai') vs zero-text spot illustration ('hybrid')")
    parser.add_argument("--type", default="comparison", choices=list(TYPE_LAYOUTS.keys()), help="Layout archetype hint for 'ai' engine")
    parser.add_argument("--format", default="pinterest", choices=list(FORMAT_RATIOS.keys()), help="Target social platform aspect ratio")
    parser.add_argument("--palette", default="none", choices=list(COLORBLIND_NOTES.keys()), help="Colorblind safety enforcement hint")
    parser.add_argument("--facts", help="Optional text/markdown file of verified facts/numbers to ground prompt")
    parser.add_argument("--critique", default="", help="Specific refinement fixes from previous multimodal review")
    parser.add_argument("--build-prompt", action="store_true", help="Print the engineered prompt to stdout")
    parser.add_argument("--execute", action="store_true", help="Call Gemini Image API using GEMINI_API_KEY")
    parser.add_argument("--model", default="gemini-2.5-flash-image", help="Gemini image model for --execute")
    parser.add_argument("-o", "--output", default="ai_output.png", help="Output image path when using --execute")
    args = parser.parse_args()

    brand = json.loads(Path(args.brand).read_text(encoding="utf-8"))
    prompt = build_ai_prompt(
        topic=args.topic,
        brand=brand,
        engine=args.engine,
        inf_type=args.type,
        fmt=args.format,
        palette=args.palette,
        critique=args.critique,
        facts_file=args.facts,
    )

    if args.execute:
        execute_gemini_image(prompt, Path(args.output), args.model)
    else:
        print(prompt)


if __name__ == "__main__":
    main()
