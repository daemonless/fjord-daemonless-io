#!/usr/bin/env python3
"""Fail the build when Markdown reached the published HTML unrendered.

Two things went wrong on the home page and would again: an icon code shown
as text (:material-server:), and a code block's notes left as plain text, so
its # (1) markers get no bubbles. Both happen when Markdown sits inside an
HTML block without the markdown attribute (<div class="..." markdown>).
The # (1) markers themselves stay in the HTML on purpose: the page's script
turns them into bubbles, using the <ol> that must follow the code block.
"""
import pathlib, re, sys

site = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site")
icon = re.compile(r":(?:material|fontawesome|octicons|simple)-[a-z0-9-]+:")
marker = re.compile(r'<span class="c1?">[^<]*\((\d+)\)!?</span>')
problems = []
for page in sorted(site.rglob("*.html")):
    html = page.read_text(errors="replace")
    for m in icon.finditer(html):
        problems.append(f"{page}: icon code shown as text: {m.group(0)}")
    # Each code block with markers must be followed by the list of notes.
    for block in re.finditer(r'<pre[^>]*>.*?</pre>', html, re.S):
        if not marker.search(block.group(0)):
            continue
        rest = re.sub(r'^(\s*</(?:code|div|span)>)*\s*', '', html[block.end():block.end() + 2000])
        if not rest.startswith("<ol"):
            problems.append(f"{page}: a code block's # (1) notes are not a list after it (Markdown inside HTML without the markdown attribute?)")
for p in problems:
    print(p)
if not problems:
    print("Rendered: no raw icon codes, every annotated code block has its notes.")
sys.exit(1 if problems else 0)
