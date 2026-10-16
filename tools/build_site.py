"""Wrap the page (app.html, the version written for the Claude preview) into a standalone index.html for hosting,
and build _worker.js (the Letters lock) with the key from letters_key.txt.
Only needed if you edit app.html; index.html in this repo is the built result."""
from pathlib import Path
site = Path(__file__).resolve().parent.parent / 'site'
body = (site / 'app.html').read_text(encoding='utf-8')
# the hosted site is for everyone: the plain link says "My Monster Book"; gift links add ?for=Name
body = body.replace("const DEFAULT_OWNER = 'Sam';", "const DEFAULT_OWNER = '';", 1)
# Letters only for devices with the pass (see tools/_worker_src.js)
assert "const LETTERS_GATED = false;" in body
body = body.replace("const LETTERS_GATED = false;", "const LETTERS_GATED = true;", 1)
body = body.replace("<title>Sam's Monster Book</title>", "<title>My Monster Book</title>", 1)
body = body.replace('aria-label="Sam\'s Monster Book"', 'aria-label="My Monster Book"', 1)
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
<meta property="og:title" content="My Monster Book">
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

# the gatekeeper Cloudflare runs in front of the site, with the secret key from letters_key.txt (never in the repo)
import secrets
keyfile = site.parent / 'letters_key.txt'
if not keyfile.exists(): keyfile.write_text(secrets.token_urlsafe(18) + '\n')
key = keyfile.read_text().strip()
assert len(key) >= 20 and key.replace('-', '').replace('_', '').isalnum()
worker = (Path(__file__).resolve().parent / '_worker_src.js').read_text(encoding='utf-8')
assert worker.count('__LETTERS_KEY__') == 1
(site / '_worker.js').write_text(worker.replace('__LETTERS_KEY__', key), encoding='utf-8')
print('wrote', site / '_worker.js')
