"""Play the match game in Chromium at phone size and screenshot each level.
    python3 tools/test_match.py OUTDIR"""
import http.server, socketserver, sys, threading, functools, time
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
PORT = 8797
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()

problems = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:%d/Fredoka.ttf)}"
           "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:%d/Nunito.ttf)}") % (PORT, PORT)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    page = ctx.new_page()
    page.on('console', lambda m: m.type == 'error' and problems.append(f'console error: {m.text}'))
    page.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    page.goto(f'http://127.0.0.1:{PORT}/index.html'); page.wait_for_timeout(800)
    page.click('#tabMatch'); page.wait_for_timeout(600)
    print('tabs fit:', page.evaluate("document.querySelector('.tabs').scrollWidth <= document.querySelector('.tabs').clientWidth"),
          '| page wider than screen:', page.evaluate('document.documentElement.scrollWidth > innerWidth'))
    page.screenshot(path=OUT / 'm1_easy.png', full_page=True)
    # play the easy game with perfect memory: reveal via the DOM, then click pairs
    faces = page.eval_on_selector_all('.mcard img', 'els => els.map(e => e.getAttribute("src"))')
    print('easy board:', len(faces), 'cards,', len(set(faces)), 'distinct monsters')
    pairs = {}
    for i, f in enumerate(faces): pairs.setdefault(f, []).append(i)
    # first, one deliberate mismatch to check the flip-back
    a, b2 = pairs[faces[0]][0], [i for i, f in enumerate(faces) if f != faces[0]][0]
    page.click(f'.mcard >> nth={a}'); page.wait_for_timeout(100)
    page.screenshot(path=OUT / 'm2_one_up.png')
    page.click(f'.mcard >> nth={b2}'); page.wait_for_timeout(300)
    page.screenshot(path=OUT / 'm3_mismatch.png')
    page.wait_for_timeout(1000)
    print('after mismatch, cards up:', page.eval_on_selector_all('.mcard.up', 'els => els.length'), '| flips:', page.text_content('#flips'))
    for f, (i, j) in pairs.items():
        page.click(f'.mcard >> nth={i}'); page.wait_for_timeout(80)
        page.click(f'.mcard >> nth={j}'); page.wait_for_timeout(250)
    page.wait_for_timeout(1200)
    print('found:', page.text_content('#found'), 'of', page.text_content('#total'), '| flips:', page.text_content('#flips'), '| win shown:', page.is_visible('#win'))
    print('win text:', page.text_content('#winTitle'), '-', page.text_content('#winText'))
    page.screenshot(path=OUT / 'm4_win.png', full_page=True)
    # play again, worse score, best should persist
    page.click('#again'); page.wait_for_timeout(500)
    print('best shown after new game:', page.text_content('#best'))
    # each level renders and fits
    for k, name in enumerate(['easy', 'medium', 'hard', 'monster']):
        page.click(f'.level >> nth={k}'); page.wait_for_timeout(500)
        n = page.eval_on_selector_all('.mcard', 'els => els.length')
        w = page.evaluate("document.querySelector('.mcard').getBoundingClientRect().width")
        over = page.evaluate('document.documentElement.scrollWidth > innerWidth')
        print(f'{name}: {n} cards, card {w:.0f}px wide, overflow {over}')
        page.screenshot(path=OUT / f'm5_{name}.png', full_page=(k < 3))
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'no errors', *problems, sep='\n  ')
