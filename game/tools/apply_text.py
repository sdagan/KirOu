# -*- coding: utf-8 -*-
"""
apply_text.py — take the freely-editable Hebrew text files and inject the
sentences back into the game HTML (book1.html / book2.html).

Edit the text in  game/text/book1.txt  and  game/text/book2.txt , then run:
    py apply_text.py          (or:  python apply_text.py)

It only touches the per-page sentence arrays (the `lines:[...]`). Images,
answer keys and engine code are left untouched.
"""
import re, sys, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)  # game/

BOOKS = [
    ("book1", os.path.join(GAME, "text", "book1.txt"), os.path.join(GAME, "book1.html")),
    ("book2", os.path.join(GAME, "text", "book2.txt"), os.path.join(GAME, "book2.html")),
]


def parse_text(path):
    """Return {page_number: [sentence, ...]} from an editable .txt file."""
    pages, cur = {}, None
    with io.open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            s = line.strip()
            if not s:
                continue
            m = re.match(r"^##\s*(?:עמוד|page)\s*(\d+)", s)
            if m:
                cur = int(m.group(1))
                pages[cur] = []
                continue
            if s.startswith("#"):
                continue
            if cur is not None:
                pages[cur].append(s)
    return pages


def js_array(sentences):
    """Build a JS single-quoted string array literal from sentences."""
    parts = []
    for t in sentences:
        parts.append("'" + t.replace("\\", "\\\\").replace("'", "\\'") + "'")
    return "[" + ",".join(parts) + "]"


def apply_book(name, txt_path, html_path):
    pages = parse_text(txt_path)
    with io.open(html_path, encoding="utf-8") as f:
        html = f.read()
    changed = 0

    for n, sentences in pages.items():
        arr = js_array(sentences)
        done = False

        # form A:  pg(N,[...])  or  p1(N,[...])
        patA = re.compile(r"((?:pg|p1)\(" + str(n) + r",)\[[^\]]*\]")
        html2, c = patA.subn(lambda m: m.group(1) + arr, html)
        if c:
            html = html2; changed += c; done = True

        # form B (explicit early pages):  עַמּוּד N",lines:[...]
        if not done:
            cap = "עַמּוּד " + str(n)
            patB = re.compile(r"(" + re.escape(cap) + r'",\s*lines:\s*)\[[^\]]*\]')
            html2, c = patB.subn(lambda m: m.group(1) + arr, html)
            if c:
                html = html2; changed += c; done = True

        if not done:
            print("  ! page %d: no match in %s (left unchanged)" % (n, os.path.basename(html_path)))

    # English: fill the  var LINES_EN=[...]  block (per-page arrays, ordered by page)
    en_path = txt_path[:-4] + ".en.txt"
    if os.path.exists(en_path) and "var LINES_EN=" in html:
        en = parse_text(en_path)
        maxp = max(en.keys()) if en else 0
        rows = [js_array(en.get(p, [])) for p in range(1, maxp + 1)]
        block = "var LINES_EN=[" + ",".join(rows) + "];"
        html2, c = re.subn(r"var LINES_EN=\[[\s\S]*?\];", block, html, count=1)
        if c:
            html = html2
            print("  + English: %d page(s)" % maxp)
        else:
            print("  ! English block not replaced in %s" % os.path.basename(html_path))

    with io.open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("%s: updated %d page(s) -> %s" % (name, changed, os.path.basename(html_path)))


if __name__ == "__main__":
    for name, txt, html in BOOKS:
        if os.path.exists(txt) and os.path.exists(html):
            apply_book(name, txt, html)
        else:
            print("skip %s (missing file)" % name)
    print("Done. Remember to re-copy into catapp/www and rebuild the APK.")
