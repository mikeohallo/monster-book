"""Keeping monsters safe: a phone linked to the family's private store by three faces and a grown-up's passkey, saving
every change, a new phone bringing it all back, an unlinked phone, 3D monsters in the town, and the voices: lines with
a monster's name made by the store and kept on the phone, never played over the phone's own voice. Runs the private store
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
        # the phone's voice and the clips, written down instead of heard (as in test_town.py): __said is every line said,
        # __clips the ones said by a clip, __paused each clip cut off
        ctx.add_init_script("""window.__said = []; window.__clips = []; window.__paused = []; window.__sayGap = 0; let fresh = true;
            Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
              speak: u => { if (fresh || !window.__said.length) window.__said.push(u.text); else window.__said[window.__said.length - 1] += ' ' + u.text;
                            fresh = false; setTimeout(() => u.onend && u.onend({}), 5); },
              cancel() { fresh = true; }, getVoices: () => [], addEventListener() {}, removeEventListener() {} } });
            HTMLMediaElement.prototype.play = function () {
              const a = this, line = a.dataset.line || '';
              return fetch(a.src).then(r => { if (!r.ok) throw new Error('missing');
                window.__said.push(line); window.__clips.push(line); fresh = true; a.dispatchEvent(new Event('playing')); })
                .catch(e => { a.dispatchEvent(new Event('error')); throw e; }); };
            HTMLMediaElement.prototype.pause = function () { if (this.dataset.line) window.__paused.push(this.dataset.line); };""")
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
        check('an unlinked phone makes and saves monsters without ever calling the store', c.store_calls == [] and 'monster-book.keep' not in dbs and 'monster-book.voices' not in dbs)
        c.click('#tabTown'); c.wait_for_timeout(600); tap(c, '#twLayer .twfirst'); c.wait_for_timeout(500)
        check("  its town still talks in the shipped voices, and a line with a name in the phone's own voice",
              'I need a home! Tap a plus to build me a house.' in c.evaluate('window.__clips') and c.store_calls == []
              and any('Gloop' in x for x in c.evaluate('window.__said')) and not any('Gloop' in x for x in c.evaluate('window.__clips')))
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
        t0 = a.evaluate('Date.now()')
        make_monster(a, 5, 9, 24, 'Fuzzbert')
        a.wait_for_function("kp.art.has('05-09-24')", timeout=20000)
        a.wait_for_function(f"kp.me && kp.me.saved > {t0}", timeout=10000)   # the copy goes a moment after the change (the 3D monster can be quicker)
        copies = s.sql('SELECT monsters, data FROM snapshots ORDER BY id DESC LIMIT 1')
        check('saving a monster copies it to the store', copies and copies[0]['monsters'] == 1 and json.loads(copies[0]['data'])['monsters'][0]['name'] == 'Fuzzbert')
        pics = lambda: [c for c in s.gemini.calls if 'gemini-3-pro-image' in c['path']]
        talks = lambda: [c for c in s.gemini.calls if c['path'].startswith('/v1beta/interactions')]
        call = pics()[-1]['body']['contents'][0]['parts'] if pics() else []
        src = Image.open(io.BytesIO(base64.b64decode(call[0]['inlineData']['data']))) if call else None
        check(f'the 3D monster is asked for once, from the book monster drawn on the phone {src.size if src else None}',
              len(pics()) == 1 and src and src.format == 'JPEG' and abs(src.size[1] / src.size[0] - 1485 / 925) < .01)
        art = s.sql("SELECT length(image) AS n FROM art WHERE combo = '05-09-24'")
        check(f'  the phone cut it out and sent it back to the store ({art[0]["n"] if art else 0} bytes)', art and 2000 < art[0]['n'] < 600 * 1024)
        cut = a.evaluate("fetch(kp.art.get('05-09-24').url).then(r => r.arrayBuffer()).then(b => btoa(String.fromCharCode(...new Uint8Array(b))))")
        im = Image.open(io.BytesIO(base64.b64decode(cut))).convert('RGBA')
        w, h = im.size
        corners = [im.getpixel(xy)[3] for xy in ((0, 0), (w - 1, 0), (0, h // 3), (w - 1, h // 3))]
        check(f'  the white is gone from around it, and it is trimmed to the monster ({w}x{h}, corners {corners})', max(corners) < 30 and im.getpixel((w // 2, h // 2))[3] > 250 and 500 <= h <= 640)

        # --- the voices: a monster's own lines are made by the store after it's saved, and kept on the phone ----------
        hi = "Hi! I'm Fuzzbert! I love Worms!"
        a.wait_for_function(f"VO.store.has('monster\\n' + {json.dumps(hi)})", timeout=15000)
        t = [c for c in talks() if 'oh! I love Worms!' in c['body']['input'][0]['content'][0]['text']]
        check(f"after the save, the monster's hello is made in the monsters' voice, its name respelled {[c['body']['input'][0]['content'][0]['text'] for c in t]}",
              len(t) == 1 and t[0]['body']['generation_config'] == {'speech_config': [{'voice': 'voice_1iki1zg5qzyg'}]} and t[0]['body']['input'][0]['content'][0]['text'] == "Hi! I'm fuzzbert-oh! I love Worms!")
        kept = a.evaluate("indexedDB.databases().then(d => d.map(x => x.name))")
        check('  and kept on the phone, in its own database', 'monster-book.voices' in kept)
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
        check(f'  where it says hello with its clip, not the phone voice {a.evaluate("window.__said.slice(-2)")}', a.evaluate('window.__clips.at(-1)') == hi and a.evaluate('window.__said.at(-1)') == hi)
        # a line with no clip yet: the phone's voice says it, and the clip made meanwhile is only kept for next time
        s.gemini.delay = 2.5
        n_t = len(talks())
        a.evaluate("window.__said.length = 0; window.__clips.length = 0")
        a.click('#twMove'); a.wait_for_timeout(300)
        line = a.evaluate('window.__said.at(-1)')
        check(f'a new line with a name in it is said by the phone at once ({line})', line and line.startswith('Fuzzbert wants to move!') and a.evaluate('window.__clips.length') == 0)
        a.wait_for_function(f"VO.store.has('narrator\\n' + {json.dumps(line)})", timeout=15000)
        a.wait_for_timeout(300)
        check("  the store makes it meanwhile, and it isn't played over or after the phone's voice", len(talks()) == n_t + 1 and a.evaluate('window.__clips.length') == 0
              and talks()[-1]['body']['generation_config'] == {'speech_config': [{'voice': 'en-us-hali'}]})
        s.gemini.delay = 0.2
        a.evaluate("twStayHome()"); a.wait_for_timeout(300)
        a.evaluate("twCloseUp(2)"); a.wait_for_timeout(400)
        a.click('#twMove'); a.wait_for_timeout(400)
        moves = [c for c in talks() if 'wants to move' in c['body']['input'][0]['content'][0]['text']]
        check('  the next time, the line is its clip (made once)', a.evaluate('window.__clips.at(-1)') == line and len(moves) == 1)
        # a new line cuts off the last; mute stops it
        a.evaluate("window.__paused.length = 0"); a.evaluate("twStayHome()"); a.wait_for_timeout(300)
        check(f'  a new line cuts off the clip before it {a.evaluate("window.__paused")}', line in a.evaluate('window.__paused'))
        a.evaluate("window.__said.length = 0; window.__paused.length = 0")
        a.evaluate(f"say({json.dumps(hi)}, 'monster')"); a.wait_for_timeout(200)
        a.eval_on_selector('.mute', 'e => e.click()')
        a.wait_for_timeout(200)
        muted = a.evaluate('!sound.on')
        a.evaluate(f"say({json.dumps(hi)}, 'monster')"); a.wait_for_timeout(300)
        check(f'  mute stops the clip, and nothing more is said ({a.evaluate("window.__said")})', muted and hi in a.evaluate('window.__paused') and a.evaluate('window.__said') == [hi])
        a.eval_on_selector('.mute', 'e => e.click()'); a.wait_for_timeout(200)
        # the store out of reach: the phone's voice, and no errors
        a.route('**/store/v1/voice', lambda r: r.abort())
        a.evaluate("window.__said.length = 0; window.__clips.length = 0")
        a.evaluate("say('Fuzzbert is out of reach!')"); a.wait_for_timeout(500)
        check("with the store out of reach, a new line is the phone's voice", a.evaluate('window.__said') == ['Fuzzbert is out of reach!'] and a.evaluate('window.__clips') == [])
        a.unroute('**/store/v1/voice')
        a.evaluate("tw.moving = null; renderTown(); twCloseUp(2)"); a.wait_for_timeout(400)
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
        check('  and gets the 3D monster from the store, without making it again', len(pics()) == 1)
        n.goto(F + '/'); n.wait_for_timeout(1000)
        tap(n, '#twLayer .twhouse[data-plot="2"]'); n.wait_for_timeout(1400)
        check('  where it leans out of its window in 3D on the small screen too', n.evaluate("!!document.querySelector('#twLeaner .tw3d img')"))
        n.screenshot(path=OUT / 'k7_newphone.png')

        # --- the first phone opened again: its 3D monsters come from the phone itself --------------------------------
        a.store_calls.clear()
        a.goto(F + '/'); a.wait_for_timeout(1500)
        check('reopened, the first phone shows its 3D monster straight from the phone (no fetch of it)',
              a.evaluate("!!document.querySelector('#twLayer .twhouse')") and not [x for x in a.store_calls if '/art/' in x])
        a.wait_for_function("VO.store.size > 0", timeout=5000)
        check('  and its kept clips too, ready at once', a.evaluate(f"VO.store.has('monster\\n' + {json.dumps(hi)})"))

        # --- a grown-up changes how a name is said: the phones drop their old clips with it -----------------------------
        g.reload(); g.wait_for_selector('#signedin:not([hidden])')
        g.wait_for_function("document.querySelectorAll('#names input').length === 1")
        check('the Names list on the grown-up page has the monster, as Gemini spelled it', g.locator('#names b').first.text_content() == 'Fuzzbert' and g.locator('#names input').first.input_value() == 'fuzzbert-oh')
        g.fill('#names input', 'FUZZ-burt'); g.click('#names [data-save]')
        g.wait_for_function("document.getElementById('namesMsg').textContent.startsWith('Saved')")
        a.goto(F + '/'); a.wait_for_timeout(1500)
        a.wait_for_function(f"VO.store.has('monster\\n' + {json.dumps(hi)})", timeout=15000)
        t = [c for c in talks() if 'I love Worms!' in c['body']['input'][0]['content'][0]['text']]
        check(f"reopened, the phone drops its clips with the old spelling and gets them made again {[c['body']['input'][0]['content'][0]['text'] for c in t]}",
              len(t) == 2 and t[-1]['body']['input'][0]['content'][0]['text'] == "Hi! I'm FUZZ-burt! I love Worms!")

        # --- rolling back: the page live before the voices still works on this store and this phone ------------------
        if (SITE / 'index_v33.html').exists():
            a.goto(F + '/index_v33.html'); a.wait_for_timeout(1500)
            ok_old = a.evaluate("typeof VO === 'undefined' && store.monsters.length === 1 && kpLinked()")
            before = s.sql('SELECT COUNT(*) AS n FROM snapshots')[0]['n']
            make_monster(a, 3, 3, 3, 'Rolly'); a.wait_for_timeout(2500)
            check('the page live before the voices (v33) opens on the same phone, linked, and still saves to the store', ok_old and s.sql('SELECT COUNT(*) AS n FROM snapshots')[0]['n'] > before)
            a.goto(F + '/'); a.wait_for_timeout(1500)
            check('  and back on this page, the kept clips are still there', a.evaluate(f"VO.store.has('monster\\n' + {json.dumps(hi)})") and a.evaluate('store.monsters.length') == 2)
        else:
            check('rollback test: index_v33.html (the page live before the voices) is beside index.html', False)

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
