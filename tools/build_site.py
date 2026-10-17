"""Wrap the page (app.html, the version written for the Claude preview) into a standalone index.html for hosting.
Only needed if you edit app.html; index.html in this repo is the built result."""
import re
from pathlib import Path
site = Path(__file__).resolve().parent.parent / 'site'
body = (site / 'app.html').read_text(encoding='utf-8')
def sub1(pattern, repl):   # exactly one match, or stop
    global body
    body, n = re.subn(pattern, lambda m: repl, body, count=1)
    assert n == 1, pattern
# the hosted site is for everyone: no name built in, so the plain link says "My Monster Lab"; gift links add ?for=Name
sub1(r"const DEFAULT_OWNER = '[^'\n]*';", "const DEFAULT_OWNER = '';")
sub1(r"<title>[^<\n]*Monster Lab</title>", "<title>My Monster Lab</title>")
sub1(r'aria-label="[^"\n]*Monster Lab"', 'aria-label="My Monster Lab"')
SITE_URL = 'https://monsters.mikeohalloran.au'
head_end = body.index('<style>')
head, rest = body[:head_end], body[head_end:]
style_end = rest.index('</style>') + len('</style>')
style, content = rest[:style_end], rest[style_end:]
page = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FFF8EC">
<meta name="robots" content="noindex">
<link rel="icon" href="faces/F01.webp" type="image/webp">
<meta property="og:title" content="My Monster Lab">
<meta property="og:description" content="Flip a head, a body and some legs, meet your monster, and make its card.">
<meta property="og:image" content="{SITE_URL}/faces/F01.webp">
<meta property="og:url" content="{SITE_URL}/">
{head.strip()}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}} body{{margin:0}} img{{max-width:100%}}</style>
{style}
</head>
<body>
{content.strip()}
</body>
</html>
"""
(site / 'index.html').write_text(page, encoding='utf-8')
print('wrote', site / 'index.html', len(page), 'bytes')
