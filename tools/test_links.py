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
socketserver.ThreadingTCPServer.daemon_threads = True
srv = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
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
    check('Make tab sets #make', p.evaluate('location.hash') == '#make')
    p.click('#tabLib'); p.wait_for_timeout(300)
    check('My monsters tab sets #monsters', p.evaluate('location.hash') == '#monsters')
    p.click('#tabGames'); p.wait_for_timeout(300)
    check('Play tab sets #games', p.evaluate('location.hash') == '#games' and p.is_visible('#games'))
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('Town tab clears the hash (the town is the front page)', p.evaluate('location.hash') == '' and p.is_visible('#town'))
    for tile, h in (('#playMatch', '#match'), ('#playWhack', '#whack'), ('#playBed', '#bedtime')):
        p.click('#tabGames'); p.click(tile); p.wait_for_timeout(300)
        check(f'{tile} sets {h}', p.evaluate('location.hash') == h)
    for h, sec in (('#whack', '#whackgame'), ('#bedtime', '#bedgame'), ('#make', '#make'), ('#games', '#games')):
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
    p.goto(BASE + '?for=Alex#match'); p.wait_for_timeout(700)
    title = p.text_content('.title')
    check(f'?for=Alex#match: title "{title.strip()}" and on the game', 'Alex' in title and p.is_visible('#matchgame'))
    p.click('#tabMake'); p.wait_for_timeout(300)
    check('gift link keeps ?for=Alex after switching tabs', p.evaluate('location.search') == '?for=Alex')
    # 7. typing a hash by hand switches screens
    p.evaluate("location.hash = '#monsters'"); p.wait_for_timeout(300)
    check('changing the hash to #monsters shows the library', p.is_visible('#library'))
    p.evaluate("location.hash = ''"); p.wait_for_timeout(300)
    check('clearing the hash goes back to the town', p.is_visible('#town'))
    # 8. the plain link opens on the town; the games page has Make a monster first, showing the monster on the flip book
    p.goto(BASE); p.wait_for_timeout(600)
    check('plain link opens on the town, Town tab selected', p.is_visible('#town') and not p.is_visible('#games') and p.get_attribute('#tabTown', 'aria-selected') == 'true')
    p.click('#tabGames'); p.wait_for_timeout(300)
    first = p.eval_on_selector_all('#games .gamelist > *', 'e => e[0].id')
    check(f'the games page has Make a monster first ({first})', p.is_visible('#games') and not p.is_visible('#make')
          and p.get_attribute('#tabGames', 'aria-selected') == 'true' and first == 'playMake')
    order = p.eval_on_selector_all('.tab .tlabel', 'e => e.map(x => x.textContent.trim())')
    check(f'tabs in order: {order}', order == ['Town', 'Play', 'Make', 'My monsters'])
    p.click('#playMake'); p.wait_for_timeout(300)
    check('Make a monster opens the flip book (#make)', p.is_visible('#make') and p.evaluate('location.hash') == '#make' and p.get_attribute('#tabMake', 'aria-selected') == 'true')
    p.click('.strip[data-part="H"] .next'); p.wait_for_timeout(700)
    h = p.evaluate('state.H')
    p.click('#tabGames'); p.wait_for_timeout(300)
    check(f'the Make card shows the monster on the flip book (head {h})', p.get_attribute('#mkH', 'src').endswith(f'H{h:02d}.webp'))
    p.screenshot(path=OUT / 'home.png', full_page=True)
    title = p.get_attribute('#title', 'aria-label')
    check(f'the site is called Monster Lab ("{title}")', title.endswith('Monster Lab'))
    # 9. old Letters and Numbers links go to the Learning Lab, with the name
    seen = []   # where the page went (the address with its #part, which never reaches a server)
    ctx.route('https://learn.mikeohalloran.au/**', lambda r: r.fulfill(status=200, content_type='text/html', body='<p>learning lab</p>'))
    p.on('framenavigated', lambda f: f == p.main_frame and f.url.startswith('https://learn.') and seen.append(f.url))
    for h in ('#letters', '#count', '#quick'):
        p.goto(BASE + '?for=Sam' + h, wait_until='commit'); p.wait_for_url('https://learn.mikeohalloran.au/**', timeout=8000); p.wait_for_timeout(200)
    check(f'#letters, #count and #quick go to the Learning Lab ({len(seen)} hops)', seen == [f'https://learn.mikeohalloran.au/?for=Sam{h}' for h in ('#letters', '#count', '#quick')])
    # 10. the one-time hand-over: this site's saved Letters and Numbers progress goes back to the Learning Lab
    seen.clear()
    p.goto(BASE, wait_until='domcontentloaded'); p.wait_for_timeout(300); p.evaluate("localStorage.setItem('monster-book.letters', JSON.stringify({ next: 'k', mode: 'spell', traced: { a: 1 } })); localStorage.setItem('monster-book.numbers', JSON.stringify({ count: '2' })); localStorage.setItem('monster-book.sound', 'off')")
    p.goto(BASE + '?handoff=learn&for=Sam&to=letters', wait_until='commit'); p.wait_for_timeout(800)
    import json as _j, urllib.parse as _u
    got = _j.loads(_u.unquote(seen[0].split('#import=', 1)[1])) if seen and '#import=' in seen[0] else {}
    check(f'?handoff=learn sends the progress straight back ({seen[0][:60] if seen else "no hop"}...)', seen and seen[0].startswith('https://learn.mikeohalloran.au/?for=Sam#import=')
          and _j.loads(got.get('letters') or '{}').get('next') == 'k' and _j.loads(got.get('numbers') or '{}').get('count') == '2' and got.get('sound') == 'off' and got.get('to') == 'letters')
    p.goto(BASE + '?handoff=learn&to=../../evil', wait_until='commit'); p.wait_for_timeout(800)
    check('  it only ever goes to the Learning Lab, and drops a strange "to"', seen[-1].startswith('https://learn.mikeohalloran.au/') and '"to":""' in _u.unquote(seen[-1]))
    p.evaluate("localStorage.removeItem('monster-book.letters'); localStorage.removeItem('monster-book.numbers'); localStorage.removeItem('monster-book.sound')")
    ctx.close(); b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
