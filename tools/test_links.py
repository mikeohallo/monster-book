"""Check the tab icons fit on narrow phones and that #match / #monsters links work.
    python3 tools/test_links.py OUTDIR"""
import http.server, socketserver, sys, threading, functools
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
PORT = 8798
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{PORT}/index.html'

problems = []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:%d/Fredoka.ttf)}"
           "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:%d/Nunito.ttf)}") % (PORT, PORT)
    def ctx_for(width):
        ctx = b.new_context(viewport={'width': width, 'height': 800}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
        ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
        return ctx
    def page_for(ctx):
        p = ctx.new_page()
        p.on('console', lambda m: m.type == 'error' and problems.append(f'console error: {m.text}'))
        p.on('pageerror', lambda e: problems.append(f'page error: {e}'))
        return p

    # 1. tab bar fits at common phone widths, with a saved monster so the count shows two digits
    for w in (360, 375, 390, 430):
        ctx = ctx_for(w); p = page_for(ctx)
        p.goto(BASE); p.wait_for_timeout(700)
        p.evaluate("document.getElementById('libCount').textContent = '12'")
        fits = p.evaluate("(() => { const t = document.querySelector('.tabs'); return t.scrollWidth <= t.clientWidth && t.getBoundingClientRect().right <= innerWidth })()")
        wide = p.evaluate('document.documentElement.scrollWidth > innerWidth')
        icons = p.evaluate("[...document.querySelectorAll('.tab .ticon')].map(e => Math.round(e.getBoundingClientRect().height))")
        loaded = p.evaluate("[...document.querySelectorAll('.tab img')].every(i => i.complete && i.naturalWidth > 0)")
        bar = p.evaluate("Math.round(document.querySelector('.tabs').getBoundingClientRect().width)")
        check(f'{w}px: tabs fit ({bar}px bar), no sideways scroll, icon heights {icons}, images loaded', fits and not wide and loaded)
        p.locator('header').screenshot(path=OUT / f'tabs_{w}.png')
        ctx.close()

    ctx = ctx_for(390); p = page_for(ctx)
    # 2. opening #match goes straight to the game
    p.goto(BASE + '#match'); p.wait_for_timeout(700)
    check('#match opens the game', p.is_visible('#matchgame') and not p.is_visible('#make') and p.eval_on_selector_all('.mcard', 'e => e.length') == 12)
    check('#match: Games tab selected', p.get_attribute('#tabGames', 'aria-selected') == 'true')
    p.screenshot(path=OUT / 'direct_match.png')
    # 3. tabs update the address
    p.click('#tabMake'); p.wait_for_timeout(300)
    check('Make tab clears the hash', p.evaluate('location.hash') == '')
    p.click('#tabLib'); p.wait_for_timeout(300)
    check('My monsters tab sets #monsters', p.evaluate('location.hash') == '#monsters')
    p.click('#tabGames'); p.wait_for_timeout(300)
    check('Games tab sets #games', p.evaluate('location.hash') == '#games')
    for tile, h in (('#playMatch', '#match'), ('#playWhack', '#whack'), ('#playBed', '#bedtime')):
        p.click('#tabGames'); p.click(tile); p.wait_for_timeout(300)
        check(f'{tile} sets {h}', p.evaluate('location.hash') == h)
    for h, sec in (('#whack', '#whackgame'), ('#bedtime', '#bedgame'), ('#games', '#games')):
        p.evaluate(f"location.hash = '{h}'"); p.wait_for_timeout(300)
        check(f'typing {h} shows {sec}', p.is_visible(sec))
    p.click('#tabGames'); p.click('#playMatch'); p.wait_for_timeout(300)
    # 4. game survives a reload on #match (new board, but still on the game)
    p.reload(); p.wait_for_timeout(700)
    check('reload on #match stays on the game', p.is_visible('#matchgame'))
    # 5. back button still leaves the site rather than stepping through tabs
    hist = p.evaluate('history.length')
    p.click('#tabMake'); p.click('#tabGames'); p.click('#playWhack'); p.wait_for_timeout(200)
    check('tab switches do not pile up history', p.evaluate('history.length') == hist)
    # 6. a gift link keeps its name with #match
    p.goto(BASE + '?for=Ivy#match'); p.wait_for_timeout(700)
    title = p.text_content('.title')
    check(f'?for=Ivy#match: title "{title.strip()}" and on the game', 'Ivy' in title and p.is_visible('#matchgame'))
    p.click('#tabMake'); p.wait_for_timeout(300)
    check('gift link keeps ?for=Ivy after switching tabs', p.evaluate('location.search') == '?for=Ivy')
    # 7. typing a hash by hand switches screens
    p.evaluate("location.hash = '#monsters'"); p.wait_for_timeout(300)
    check('changing the hash to #monsters shows the library', p.is_visible('#library'))
    p.evaluate("location.hash = ''"); p.wait_for_timeout(300)
    check('clearing the hash goes back to Make', p.is_visible('#make'))
    # 8. plain link still opens on Make
    p.goto(BASE); p.wait_for_timeout(600)
    check('plain link opens on Make', p.is_visible('#make') and p.get_attribute('#tabMake', 'aria-selected') == 'true')
    ctx.close(); b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
