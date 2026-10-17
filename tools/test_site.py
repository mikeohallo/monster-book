"""Drive the site in Chromium at phone size, check each step and screenshot each screen. Exits non-zero if anything fails.
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
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)
codes = lambda pg: [c.split()[0] for c in pg.eval_on_selector_all('.chip .code', 'els => els.map(e => e.textContent)')]

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
    page.goto('http://127.0.0.1:8791/index.html#make')
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / '1_make.png', full_page=True)
    # flip each strip forward and the head back
    page.click('.strip[data-part="H"] .next'); page.wait_for_timeout(150)
    page.screenshot(path=OUT / '1b_midflip.png')
    page.wait_for_timeout(500)
    page.click('.strip[data-part="B"] .next'); page.click('.strip[data-part="L"] .prev'); page.wait_for_timeout(700)
    check(f'flipping: head and body forward, legs back ({codes(page)})', codes(page) == ['H02', 'B03', 'L02'])
    # type codes: the whole fox
    page.click('#typeCodes'); page.fill('#cH', '18'); page.fill('#cB', 'B18'); page.fill('#cL', '18')
    page.click('#codes button[type=submit]'); page.wait_for_timeout(900)
    check(f'typed codes 18, B18, 18 give the whole fox ({codes(page)}, "{page.text_content("#match")}")', codes(page) == ['H18', 'B18', 'L18'] and 'Fox' in page.text_content('#match'))
    # bad code
    page.click('#typeCodes'); page.fill('#cH', '45'); page.click('#codes button[type=submit]')
    check(f'a code over 30 is refused with a message ("{page.text_content("#codeErr")}")', '1 to 30' in page.text_content('#codeErr') and codes(page) == ['H18', 'B18', 'L18'])
    page.fill('#cH', '18'); page.fill('#cB', '26'); page.fill('#cL', '7'); page.click('#codes button[type=submit]'); page.wait_for_timeout(900)
    # swipe the body strip left (next)
    box = page.locator('.strip[data-part="B"]').bounding_box()
    y = box['y'] + box['height'] / 2
    page.mouse.move(box['x'] + box['width'] * .7, y); page.mouse.down(); page.mouse.move(box['x'] + box['width'] * .3, y, steps=6); page.mouse.up()
    page.wait_for_timeout(700)
    check(f'swiping the body left turns to the next one ({codes(page)})', codes(page) == ['H18', 'B27', 'L07'])
    page.click('.strip[data-part="B"] .prev'); page.wait_for_timeout(700)
    page.screenshot(path=OUT / '2_mixed.png', full_page=True)
    # meet
    page.click('#toMeet'); page.wait_for_timeout(1200)
    page.click('#makeName'); check(f'"make up a name" fills in a name ({page.input_value("#q_name")})', len(page.input_value('#q_name')) >= 3)
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
    check('the card is a real picture, with a save button', len(data) > 10000 and page.is_visible('#dl'))
    page.click('#saveLib'); page.wait_for_timeout(300)
    check(f'saving: "{page.text_content("#saveLib")}", My monsters count {page.text_content("#libCount")}', 'Saved' in page.text_content('#saveLib') and page.text_content('#libCount').strip() == '1')
    # change answers -> save changes
    page.click('#editAns'); page.wait_for_timeout(500); page.fill('#q_grumpy', 'Bath time and broccoli'); page.click('#toCard')
    page.wait_for_timeout(1500); check(f'changed answers offer "{page.text_content("#saveLib")}"', 'Save changes' in page.text_content('#saveLib'))
    page.click('#saveLib'); page.wait_for_timeout(200)
    # second monster
    page.click('#another'); page.wait_for_timeout(300); page.click('#shuffle'); page.wait_for_timeout(1200)
    page.click('#toMeet'); page.wait_for_timeout(800); page.fill('#q_name', 'Princess Wobble'); page.click('#toCard'); page.wait_for_timeout(1800); page.click('#saveLib')
    # library
    page.click('#tabLib'); page.wait_for_timeout(2500)
    page.screenshot(path=OUT / '5_library.png', full_page=True)
    stored = page.evaluate("localStorage.getItem('monster-book.v1')")
    d = json.loads(stored); got = [(m['name'], m['h'], m['b'], m['l'], m.get('grumpy')) for m in d['monsters']]
    check(f'both monsters saved, the first with its changed answer and codes {got}', [m['name'] for m in d['monsters']] == ['Fuzzbert', 'Princess Wobble']
          and got[0] == ('Fuzzbert', 18, 26, 7, 'Bath time and broccoli') and page.eval_on_selector_all('.tile', 'e => e.length') == 2)
    # owner name
    page.fill('#owner', 'Max'); page.press('#owner', 'Tab'); page.wait_for_timeout(200)
    check(f'the owner name renames the site ("{page.get_attribute("#title", "aria-label")}")', page.get_attribute('#title', 'aria-label') == "Max's Monster Lab")
    # open a saved one, delete needs two taps
    page.click('.tile >> nth=0'); page.wait_for_timeout(1800)
    page.click('#del'); check(f'delete asks twice: "{page.text_content("#del")}", still {page.text_content("#libCount")}', 'again' in page.text_content('#del') and page.text_content('#libCount').strip() == '2')
    page.click('#del'); page.wait_for_timeout(300); check(f'the second tap deletes it ({page.text_content("#libCount")} left)', page.text_content('#libCount').strip() == '1')
    # backup / restore round trip
    backup = page.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('monster-book.v1')))")
    page.evaluate("localStorage.removeItem('monster-book.v1')"); page.reload(); page.wait_for_timeout(800)
    page.click('#tabLib'); page.wait_for_timeout(300); check(f'with the saved data cleared, My monsters is empty ({page.text_content("#libCount")})', page.text_content('#libCount').strip() in ('', '0'))
    payload = json.dumps({'app': 'monster-book', 'version': 1, 'owner': 'Max', 'monsters': json.loads(backup)['monsters']})
    page.set_input_files('#restoreFile', files=[{'name': 'b.json', 'mimeType': 'application/json', 'buffer': payload.encode()}])
    page.wait_for_timeout(800)
    restored = json.loads(page.evaluate("localStorage.getItem('monster-book.v1')") or '{}')
    check(f'restoring the backup brings the monster and the owner back ({page.text_content("#libCount")}, "{page.get_attribute("#title", "aria-label")}")',
          page.text_content('#libCount').strip() == '1' and [m['name'] for m in restored.get('monsters', [])] == [m['name'] for m in json.loads(backup)['monsters']]
          and page.get_attribute('#title', 'aria-label') == "Max's Monster Lab")
    page.screenshot(path=OUT / '6_library_restored.png', full_page=True)
    # horizontal overflow check
    check('no sideways scroll', not page.evaluate('document.documentElement.scrollWidth > innerWidth'))
    # empty state on a fresh device
    p2 = ctx.new_page(); p2.goto('http://127.0.0.1:8791/index.html?for=Alex'); p2.evaluate("localStorage.clear()"); p2.reload(); p2.wait_for_timeout(800)
    p2.click('#tabLib'); p2.wait_for_timeout(300); p2.screenshot(path=OUT / '7_empty.png', full_page=True)
    check(f'a gift link on a fresh device: "{p2.get_attribute("#title", "aria-label")}", nothing saved', p2.get_attribute('#title', 'aria-label') == "Alex's Monster Lab"
          and p2.text_content('#libCount').strip() in ('', '0'))
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good: no failed checks, console errors or failed loads', *problems, sep='\n  ')
sys.exit(1 if problems else 0)
