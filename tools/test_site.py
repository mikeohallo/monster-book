"""Drive the site in Chromium at phone size and screenshot each screen.
    python3 tools/test_site.py OUTDIR   (serves the repo root on port 8791 while it runs)"""
import http.server, socketserver, sys, threading, functools, json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(('127.0.0.1', 8791), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

problems = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:8791/Fredoka.ttf)}"
           "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:8791/Nunito.ttf)}")
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    page = ctx.new_page()
    page.on('console', lambda m: m.type in ('error', 'warning') and problems.append(f'console {m.type}: {m.text}'))
    page.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    page.on('requestfailed', lambda r: 'fonts.g' not in r.url and problems.append(f'failed: {r.url}'))
    page.goto('http://127.0.0.1:8791/index.html')
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / '1_make.png', full_page=True)
    # flip each strip forward and the head back
    page.click('.strip[data-part="H"] .next'); page.wait_for_timeout(150)
    page.screenshot(path=OUT / '1b_midflip.png')
    page.wait_for_timeout(500)
    page.click('.strip[data-part="B"] .next'); page.click('.strip[data-part="L"] .prev'); page.wait_for_timeout(700)
    chips = page.eval_on_selector_all('.chip .code', 'els => els.map(e => e.textContent)')
    print('after flips:', chips)
    # type codes: the whole fox
    page.click('#typeCodes'); page.fill('#cH', '18'); page.fill('#cB', 'B18'); page.fill('#cL', '18')
    page.click('#codes button[type=submit]'); page.wait_for_timeout(900)
    print('codes 18/18/18:', page.eval_on_selector_all('.chip .code', 'els => els.map(e => e.textContent)'), '|', page.text_content('#match'))
    # bad code
    page.click('#typeCodes'); page.fill('#cH', '45'); page.click('#codes button[type=submit]')
    print('bad code message:', page.text_content('#codeErr'))
    page.fill('#cH', '18'); page.fill('#cB', '26'); page.fill('#cL', '7'); page.click('#codes button[type=submit]'); page.wait_for_timeout(900)
    # swipe the body strip left (next)
    box = page.locator('.strip[data-part="B"]').bounding_box()
    y = box['y'] + box['height'] / 2
    page.mouse.move(box['x'] + box['width'] * .7, y); page.mouse.down(); page.mouse.move(box['x'] + box['width'] * .3, y, steps=6); page.mouse.up()
    page.wait_for_timeout(700)
    print('after swipe:', page.eval_on_selector_all('.chip .code', 'els => els.map(e => e.textContent)'))
    page.click('.strip[data-part="B"] .prev'); page.wait_for_timeout(700)
    page.screenshot(path=OUT / '2_mixed.png', full_page=True)
    # meet
    page.click('#toMeet'); page.wait_for_timeout(1200)
    page.click('#makeName'); print('made-up name:', page.input_value('#q_name'))
    page.fill('#q_name', 'Fuzzbert'); page.fill('#q_food', 'Spaghetti and pancakes'); page.fill('#q_friend', 'A snail called Gary'); page.fill('#q_grumpy', 'Bath time')
    page.screenshot(path=OUT / '3_meet.png', full_page=True)
    page.click('#toCard'); page.wait_for_function("document.getElementById('cardImg').complete && document.getElementById('cardImg').naturalWidth > 0", timeout=15000)
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / '4_card.png', full_page=True)
    src = page.get_attribute('#cardImg', 'src')
    data = page.evaluate("""async () => { const r = await fetch(document.getElementById('cardImg').src); const b = await r.blob();
        return await new Promise(res => { const f = new FileReader(); f.onload = () => res(f.result); f.readAsDataURL(b); }); }""")
    import base64
    (OUT / 'card_full.png').write_bytes(base64.b64decode(data.split(',', 1)[1]))
    print('download button visible (top-level):', page.is_visible('#dl'))
    page.click('#saveLib'); page.wait_for_timeout(300)
    print('save button now:', page.text_content('#saveLib'), '| count', page.text_content('#libCount'))
    # change answers -> save changes
    page.click('#editAns'); page.wait_for_timeout(500); page.fill('#q_grumpy', 'Bath time and broccoli'); page.click('#toCard')
    page.wait_for_timeout(1500); print('after edit, save button:', page.text_content('#saveLib'))
    page.click('#saveLib'); page.wait_for_timeout(200)
    # second monster
    page.click('#another'); page.wait_for_timeout(300); page.click('#shuffle'); page.wait_for_timeout(1200)
    page.click('#toMeet'); page.wait_for_timeout(800); page.fill('#q_name', 'Princess Wobble'); page.click('#toCard'); page.wait_for_timeout(1800); page.click('#saveLib')
    # library
    page.click('#tabLib'); page.wait_for_timeout(2500)
    page.screenshot(path=OUT / '5_library.png', full_page=True)
    stored = page.evaluate("localStorage.getItem('monster-book.v1')")
    d = json.loads(stored); print('stored monsters:', [(m['name'], m['h'], m['b'], m['l'], m.get('grumpy')) for m in d['monsters']])
    # owner name
    page.fill('#owner', 'Max'); page.press('#owner', 'Tab'); page.wait_for_timeout(200)
    print('title now:', page.get_attribute('#title', 'aria-label'))
    # open a saved one, delete needs two taps
    page.click('.tile >> nth=0'); page.wait_for_timeout(1800)
    page.click('#del'); print('first tap:', page.text_content('#del'), '| count', page.text_content('#libCount'))
    page.click('#del'); page.wait_for_timeout(300); print('after second tap, count:', page.text_content('#libCount'))
    # backup / restore round trip
    backup = page.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('monster-book.v1')))")
    page.evaluate("localStorage.removeItem('monster-book.v1')"); page.reload(); page.wait_for_timeout(800)
    page.click('#tabLib'); page.wait_for_timeout(300); print('after clearing, count:', page.text_content('#libCount'))
    payload = json.dumps({'app': 'monster-book', 'version': 1, 'owner': 'Max', 'monsters': json.loads(backup)['monsters']})
    page.set_input_files('#restoreFile', files=[{'name': 'b.json', 'mimeType': 'application/json', 'buffer': payload.encode()}])
    page.wait_for_timeout(800); print('after restore, count:', page.text_content('#libCount'), '| title', page.get_attribute('#title', 'aria-label'))
    page.screenshot(path=OUT / '6_library_restored.png', full_page=True)
    # horizontal overflow check
    print('page wider than screen:', page.evaluate('document.documentElement.scrollWidth > innerWidth'))
    # empty state on a fresh device
    p2 = ctx.new_page(); p2.goto('http://127.0.0.1:8791/index.html?for=Alex'); p2.evaluate("localStorage.clear()"); p2.reload(); p2.wait_for_timeout(800)
    p2.click('#tabLib'); p2.wait_for_timeout(300); p2.screenshot(path=OUT / '7_empty.png', full_page=True)
    print('?for=Alex title:', p2.get_attribute('#title', 'aria-label'))
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'no console errors or failed loads', *problems, sep='\n  ')
