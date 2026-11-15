#!/usr/bin/env python3
"""Fail the build when Markdown reached the published HTML unrendered.

Checks across all generated HTML pages:
1. Unrendered icon shortcodes (:material-server:, :simple-*, etc.).
2. Annotated code blocks (# (1)) missing their <ol> note list immediately after.
3. Unrendered admonitions / details fences (!!! note, ??? ") left as body text.
4. Broken YAML frontmatter rendered into visible <p>title: ... body text.
5. Instant-preview attributes (data-preview) emitted on internal doc links.
"""
import pathlib
import re
import sys

site = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site")
icon = re.compile(r":(?:material|fontawesome|octicons|simple)-[a-z0-9-]+:")
marker = re.compile(r'<span class="c1?">[^<]*\((\d+)\)!?</span>')
raw_admonition = re.compile(r"(?:<p>|<li>|\n)\s*(?:!!!|\?\?\?\+?)\s+(?:[a-z]+|\"|&quot;)")
raw_frontmatter = re.compile(r"<p>\s*title:\s*(?:\"|&quot;|')")

problems = []
preview_links = 0

for page in sorted(site.rglob("*.html")):
    html = page.read_text(errors="replace")
    preview_links += html.count("data-preview")
    # Strip <pre>...</pre> and <code>...</code> before prose-only checks.
    prose = re.sub(r"<pre[^>]*>.*?</pre>", "", html, flags=re.S)
    prose = re.sub(r"<code[^>]*>.*?</code>", "", prose, flags=re.S)

    for m in icon.finditer(prose):
        problems.append(f"{page}: icon code shown as text: {m.group(0)}")
    for m in raw_admonition.finditer(prose):
        snippet = " ".join(m.group(0).split())
        problems.append(f"{page}: unrendered admonition shown as text: {snippet}")
    for m in raw_frontmatter.finditer(prose):
        problems.append(f"{page}: broken YAML frontmatter rendered as body text")

    # Each code block with markers must be followed by the list of notes.
    for block in re.finditer(r"<pre[^>]*>.*?</pre>", html, re.S):
        if not marker.search(block.group(0)):
            continue
        rest = re.sub(r"^(\s*</(?:code|div|span)>)*\s*", "", html[block.end():block.end() + 2000])
        if not rest.startswith("<ol"):
            problems.append(
                f"{page}: a code block's # (1) notes are not a list after it "
                "(Markdown inside HTML without the markdown attribute?)"
            )

if preview_links == 0:
    problems.append(f"{site}: zero data-preview links generated (is zensical.extensions.preview configured?)")

for p in problems:
    print(p)
if not problems:
    print(f"Rendered: no raw icon codes, admonitions, or frontmatter leaks; {preview_links} preview links active.")
sys.exit(1 if problems else 0)
