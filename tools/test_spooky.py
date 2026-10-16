"""Play Torch hunt and the Pumpkin face maker at phone, folding-phone and laptop sizes.
    python3 tools/test_spooky.py OUTDIR"""
import http.server, socketserver, sys, threading, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
PORT = 8787
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{PORT}/index.html'
css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:%d/Fredoka.ttf)}"
       "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:%d/Nunito.ttf)}") % (PORT, PORT)
problems = []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

def page_at(b, w, h, touch=True):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=touch, has_touch=touch, accept_downloads=True)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    p = ctx.new_page()
    p.on('console', lambda m: m.type == 'error' and problems.append(f'console error: {m.text}'))
    p.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    return ctx, p

def shine_on_all(p):
    """Move the torch onto each hidden monster in turn, the way a finger would."""
    box = p.locator('#tRoom').bounding_box()
    centres = p.evaluate("tor.hidden.map(m => [m.x, m.y])")
    for (fx, fy) in centres:
        p.mouse.move(box['x'] + fx * box['width'], box['y'] + fy * box['height'], steps=4)
        p.wait_for_timeout(330)
    return len(centres)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    # ---------------------------------------------------------------- phone: games page, torch hunt
    ctx, p = page_at(b, 390, 844)
    p.goto(BASE + '#games'); p.wait_for_timeout(900)
    check('games page has 6 games, the 2 Halloween ones under Spooky', p.eval_on_selector_all('.gametile', 'e => e.length') == 6 and p.is_visible('.spooky-head'))
    p.screenshot(path=OUT / 's1_games.png', full_page=True)
    p.click('#playTorch'); p.wait_for_timeout(1000)
    check('Torch tile opens #torch', p.evaluate('location.hash') == '#torch' and p.is_visible('#tRoom'))
    for lvl, n in ((0, 3), (1, 5), (2, 8)):
        p.click(f'#tLevels .level >> nth={lvl}'); p.wait_for_timeout(1000)   # it scrolls the room into view
        check(f'level {lvl + 1}: {n} monsters hidden, {n} empty slots', p.evaluate('tor.hidden.length') == n and p.eval_on_selector_all('#tTray span:not(.got)', 'e => e.length') == n)
        if lvl == 0:
            # a torch far from everyone finds nobody
            box = p.locator('#tRoom').bounding_box()
            far = p.evaluate("""(() => { let best = null, bd = 0;
              for (let gx = .05; gx < 1; gx += .05) for (let gy = .05; gy < 1; gy += .05) {
                const d = Math.min(...tor.hidden.map(m => Math.hypot((m.x - gx) * 3, (m.y - gy) * 4)));
                if (d > bd) { bd = d; best = [gx, gy]; } } return best; })()""")
            p.mouse.move(box['x'] + far[0] * box['width'], box['y'] + far[1] * box['height'], steps=3); p.wait_for_timeout(600)
            check('a torch pointing away finds nobody', p.evaluate('tor.found') == 0)
            check('the hint goes once the torch moves', p.evaluate("getComputedStyle(document.querySelector('#tRoom .hint')).opacity") == '0')
            p.screenshot(path=OUT / 's2_torch_dark.png', full_page=True)
        found = shine_on_all(p)
        p.wait_for_timeout(300)
        if lvl == 0: p.screenshot(path=OUT / 's3_torch_found.png', full_page=True)
        p.wait_for_timeout(1300)
        check(f'level {lvl + 1}: shining on each finds all {found}, lights on, win shown',
              p.evaluate('tor.found') == found and p.evaluate("document.getElementById('tRoom').classList.contains('lit')") and p.is_visible('#tWin'))
        if lvl == 2: p.screenshot(path=OUT / 's4_torch_lit.png', full_page=True)
    p.click('#tAgain'); p.wait_for_timeout(900)
    check('Play again: dark again, nobody found', not p.evaluate("document.getElementById('tRoom').classList.contains('lit')") and p.evaluate('tor.found') == 0)
    # dragging on the room must not scroll the page
    y0 = p.evaluate('scrollY'); box = p.locator('#tRoom').bounding_box()
    p.touchscreen.tap(box['x'] + 100, box['y'] + 200)
    check('the room is set not to scroll the page when dragged', p.evaluate("getComputedStyle(document.getElementById('tRoom')).touchAction") == 'none')
    p.click('#torchgame [data-go="games"]'); p.wait_for_timeout(200)
    check('leaving stops the torch timer', p.evaluate('tor.timer') is None)

    # ---------------------------------------------------------------- pumpkin
    p.click('#playPumpkin'); p.wait_for_timeout(500)
    check('Pumpkin tile opens #pumpkin', p.evaluate('location.hash') == '#pumpkin' and p.is_visible('#pk'))
    first = p.text_content('#pkRow_eyes small')
    p.click('#pkRow_eyes button >> nth=1'); p.wait_for_timeout(150)
    second = p.text_content('#pkRow_eyes small')
    check(f'next eyes: {first} -> {second}', first != second)
    # tapping the mouth on the pumpkin itself changes the mouth
    m0 = p.text_content('#pkRow_mouth small')
    box = p.locator('#pk').bounding_box()
    p.mouse.click(box['x'] + box['width'] * .5, box['y'] + box['height'] * (285 / 380)); p.wait_for_timeout(150)
    check(f'tapping the mouth: {m0} -> {p.text_content("#pkRow_mouth small")}', p.text_content('#pkRow_mouth small') != m0)
    n0 = p.text_content('#pkRow_nose small')
    p.mouse.click(box['x'] + box['width'] * .5, box['y'] + box['height'] * (222 / 380)); p.wait_for_timeout(150)
    check(f'tapping the nose: {n0} -> {p.text_content("#pkRow_nose small")}', p.text_content('#pkRow_nose small') != n0)
    p.click('#pkShuffle'); p.wait_for_timeout(150)
    p.screenshot(path=OUT / 's5_pumpkin.png', full_page=True)
    p.click('#pkLight'); p.wait_for_timeout(700)
    check('Light it: night background, glowing face', p.evaluate("document.getElementById('pkStage').classList.contains('lit')") and p.eval_on_selector_all('#pk .pkglow', 'e => e.length') == 1)
    check(f'button now says "{p.text_content("#pkLight").strip()}"', p.text_content('#pkLight').strip() == 'Lights on')
    p.screenshot(path=OUT / 's6_pumpkin_lit.png')
    with p.expect_download() as d: p.click('#pkSave')
    d.value.save_as(OUT / 'pumpkin.png'); im = Image.open(OUT / 'pumpkin.png')
    check(f'Save picture: {d.value.suggested_filename} {im.size}', im.size == (1200, 1140) and d.value.suggested_filename.endswith('pumpkin.png'))
    import numpy as np
    PX_CM = 300 / 2.54
    def stencil(name):
        with p.expect_download() as d: p.click('#pkStencil')
        f = OUT / f'stencil_{name}.jpg'; d.value.save_as(f)
        return d.value.suggested_filename, np.asarray(Image.open(f).convert('L'))
    # the widest face (sleepy eyes, fangs) should come out exactly the chosen size across
    p.evaluate("pk.eyes = PK.eyes.findIndex(e => e.name === 'Sleepy'); pk.nose = 0; pk.mouth = PK.mouth.findIndex(m => m.name === 'Fangs'); drawPumpkin()")
    for i, (name, cm) in enumerate((('small', 12), ('medium', 15), ('large', 18))):
        p.click(f'#pkSizes .level >> nth={i}')
        fn, a = stencil(name)
        # the face's width: grey or black between the size line and the 5 cm bar
        # any grey or black column counts, so the sharp tips of the sleepy eyes are included; skip the dashed centre line
        face = a[400:2840]; cols = np.array([c for c in np.where((face < 230).any(axis=0))[0] if abs(c - 1240) > 6])
        width_cm = (cols.max() - cols.min()) / PX_CM
        bar = np.where((a[2862:2878] < 120).all(axis=0))[0]; bar_cm = (bar.max() - bar.min() + 1) / PX_CM
        check(f'stencil {name}: {fn} {a.shape[::-1]}, widest face {width_cm:.1f} cm across (want {cm}), bar {bar_cm:.2f} cm',
              a.shape == (3508, 2480) and abs(width_cm - cm) < .2 and abs(bar_cm - 5) < .03)
    # the narrowest face stays its real size on the pumpkin instead of being blown up
    p.evaluate("pk.eyes = PK.eyes.findIndex(e => e.name === 'One big eye'); pk.nose = PK.nose.findIndex(n => n.name === 'No nose'); pk.mouth = PK.mouth.findIndex(m => m.name === 'Ooh'); drawPumpkin()")
    p.click('#pkSizes .level >> nth=2')
    fn, a = stencil('narrow_large')
    face = a[400:2840]; cols = np.where((face < 230).sum(axis=0) > 40)[0]; rows = np.where(((face < 230).sum(axis=1)) > 12)[0]
    w_cm = (cols.max() - cols.min()) / PX_CM; h_cm = (rows.max() - rows.min()) / PX_CM
    want = p.evaluate("(() => { const L = pkStencilLayout(PK_SIZES[2]); return [L.wcm, L.hcm]; })()")
    check(f'narrow face on Large: {w_cm:.1f} x {h_cm:.1f} cm (it is {want[0]:.1f} x {want[1]:.1f} cm on the pumpkin, scaled)', abs(w_cm - want[0]) < .2 and abs(h_cm - want[1]) < .3 and w_cm < 8)
    # every one of the 144 faces, at every size, sits on the page below the title and above the 5 cm bar
    bad = p.evaluate("""(() => { const bad = []; const keep = {...pk};
      for (let e = 0; e < PK.eyes.length; e++) for (let n = 0; n < PK.nose.length; n++) for (let m = 0; m < PK.mouth.length; m++) {
        pk.eyes = e; pk.nose = n; pk.mouth = m; drawPumpkin();
        for (const S of PK_SIZES) { const L = pkStencilLayout(S);
          if (L.top < 420 || L.bottom > 2820 || L.left < 150 || L.right > 2330 || L.wcm > S.cm + .01) bad.push([PK.eyes[e].name, PK.nose[n].name, PK.mouth[m].name, S.name]); } }
      Object.assign(pk, keep); drawPumpkin(); return bad; })()""")
    check(f'all 144 faces fit the page at all 3 sizes{": " + str(bad[:3]) if bad else ""}', not bad)
    ctx.close()

    # ---------------------------------------------------------------- other sizes
    for (w, h, touch, label) in ((360, 740, True, 'small phone'), (904, 1000, True, 'folding phone open'), (1280, 800, False, 'laptop')):
        ctx, p = page_at(b, w, h, touch)
        for hsh in ('#torch', '#pumpkin', '#games'):
            p.goto(BASE + hsh); p.wait_for_timeout(700)
            check(f'{label} {w}px {hsh}: no sideways scroll', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
            if hsh == '#torch':
                p.wait_for_timeout(600)
                rb = p.locator('#tRoom').bounding_box()
                check(f'{label}: the whole room is on screen after opening (top {rb["y"]:.0f}, bottom {rb["y"] + rb["height"]:.0f} of {h})', rb['y'] >= 0 and rb['y'] + rb['height'] <= h + 1)
        p.goto(BASE + '#torch'); p.wait_for_timeout(1000)
        shine_on_all(p); p.wait_for_timeout(1400)
        check(f'{label}: torch hunt can be finished', p.is_visible('#tWin'))
        p.screenshot(path=OUT / f's7_{w}.png', full_page=True)
        ctx.close()
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
