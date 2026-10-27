"""Play Torch hunt (the bedroom and the witch's cottage) and the Pumpkin face maker, and print monster masks,
at phone, folding-phone and laptop sizes.
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
PX_CM = 300 / 2.54; PX_MM = PX_CM / 10
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

def find_all(p):
    """Shine on every hidden monster in turn, the way a finger would: when one is off screen in the witch's cottage,
    hold the torch at that edge until the room has slid along far enough, then move onto it."""
    box = p.locator('#tRoom').bounding_box()
    W = p.evaluate('tRoomDef().w') / 360          # the room's width in screens
    n = p.evaluate('tor.hidden.length')
    for i in range(n):
        if p.evaluate(f'tor.hidden[{i}].found'): continue
        mx, my = p.evaluate(f'[tor.hidden[{i}].x, tor.hidden[{i}].y]')
        for _ in range(60):
            cam = p.evaluate('tor.cam'); sx = mx * W - cam * (W - 1)    # where it is on screen, 0-1 across the room
            if .2 <= sx <= .8 or (sx < .2 and cam <= 0) or (sx > .8 and cam >= 1): break
            p.mouse.move(box['x'] + (.97 if sx > .8 else .03) * box['width'], box['y'] + .5 * box['height'])
            p.wait_for_timeout(150)
        cam = p.evaluate('tor.cam'); sx = mx * W - cam * (W - 1)
        p.mouse.move(box['x'] + sx * box['width'], box['y'] + my * box['height'], steps=4)
        p.wait_for_timeout(340)
    return n

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
    check('games page has 6 games, the 3 Halloween ones under Spooky', p.eval_on_selector_all('.gametile', 'e => e.length') == 6 and p.is_visible('.spooky-head') and p.is_visible('#playMask'))
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

    # ---------------------------------------------------------------- monster masks
    ctx, p = page_at(b, 390, 844)
    p.goto(BASE + '#games'); p.wait_for_timeout(500)
    p.click('#playMask'); p.wait_for_timeout(1200)
    check('Monster masks opens #masks with 30 monsters and 2 sizes', p.evaluate('location.hash') == '#masks' and p.eval_on_selector_all('#mkPick button', 'e => e.length') == 30
          and p.eval_on_selector_all('#mkSizes .level', 'e => e.length') == 2)
    inked = p.evaluate("(() => { const c = $('mkPrev'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 0; i < d.length; i += 16) if (d[i] < 200) n++; return n; })()")
    check(f'the preview shows the mask ({inked} inked samples)', inked > 2000)
    p.click('#mkPick button >> nth=0'); p.wait_for_timeout(700)
    check('picking a monster changes the preview', p.evaluate('MK.n') == 1)
    # the printed sheet: A4 at 300 ppi, the 5 cm bar, and the eye holes cut out white, 5 cm apart
    for (size, nth, eyes) in (('kid', 0, 5.0), ('big', 1, 6.3)):
        p.click(f'#mkSizes .level >> nth={nth}'); p.wait_for_timeout(400)
        with p.expect_download() as d: p.click('#mkPrint')
        fn = d.value.suggested_filename; path = OUT / fn; d.value.save_as(path)
        a = np.asarray(Image.open(path).convert('L')).astype(int)
        bar = np.where((a[int(268 * PX_MM) + 3:int(268 * PX_MM) + 18] < 120).all(axis=0))[0]; bar_cm = (bar.max() - bar.min() + 1) / PX_CM
        L = p.evaluate(f"(async () => ({{ holes: maskLayout(await maskArt(MK.n), MASK_SIZES['{size}']).holes }}))()")
        hx = [round(h['x'] * PX_MM) for h in L['holes']]; hy = round(L['holes'][0]['y'] * PX_MM); r = L['holes'][0]['r'] * PX_MM
        white = all(a[hy - int(r * .6):hy + int(r * .6), x - int(r * .6):x + int(r * .6)].min() > 235 for x in hx)
        check(f'mask {size}: {fn} {a.shape[::-1]}, bar {bar_cm:.2f} cm, eye holes {(hx[1] - hx[0]) / PX_CM:.2f} cm apart and white inside',
              a.shape == (3508, 2480) and abs(bar_cm - 5) < .03 and abs((hx[1] - hx[0]) / PX_CM - eyes) < .02 and white and fn.startswith('monster-mask-'))
    # every monster at both sizes: the art fits the page, the eye holes sit on the monster, the elastic dots are inside the cut line
    bad = p.evaluate('''(async () => { const bad = [];
      for (let n = 1; n <= 30; n++) { const info = await maskArt(n);
        for (const key of Object.keys(MASK_SIZES)) { const S = MASK_SIZES[key], L = maskLayout(info, S);
          const cxP = L.X(info.cx), onArt = (x, y) => info.on(Math.round(info.cx + (x - cxP) / L.k), Math.round(info.t + (y - MASK_TOP) / L.k));
          const why = [];
          if (L.art.l < MASK_SIDE - .01 || L.art.r > 210 - MASK_SIDE + .01 || L.art.t < MASK_TOP - .01 || L.art.b > 262) why.push('off the page');
          for (const h of L.holes) if (!onArt(h.x, h.y) || !onArt(h.x - h.r, h.y) || !onArt(h.x + h.r, h.y)) why.push('hole off the monster');
          for (const d of L.dots) { if (!onArt(d.x, d.y)) why.push('dot off the monster');
            if (L.holes.some(h => Math.hypot(h.x - d.x, h.y - d.y) < h.r + d.r + 4)) why.push('dot too near a hole'); }
          if (why.length) bad.push(mon(n).name + ' ' + key + ': ' + why.join(', ')); } }
      return bad; })()''')
    check(f'all 30 masks at both sizes: on the page, eye holes on the monster, elastic dots inside the cut line{": " + str(bad[:4]) if bad else ""}', not bad)
    p.screenshot(path=OUT / 's8_masks.png', full_page=True)
    ctx.close()


    # ---------------------------------------------------------------- the witch's cottage (phone)
    ctx, p = page_at(b, 390, 844)
    p.goto(BASE + '#torch'); p.wait_for_timeout(1000)
    check('two rooms to pick, the bedroom first time', p.eval_on_selector_all('#tRooms .level', 'e => e.map(x => x.textContent)') == ['BedroomSmall and cosy', "Witch's cottageBig and spooky"]
          and p.get_attribute('#tRooms .level >> nth=0', 'aria-pressed') == 'true')
    check('four levels; the bedroom has 3, 5, 8 and 10 monsters', p.eval_on_selector_all('#tLevels .level small', 'e => e.map(x => x.textContent)') == ['3 monsters', '5 monsters', '8 monsters', '10 monsters'])
    lv = p.eval_on_selector_all('#tLevels .level', 'e => e.map(x => { const r = x.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })')
    check(f'on a phone the four levels are two by two, each at least 2 cm wide ({lv})', all(w >= 76 for w, h in lv) and len({h for w, h in lv}) == 1)
    # the bedroom's new top level
    p.click('#tLevels .level >> nth=3'); p.wait_for_timeout(900)
    check('bedroom Tiny torch: 10 monsters, a smaller torch, 3 faces to find first', p.evaluate('tor.hidden.length') == 10 and p.evaluate('TLEVELS[3].r') < p.evaluate('TLEVELS[2].r')
          and p.eval_on_selector_all('#tTray span.want', 'e => e.length') == 3)
    find_all(p); p.wait_for_timeout(1400)
    check('bedroom Tiny torch can be finished', p.is_visible('#tWin') and p.evaluate('tor.found') == 10)
    # into the cottage
    p.click('#tRooms .level >> nth=1'); p.click('#tLevels .level >> nth=0'); p.wait_for_timeout(1000)
    check("the cottage: 4, 7, 10 and 12 monsters; the words say it's the witch's cottage",
          p.eval_on_selector_all('#tLevels .level small', 'e => e.map(x => x.textContent)') == ['4 monsters', '7 monsters', '10 monsters', '12 monsters']
          and "witch's cottage" in p.text_content('#tLede') and p.get_attribute('#tBg', 'viewBox') == '0 0 720 480')
    view = p.evaluate("(() => { const r = $('tRoom').getBoundingClientRect(), w = $('tWorld').getBoundingClientRect(); return [r.width, w.width, w.left - r.left]; })()")
    check(f'the cottage is twice as wide as the room on screen ({view[1]:.0f} of {view[0]:.0f} px) and starts at the left', abs(view[1] - 2 * view[0]) < 1 and abs(view[2]) < 1)
    check('an arrow on the right says there is more room that way, none on the left', p.evaluate("$('tPanR').classList.contains('on') && !$('tPanL').classList.contains('on')"))
    p.screenshot(path=OUT / 'c1_cottage_dark.png', full_page=True)
    # hold the torch at the right edge: the room slides all the way, then stops
    box = p.locator('#tRoom').bounding_box()
    p.mouse.move(box['x'] + box['width'] * .5, box['y'] + box['height'] * .1, steps=3)
    p.mouse.move(box['x'] + box['width'] * .97, box['y'] + box['height'] * .1, steps=3); p.wait_for_timeout(700)
    mid = p.evaluate('tor.cam')
    p.wait_for_timeout(2500)
    view = p.evaluate("(() => { const r = $('tRoom').getBoundingClientRect(), w = $('tWorld').getBoundingClientRect(); return [w.right - r.right, tor.cam]; })()")
    check(f'at the right edge the room slides along (part way after 0.7 s: {mid:.2f}) to its far end (cam {view[1]:.2f}, edges {view[0]:.1f} px apart)', 0 < mid < 1 and view[1] == 1 and abs(view[0]) < 1)
    check('then the arrow points back left, not right', p.evaluate("$('tPanL').classList.contains('on') && !$('tPanR').classList.contains('on')"))
    p.mouse.move(box['x'] + box['width'] * .5, box['y'] + box['height'] * .1, steps=3); p.wait_for_timeout(200)
    c0 = p.evaluate('tor.cam'); p.mouse.move(box['x'] + box['width'] * .03, box['y'] + box['height'] * .1, steps=2); p.wait_for_timeout(400)
    c1 = p.evaluate('tor.cam'); p.mouse.move(box['x'] + box['width'] * .5, box['y'] + box['height'] * .1, steps=2); p.wait_for_timeout(500)
    check(f'in the middle it stays put; at the left edge it slides back; back in the middle it stops ({c0:.2f}, {c1:.2f}, {p.evaluate("tor.cam"):.2f})', c0 == 1 and c1 < 1 and abs(p.evaluate('tor.cam') - c1) < .03)
    # a finger: it slides while the finger is down at the edge and stops when it lifts
    p.evaluate("""(() => { const r = $('tRoom').getBoundingClientRect(), o = { bubbles: true, pointerType: 'touch', pointerId: 7, clientX: r.left + r.width * .97, clientY: r.top + r.height * .2 };
      $('tRoom').dispatchEvent(new PointerEvent('pointermove', o)); })()""")
    p.wait_for_timeout(500); t1 = p.evaluate('tor.cam')
    p.evaluate("$('tRoom').dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerType: 'touch', pointerId: 7 }))")
    p.wait_for_timeout(100); t2 = p.evaluate('tor.cam'); p.wait_for_timeout(600); t3 = p.evaluate('tor.cam')
    check(f'a finger held at the edge slides the room ({c1:.2f} -> {t1:.2f}) and lifting it stops it ({t2:.2f} = {t3:.2f})', t1 > c1 and abs(t3 - t2) < .001)
    # every level, finding them all by sliding along
    for lvl, n in ((0, 4), (1, 7), (2, 10), (3, 12)):
        p.click(f'#tLevels .level >> nth={lvl}'); p.wait_for_timeout(900)
        want = p.eval_on_selector_all('#tTray span.want', 'e => e.length')
        check(f'cottage level {lvl + 1}: {n} monsters hidden, {want} faces to find first', p.evaluate('tor.hidden.length') == n and want == (3 if lvl >= 2 else 0)
              and p.eval_on_selector_all('#tTray span:not(.got)', 'e => e.length') == n)
        if lvl == 3:
            deep = p.evaluate('tor.hidden.filter(m => m.deep).length')
            check(f'Tiny torch: some hide deeper, so only part of them shows ({deep} of 12)', 3 <= deep <= 6)
        if lvl == 2:
            # the third face to find fills its own slot, not the first
            box = p.locator('#tRoom').bounding_box(); W = 2
            mx, my = p.evaluate('[tor.hidden[2].x, tor.hidden[2].y]')
            p.evaluate(f"tor.cam = Math.min(1, Math.max(0, ({mx} * 2 - .5))); drawTorch()")
            cam = p.evaluate('tor.cam'); sx = mx * W - cam
            p.mouse.move(box['x'] + sx * box['width'], box['y'] + my * box['height'], steps=4); p.wait_for_timeout(500)
            cls = p.eval_on_selector_all('#tTray span', 'e => e.slice(0, 3).map(x => x.className)')
            check(f'finding the third face fills the third slot ({cls})', cls[2] == 'got' and cls[0] == 'want' and cls[1] == 'want')
            # the giggle hint: near a monster it giggles, far from all of them it doesn't
            p.evaluate("window.__peeps = []; const o = sound.peep.bind(sound); sound.peep = v => { window.__peeps.push(v); o(v); }")
            m = p.evaluate("(() => { const i = tor.hidden.findIndex(m => !m.found); return [tor.hidden[i].x, tor.hidden[i].y]; })()")
            p.evaluate(f"tor.cam = Math.min(1, Math.max(0, ({m[0]} * 2 - .5))); drawTorch()")
            cam = p.evaluate('tor.cam'); sx = m[0] * 2 - cam; R = p.evaluate('TLEVELS[2].r')
            p.mouse.move(box['x'] + (sx + R * 1.2 * (1 if sx < .5 else -1)) * box['width'], box['y'] + m[1] * box['height'], steps=3); p.wait_for_timeout(1600)
            peeps = p.evaluate('window.__peeps.length')
            check(f'Hard: with the torch close to a monster, it giggles ({peeps} times in 1.6 s)', peeps >= 1)
        find_all(p); p.wait_for_timeout(1400)
        check(f"cottage level {lvl + 1}: found all {n}, lights on, and it says the witch's cottage",
              p.evaluate('tor.found') == n and p.is_visible('#tWin') and "witch's cottage" in p.text_content('#tWinText'))
        if lvl == 3: p.screenshot(path=OUT / 'c2_cottage_lit.png', full_page=True)
    # Easy never giggles: it's only a help on the harder levels
    p.click('#tLevels .level >> nth=0'); p.wait_for_timeout(700)
    p.evaluate("window.__peeps = []")
    box = p.locator('#tRoom').bounding_box()
    for k in range(12): p.mouse.move(box['x'] + box['width'] * (.25 + .04 * k), box['y'] + box['height'] * (.3 + .03 * k)); p.wait_for_timeout(100)
    check('Easy: no giggle hints', p.evaluate('window.__peeps.length') == 0)
    # the room is remembered, and #cottage goes straight there
    p.goto(BASE + '#torch'); p.wait_for_timeout(900)
    check('the cottage is remembered next time', p.get_attribute('#tRooms .level >> nth=1', 'aria-pressed') == 'true' and p.get_attribute('#tBg', 'viewBox') == '0 0 720 480')
    p.click('#tRooms .level >> nth=0'); p.wait_for_timeout(500)
    p.goto(BASE + '#games'); p.wait_for_timeout(300); p.goto(BASE + '#cottage'); p.wait_for_timeout(900)
    check('#cottage opens Torch hunt in the witch\'s cottage', p.is_visible('#tRoom') and p.get_attribute('#tRooms .level >> nth=1', 'aria-pressed') == 'true')
    # hiding spots: all inside their room, no two overlapping, and the same with the Tiny torch places
    bad = p.evaluate("""(() => { const bad = [];
      for (const [id, R] of Object.entries(ROOMS)) for (const deep of [false, true]) {
        const box = R.spots.map(sp => { const x = sp.x + (deep && sp.d ? sp.d[0] : 0), y = sp.y + (deep && sp.d ? sp.d[1] : 0); return [x - sp.s / 2, y - sp.s / 2, x + sp.s / 2, y + sp.s / 2]; });
        box.forEach((a, i) => { if (a[0] < 0 || a[1] < 0 || a[2] > R.w || a[3] > 480) bad.push(`${id} spot ${i} outside`);
          box.forEach((c, j) => { if (j > i && a[0] < c[2] && c[0] < a[2] && a[1] < c[3] && c[1] < a[3]) bad.push(`${id} spots ${i} and ${j} overlap${deep ? ' (deep)' : ''}`); }); }); }
      return bad; })()""")
    check(f'every hiding spot is inside its room and no two overlap{": " + str(bad) if bad else ""}', not bad)
    ctx.close()

    # ---------------------------------------------------------------- other sizes
    for (w, h, touch, label) in ((360, 740, True, 'small phone'), (904, 1000, True, 'folding phone open'), (1280, 800, False, 'laptop')):
        ctx, p = page_at(b, w, h, touch)
        for hsh in ('#torch', '#pumpkin', '#masks', '#games'):
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
        p.goto(BASE + '#games'); p.wait_for_timeout(300); p.goto(BASE + '#cottage'); p.wait_for_timeout(1300)
        rb = p.locator('#tRoom').bounding_box()
        check(f"{label}: the witch's cottage is all on screen after opening (top {rb['y']:.0f}, bottom {rb['y'] + rb['height']:.0f} of {h})", rb['y'] >= 0 and rb['y'] + rb['height'] <= h + 1)
        p.click(f'#tLevels .level >> nth={3 if w == 360 else 1}'); p.wait_for_timeout(900)
        n = find_all(p); p.wait_for_timeout(1400)
        check(f"{label}: the witch's cottage can be finished ({n} monsters, {'Tiny torch' if w == 360 else 'Medium'})", p.is_visible('#tWin') and p.evaluate('tor.found') == n)
        check(f'{label}: still no sideways scroll in the cottage', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
        p.screenshot(path=OUT / f'c3_{w}.png', full_page=True)
        ctx.close()
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
