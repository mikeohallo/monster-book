"""Keeping monsters safe: a phone linked to the family's private store by three faces and a grown-up's passkey, saving
every change, a new phone bringing it all back, an unlinked phone, and 3D monsters in the town. Runs the private store
(the monster-store repo, beside this one or at $MONSTER_STORE) on this machine, with a pretend Gemini and a pretend
passkey; nothing talks to Cloudflare or Google. Without the store repo, it says so and skips.
    python3 tools/test_keep.py OUTDIR"""
import base64, io, json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
STORE = Path(os.environ.get('MONSTER_STORE') or SITE.parent / 'monster-store')
if not (STORE / 'test' / 'stack.py').exists() or not (STORE / 'node_modules').exists():
    print(f'skipped: needs the private monster-store repo (with npm ci done) at {STORE}')
    sys.exit(0)
sys.path.insert(0, str(STORE / 'test'))
from stack import Stack, SETUP_CODE
from PIL import Image

problems = []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

with Stack(SITE) as s:
    F = s.front
    css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(%s/Fredoka.ttf)}"
           "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(%s/Nunito.ttf)}") % (F, F)
    # the pretend Gemini answers with a real 3D monster on white
    buf = io.BytesIO(); Image.open(STORE / 'art' / 'style_ref.jpg').convert('RGB').save(buf, 'PNG'); s.gemini.answer = buf.getvalue()

    def phone(b, w=673, h=760):
        ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
        ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
        p = ctx.new_page()
        p.store_calls = []
        p.on('request', lambda r: p.store_calls.append(r.method + ' ' + r.url.split(F)[-1]) if '/store/' in r.url else None)
        p.on('console', lambda m: m.type == 'error' and 'Failed to load resource' not in m.text and problems.append(f'console error: {m.text}'))
        p.on('pageerror', lambda e: problems.append(f'page error: {e}'))
        return ctx, p

    def faces_on(p):
        return [int(src.split('/F')[1][:2]) for src in p.eval_on_selector_all('#keepPanel .kpfaces img', 'e => e.map(i => i.getAttribute("src"))')]

    def make_monster(p, h, b_, l, name):
        p.click('#tabMake'); p.wait_for_timeout(300)
        p.evaluate(f"goTo('H', {h}, 1); goTo('B', {b_}, 1); goTo('L', {l}, 1)"); p.wait_for_timeout(400)
        p.click('#toMeet'); p.wait_for_timeout(800)
        p.fill('#q_name', name); p.click('#p_food [data-pick="Worms"]')
        p.click('#toCard'); p.wait_for_timeout(1500)
        p.click('#saveLib'); p.wait_for_timeout(300)

    def tap(p, sel): p.eval_on_selector(sel, 'e => e.click()')

    with sync_playwright() as pw:
        b = pw.chromium.launch()

        # --- a phone that isn't linked sends nothing, and keeps nothing extra ---------------------------------------
        ctx, c = phone(b)
        c.goto(F + '/?for=Sam'); c.wait_for_timeout(1200)
        make_monster(c, 1, 2, 3, 'Gloop'); c.click('#tabLib'); c.wait_for_timeout(400)
        dbs = c.evaluate("indexedDB.databases().then(d => d.map(x => x.name))")
        check('an unlinked phone makes and saves monsters without ever calling the store', c.store_calls == [] and 'monster-book.keep' not in dbs)
        check("  My monsters doesn't mention keeping safe, and still says nothing is sent anywhere",
              not c.is_visible('#kpLine') and 'Nothing you type is sent anywhere' in c.text_content('#libNote'))
        ctx.close()

        # --- linking a phone: three faces ---------------------------------------------------------------------------
        ctx, a = phone(b)
        a.goto(F + '/?for=Sam#keep'); a.wait_for_timeout(1200)
        check('#keep opens the Keep screen, with Link this phone', a.is_visible('#keep') and a.is_visible('#kpStart') and 'Keep these monsters safe' in a.text_content('#keepPanel'))
        a.screenshot(path=OUT / 'k1_start.png')
        a.click('#kpStart'); a.wait_for_selector('#keepPanel .kpfaces img')
        fa = faces_on(a)
        check(f'Link shows three monster faces to show the grown-up {fa}', len(fa) == 3 and all(1 <= f <= 30 for f in fa)
              and a.evaluate("[...document.querySelectorAll('#keepPanel .kpfaces img')].every(i => i.complete && i.naturalWidth > 0)"))
        check('  with where the grown-up goes', 'localhost:8790/store/grownup' in a.text_content('#keepPanel'))
        key = a.evaluate("kpGet('kv', 'me').then(m => [m.keys.privateKey.extractable, m.keys.privateKey.algorithm.name, m.keys.privateKey.algorithm.namedCurve])")
        check(f"  the phone's private key can't be read out of the browser {key}", key == [False, 'ECDSA', 'P-256'])
        a.screenshot(path=OUT / 'k2_faces.png')

        # --- the grown-up says yes ----------------------------------------------------------------------------------
        gctx = b.new_context(viewport={'width': 412, 'height': 900}, bypass_csp=True)
        g = gctx.new_page()
        cdp = gctx.new_cdp_session(g); cdp.send('WebAuthn.enable')
        cdp.send('WebAuthn.addVirtualAuthenticator', {'options': {'protocol': 'ctap2', 'transport': 'internal', 'hasResidentKey': True, 'hasUserVerification': True, 'isUserVerified': True}})
        g.goto(F + '/store/grownup'); g.wait_for_selector('#setup:not([hidden])')
        g.fill('#code', SETUP_CODE); g.click('#doSetup'); g.wait_for_selector('#signedin:not([hidden])', timeout=10000)
        for f in fa: g.click(f'#faces [data-face="{f}"]')
        g.fill('#newKid', "Sam's monsters"); g.fill('#phoneLabel', 'Test Fold'); g.click('#doApprove')
        g.wait_for_function("document.getElementById('approveMsg').textContent.startsWith('Done')")
        g.screenshot(path=OUT / 'k3_grownup.png', full_page=True)
        a.wait_for_function("document.getElementById('keepPanel').textContent.includes('kept safe')", timeout=10000)
        check('the phone sees the yes by itself: "These monsters are kept safe"', 'These monsters are kept safe' in a.text_content('#keepPanel'))
        a.screenshot(path=OUT / 'k4_linked.png')

        # --- a linked phone saves every change, and makes its monsters in 3D ---------------------------------------
        a.goto(F + '/?for=Sam'); a.wait_for_timeout(1000)
        make_monster(a, 5, 9, 24, 'Fuzzbert')
        a.wait_for_function("kp.art.has('05-09-24')", timeout=20000)
        copies = s.sql('SELECT monsters, data FROM snapshots ORDER BY id DESC LIMIT 1')
        check('saving a monster copies it to the store', copies and copies[0]['monsters'] == 1 and json.loads(copies[0]['data'])['monsters'][0]['name'] == 'Fuzzbert')
        call = s.gemini.calls[-1]['body']['contents'][0]['parts'] if s.gemini.calls else []
        src = Image.open(io.BytesIO(base64.b64decode(call[0]['inlineData']['data']))) if call else None
        check(f'the 3D monster is asked for once, from the book monster drawn on the phone {src.size if src else None}',
              len(s.gemini.calls) == 1 and src and src.format == 'JPEG' and abs(src.size[1] / src.size[0] - 1485 / 925) < .01)
        art = s.sql("SELECT length(image) AS n FROM art WHERE combo = '05-09-24'")
        check(f'  the phone cut it out and sent it back to the store ({art[0]["n"] if art else 0} bytes)', art and 2000 < art[0]['n'] < 600 * 1024)
        cut = a.evaluate("fetch(kp.art.get('05-09-24').url).then(r => r.arrayBuffer()).then(b => btoa(String.fromCharCode(...new Uint8Array(b))))")
        im = Image.open(io.BytesIO(base64.b64decode(cut))).convert('RGBA')
        w, h = im.size
        corners = [im.getpixel(xy)[3] for xy in ((0, 0), (w - 1, 0), (0, h // 3), (w - 1, h // 3))]
        check(f'  the white is gone from around it, and it is trimmed to the monster ({w}x{h}, corners {corners})', max(corners) < 30 and im.getpixel((w // 2, h // 2))[3] > 250 and 500 <= h <= 640)
        a.click('#toTown'); a.wait_for_timeout(900)
        check('in the town, the monster waits at the gate in 3D', a.evaluate("!!document.querySelector('#twLayer .twfirst .tw3d img') && document.querySelector('#twLayer .twfirst .tw3d img').complete"))
        a.screenshot(path=OUT / 'k5_gate3d.png')
        tap(a, '#twLayer .twplot[data-plot="2"]'); a.wait_for_timeout(3200)
        copies = s.sql('SELECT data FROM snapshots ORDER BY id DESC LIMIT 1')
        check('moving into a house is copied to the store too', json.loads(copies[0]['data'])['town']['houses'] == [{'plot': 2, 'id': a.evaluate('store.monsters[0].id')}])
        tap(a, '#twLayer .twhouse[data-plot="2"]'); a.wait_for_timeout(1400)
        lean = a.evaluate("""(() => { const f = document.querySelector('#twLeaner .tw3d img'); if (!f) return null;
            const r = $('twLeaner').getBoundingClientRect(), box = $('twClose').getBoundingClientRect(); return [r.left >= box.left - 1 && r.right <= box.right + 1, f.complete]; })()""")
        check(f'  and in the close-up, the 3D monster leans out of the window {lean}', lean == [True, True])
        a.screenshot(path=OUT / 'k6_close3d.png')
        a.click('#twBack'); a.wait_for_timeout(300)
        a.click('#tabLib'); a.wait_for_timeout(300)
        check('My monsters says it is kept safe', a.is_visible('#kpLine') and 'Kept safe' in a.text_content('#kpLine') and 'kept safe in your family' in a.text_content('#libNote'))

        # --- a new phone for the same child brings everything back --------------------------------------------------
        bctx, n = phone(b, 344, 760)
        n.goto(F + '/#keep'); n.wait_for_timeout(900)
        n.click('#kpStart'); n.wait_for_selector('#keepPanel .kpfaces img')
        g.click('#clearFaces')
        for f in faces_on(n): g.click(f'#faces [data-face="{f}"]')
        g.check('#kids input[type=radio] >> nth=0'); g.fill('#phoneLabel', 'Test spare'); g.click('#doApprove')
        n.wait_for_function("store.monsters.length === 1 && tw.houses.length === 1", timeout=10000)
        check("a new phone joined to the same child brings back the monsters and houses by itself", n.evaluate("[store.monsters[0].name, tw.houses[0].plot]") == ['Fuzzbert', 2])
        n.wait_for_function("kp.art.has('05-09-24')", timeout=10000)
        check('  and gets the 3D monster from the store, without making it again', len(s.gemini.calls) == 1)
        n.goto(F + '/'); n.wait_for_timeout(1000)
        tap(n, '#twLayer .twhouse[data-plot="2"]'); n.wait_for_timeout(1400)
        check('  where it leans out of its window in 3D on the small screen too', n.evaluate("!!document.querySelector('#twLeaner .tw3d img')"))
        n.screenshot(path=OUT / 'k7_newphone.png')

        # --- the first phone opened again: its 3D monsters come from the phone itself --------------------------------
        a.store_calls.clear()
        a.goto(F + '/'); a.wait_for_timeout(1500)
        check('reopened, the first phone shows its 3D monster straight from the phone (no fetch of it)',
              a.evaluate("!!document.querySelector('#twLayer .twhouse')") and not [x for x in a.store_calls if '/art/' in x])

        # --- removing a phone ---------------------------------------------------------------------------------------
        btn = g.locator('#phones li', has_text='Test spare').locator('[data-remove]')
        btn.click(); btn.click(); g.wait_for_function("document.querySelectorAll('#phones [data-remove]').length === 1")
        make_monster(n, 7, 7, 7, 'Max')
        n.wait_for_timeout(2500)
        n.goto(F + '/#keep'); n.wait_for_timeout(1500)
        check('a removed phone finds out on its next save, and says it is unlinked', 'unlinked this phone' in n.text_content('#keepPanel'))
        check('  its monsters are all still on it', n.evaluate('store.monsters.length') == 2)
        before = s.sql('SELECT COUNT(*) AS n FROM snapshots')[0]['n']
        n.evaluate("persist()"); n.wait_for_timeout(2500)
        check("  and it doesn't save to the store any more", s.sql('SELECT COUNT(*) AS n FROM snapshots')[0]['n'] == before)
        n.screenshot(path=OUT / 'k8_removed.png')

        # --- a copy of the page with no store behind it --------------------------------------------------------------
        ctx3, x = phone(b)
        x.route('**/store/v1/join', lambda r: r.fulfill(status=404, content_type='text/html', body='<p>no</p>'))
        x.goto(F + '/#keep'); x.wait_for_timeout(800); x.click('#kpStart'); x.wait_for_timeout(800)
        check('where there is no store behind the page, Link says so plainly', "can't link" in x.text_content('#keepPanel') and x.is_visible('#kpStart'))
        b.close()

print('all good' if not problems else f'PROBLEMS ({len(problems)}):\n  ' + '\n  '.join(problems))
sys.exit(1 if problems else 0)
