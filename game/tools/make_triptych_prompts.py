#!/usr/bin/env python3
"""Turn the 60 single-scene prompts in book2_prompts.json into 20 triptych prompts
(one per page) ready to paste into a seeded Gemini 'Create images' chat.

Each triptych = LEFT: correct  |  MIDDLE: trap A  |  RIGHT: trap B  (fixed order,
so slice_triptychs.py knows which third is which).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = json.loads((HERE / "book2_prompts.json").read_text(encoding="utf-8"))

by_page = {}
for im in spec["images"]:
    by_page.setdefault(im["page"], {})[im["role"]] = im["scene"]

INTRO = ("Create ONE very wide landscape image (aspect ratio about 4:1) divided into "
         "THREE equal panels side by side, exact equal thirds, separated by a thin clean "
         "white vertical line between them. Use the SAME characters and the SAME exact "
         "hand-drawn comic style (bold black outlines, flat colors) in all three panels. "
         "Absolutely NO text, letters, numbers or words anywhere. All three panels the "
         "exact same size.")

out = []
for p in range(1, 21):
    r = by_page[p]
    out.append(f"===== PAGE {p:02d} =====\n"
               f"{INTRO}\n"
               f"LEFT panel: {r['correct']}\n"
               f"MIDDLE panel: {r['trapA']}\n"
               f"RIGHT panel: {r['trapB']}\n")

txt = "\n".join(out)
dest = HERE / "book2_triptych_prompts.txt"
dest.write_text(txt, encoding="utf-8")
print(f"wrote {dest}  ({len(out)} prompts)")
