#!/usr/bin/env python3
"""
Build labeled visual QA contact sheets from any directory of PNG or JPEG infographics.

Usage:
  python3 make_contact_sheet.py --input dist/facebook/jpg --out dist/qa_facebook.jpg
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser(description="Create labeled QA thumbnail contact sheets.")
    parser.add_argument("--input", required=True, help="Directory of .jpg or .png images")
    parser.add_argument("--out", required=True, help="Output JPEG path (multi-sheet appends _01, _02)")
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--per-sheet", type=int, default=25)
    args = parser.parse_args()

    in_dir = Path(args.input)
    imgs = sorted(list(in_dir.glob("*.jpg")) + list(in_dir.glob("*.png")))
    if not imgs:
        raise SystemExit(f"No JPG/PNG files found in {in_dir}")

    out_base = Path(args.out)
    out_base.parent.mkdir(parents=True, exist_ok=True)

    thumb_w = 280
    pad = 12
    label_h = 24
    # Match thumb height dynamically to first image's aspect ratio
    sample_im = Image.open(imgs[0])
    thumb_h = max(140, int(round(thumb_w * (sample_im.height / sample_im.width))))

    num_sheets = (len(imgs) + args.per_sheet - 1) // args.per_sheet
    for idx in range(num_sheets):
        chunk = imgs[idx * args.per_sheet:(idx + 1) * args.per_sheet]
        rows = (len(chunk) + args.cols - 1) // args.cols
        cw = args.cols * (thumb_w + pad) + pad
        ch = rows * (thumb_h + label_h + pad) + pad
        sheet = Image.new("RGB", (cw, ch), (240, 240, 240))
        draw = ImageDraw.Draw(sheet)

        for j, p in enumerate(chunk):
            r, c = divmod(j, args.cols)
            x = pad + c * (thumb_w + pad)
            y = pad + r * (thumb_h + label_h + pad)
            im = Image.open(p).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))
            draw.rectangle([(x, y + thumb_h), (x + thumb_w, y + thumb_h + label_h)], fill=(255, 255, 255))
            draw.text((x + 6, y + thumb_h + 5), p.stem[:34], fill=(20, 20, 20))

        dest = out_base if num_sheets == 1 else out_base.with_name(f"{out_base.stem}_{idx+1:02d}{out_base.suffix}")
        sheet.save(dest, quality=92)
        print(f"Saved contact sheet: {dest} ({len(chunk)} items)")


if __name__ == "__main__":
    main()
