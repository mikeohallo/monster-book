"""Screenshot checks: the main screens at a phone width and a laptop width, in light and dark, compared with the same
screens from another copy of the site (in CI, the current main), rendered on the same machine in the same run.

    python3 tools/test_screens.py BASE_SITE HEAD_SITE OUTDIR

Both folders need faces/ and strips/ (tools/ci_art.py makes stand-ins) and the two fonts. Fails on a page error, a
failed load, a picture that didn't load, or a sideways scroll on the new copy. A screen that looks different from the
base is listed as changed, with its picture, but doesn't fail on its own: a change can be on purpose. Nothing private
is drawn: no name, stand-in art only.
"""
import functools, http.server, socketserver, sys, threading
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

BASE, HEAD, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
SCREENS = [('town', ''), ('games', '#games'), ('make', '#make'), ('library', '#monsters')]
SIZES = [('phone', 390, 844, True), ('laptop', 1280, 800, False)]
SCHEMES = ['light', 'dark']
# the page picks some things at random (name ideas, who waves): the same numbers every time, so screens compare
SEEDED = """(() => { let s = 12345; Math.random = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; }; })();"""

socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
def serve(d, port):
    s = socketserver.TCPServer(('127.0.0.1', port), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(d)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s
servers = {'base': (serve(BASE, 8801), 8801), 'head': (serve(HEAD, 8802), 8802)}

problems, changed = [], []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

def shoot(b, which, size, scheme, screen, hash_):
    _, port = servers[which]
    name, w, h, mobile = size
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                        color_scheme=scheme, reduced_motion='reduce')
    css = (f"@font-face{{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:{port}/Fredoka.ttf)}}"
           f"@font-face{{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:{port}/Nunito.ttf)}}")
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    ctx.add_init_script(SEEDED)
    p = ctx.new_page()
    errs = []
    p.on('pageerror', lambda e: errs.append(f'page error: {e}'))
    p.on('console', lambda m: m.type == 'error' and errs.append(f'console error: {m.text}'))
    p.on('requestfailed', lambda r: 'fonts.g' not in r.url and errs.append(f'failed: {r.url}'))
    p.goto(f'http://127.0.0.1:{port}/index.html{hash_}')
    p.wait_for_timeout(1800)
    path = OUT / f'{which}_{screen}_{name}_{scheme}.png'
    p.screenshot(path=path)
    info = p.evaluate("""() => ({ wide: document.documentElement.scrollWidth > innerWidth,
        broken: [...document.images].filter(i => i.offsetParent && i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src')) })""")
    ctx.close()
    return path, errs, info

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for screen, hash_ in SCREENS:
        for size in SIZES:
            for scheme in SCHEMES:
                label = f'{screen}, {size[0]} ({size[1]}x{size[2]}), {scheme}'
                new, errs, info = shoot(b, 'head', size, scheme, screen, hash_)
                check(f'{label}: no errors, every picture loaded, no sideways scroll {errs[:2] + info["broken"][:2]}',
                      not errs and not info['broken'] and not info['wide'])
                old, _, _ = shoot(b, 'base', size, scheme, screen, hash_)
                a, c = Image.open(old).convert('RGB'), Image.open(new).convert('RGB')
                if a.size != c.size:
                    changed.append(f'{label}: size {a.size} -> {c.size}'); continue
                diff = ImageChops.difference(a, c).convert('L').point(lambda v: 255 if v > 24 else 0)
                share = diff.histogram()[255] / (a.size[0] * a.size[1])
                if share > 0.005:
                    changed.append(f'{label}: {share:.1%} of the screen differs from the base')
                    diff.save(OUT / f'diff_{screen}_{size[0]}_{scheme}.png')
                else:
                    old.unlink()   # the same as the base: only the new picture is kept
    b.close()
for s, _ in servers.values(): s.shutdown()
print('\nlooks different from the base (check the pictures; not a failure on its own):' if changed else '\nevery screen looks the same as the base',
      *changed, sep='\n  ')
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
sys.exit(1 if problems else 0)
