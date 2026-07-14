#!/usr/bin/env python3
"""Generate Cat Man story images via the Google Gemini API ("nano banana").

Reads GEMINI_API_KEY from the project-root .env (or the environment), reads a
prompts JSON (default: book2_prompts.json), and generates one image per entry
using a shared style header + optional character reference images. For each entry
it saves the raw PNG and a game-ready 1000x750 JPEG into the book's scenes folder.

Setup:
    pip install -r requirements.txt
    # put your key in the project-root .env   (GEMINI_API_KEY=...)

Usage:
    python generate_images.py                     # generate the whole book
    python generate_images.py --pages 1-5         # only pages 1..5
    python generate_images.py --pages 3,7,12      # specific pages
    python generate_images.py --overwrite         # regenerate existing images
    python generate_images.py --no-refs           # ignore character references
    python generate_images.py --prompts book3_prompts.json
"""
import os, sys, io, re, json, time, argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent            # ...\MyApp\Cat
MODEL = "gemini-2.5-flash-image"             # nano banana. If Google renames it, change here.


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "GEMINI_API_KEY":
                return v.strip().strip('"').strip("'")
    return ""


def parse_pages(spec, all_pages):
    if not spec:
        return set(all_pages)
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default=str(HERE / "book2_prompts.json"))
    ap.add_argument("--pages", default="")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--no-refs", action="store_true")
    ap.add_argument("--delay", type=float, default=6.0, help="seconds between calls")
    args = ap.parse_args()

    key = load_api_key()
    if not key:
        print("No GEMINI_API_KEY found.")
        print("  -> put your key in", PROJECT_ROOT / ".env", "as  GEMINI_API_KEY=...")
        print("  -> get a free key at https://aistudio.google.com/apikey")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        print("Missing dependencies. Run:  pip install -r requirements.txt")
        sys.exit(1)
    from PIL import Image

    spec = json.loads(Path(args.prompts).read_text(encoding="utf-8"))
    style = spec["style_header"]
    prefix = spec.get("prefix", "img")
    out_dir = PROJECT_ROOT / spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    refs_dir = PROJECT_ROOT / spec.get("refs_dir", "game/assets")

    style_ref_img = None
    srp = spec.get("style_ref")
    if srp and (PROJECT_ROOT / srp).exists():
        style_ref_img = Image.open(PROJECT_ROOT / srp)

    client = genai.Client(api_key=key)
    want = parse_pages(args.pages, [im["page"] for im in spec["images"]])

    total = ok = skipped = failed = 0
    for im in spec["images"]:
        if im["page"] not in want:
            continue
        total += 1
        name = f"{prefix}_p{im['page']:02d}_{im['role']}"
        jpg = out_dir / f"{name}.jpg"
        if jpg.exists() and not args.overwrite:
            skipped += 1
            print(f"  skip  {name} (already exists)")
            continue

        contents = [style + im["scene"]]
        if not args.no_refs:
            if style_ref_img is not None:
                contents.append(style_ref_img)
            for r in im.get("refs", []):
                p = refs_dir / f"{r}.png"
                if p.exists():
                    contents.append(Image.open(p))

        data = None
        for attempt in range(6):
            try:
                resp = client.models.generate_content(model=MODEL, contents=contents)
                for part in resp.candidates[0].content.parts:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        data = inline.data
                        break
                if data:
                    break
                print(f"  ...no image for {name}, retry {attempt + 1}")
                time.sleep(5)
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    m = re.search(r"retryDelay['\":\s]+([0-9.]+)s", msg)
                    wait = int(float(m.group(1))) + 2 if m else 30
                    wait = min(max(wait, 15), 65)
                    print(f"  ...rate-limited on {name}, waiting {wait}s (try {attempt + 1})")
                    time.sleep(wait)
                else:
                    print(f"  ...error on {name} (try {attempt + 1}): {msg[:120]}")
                    time.sleep(4)

        if not data:
            failed += 1
            print(f"  FAIL  {name}")
            continue

        (raw_dir / f"{name}.png").write_bytes(data)
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            TW, TH = 1000, 750
            target = TW / TH
            w, h = img.size
            if w / h > target:
                nw = int(h * target); x = (w - nw) // 2; img = img.crop((x, 0, x + nw, h))
            else:
                nh = int(w / target); y = (h - nh) // 2; img = img.crop((0, y, w, y + nh))
            img.resize((TW, TH), Image.LANCZOS).save(jpg, quality=88)
        except Exception as e:
            print(f"  (saved raw, post-process failed for {name}: {e})")
        ok += 1
        print(f"  OK    {name}")
        time.sleep(args.delay)

    print(f"\nDone: {ok} generated, {skipped} skipped, {failed} failed (of {total} requested).")
    print("Output folder:", out_dir)


if __name__ == "__main__":
    main()
