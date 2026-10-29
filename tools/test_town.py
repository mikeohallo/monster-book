"""The monster town (the Monster Lab's first screen) and the picture answers on Meet your monster, in Chromium at the
sizes of a folding phone's inner and outer screens, an ordinary phone and a laptop.
    python3 tools/test_town.py OUTDIR"""
import http.server, socketserver, sys, threading, functools, json
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
PORT = 8789
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{PORT}/index.html'
css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:%d/Fredoka.ttf)}"
       "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:%d/Nunito.ttf)}") % (PORT, PORT)

problems = []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

SIZES = {'fold inner': (673, 760), 'fold inner, turned': (841, 600), 'fold outer': (344, 760), 'phone': (390, 740), 'laptop': (1280, 800)}
def new_page(b, size='fold inner', mobile=True):
    w, h = SIZES[size]
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=mobile, has_touch=mobile)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    for site in ('learn', 'seek'):
        ctx.route(f'https://{site}.mikeohalloran.au/**', lambda r, site=site: r.fulfill(status=200, content_type='text/html', body=f'<p>{site}</p>'))
    # the phone's voice, written down instead of spoken: window.__said is every line the page asked it to say
    ctx.add_init_script("""window.__said = [];
        Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { speak: u => window.__said.push(u.text),
          cancel() {}, getVoices: () => [], addEventListener() {}, removeEventListener() {} } });""")
    p = ctx.new_page()
    p.on('console', lambda m: m.type == 'error' and problems.append(f'console error: {m.text}'))
    p.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    return ctx, p

def mon(i, h, b, l, name):
    return dict(id=f'm{i}', created=f'2026-10-{10 + i:02d}T09:00:00Z', h=h, b=b, l=l, name=name, food='', friend='', grumpy='')
MONS = [mon(0, 1, 2, 3, 'Fuzzbert'), mon(1, 5, 5, 5, 'Gloop'), mon(2, 24, 9, 13, 'Wigglebum'), mon(3, 10, 18, 26, ''), mon(4, 17, 3, 30, 'Sprout')]
def seed(p, monsters, houses=None):
    p.evaluate("([m, h]) => { localStorage.clear(); localStorage.setItem('monster-book.v1', JSON.stringify({owner: 'Sam', monsters: m}));"
               " if (h) localStorage.setItem('monster-book.town', JSON.stringify({v: 1, houses: h})); }", [monsters, houses])
    p.reload(); p.wait_for_timeout(900)
saved_town = lambda p: json.loads(p.evaluate("localStorage.getItem('monster-book.town') || '{}'")).get('houses', [])
def tap(p, sel):   # the town's buttons: tap the element itself (things in front can overlap the edges of a plot)
    p.eval_on_selector(sel, 'e => e.click()')
def tap_plot(p, i): tap(p, f'#twLayer .twplot[data-plot="{i}"]')
def tap_house(p, i): tap(p, f'#twLayer .twhouse[data-plot="{i}"]')
N_PLOTS = 22

with sync_playwright() as pw:
    b = pw.chromium.launch()

    # --- the first screen ---------------------------------------------------------------------------------------
    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); p.evaluate('localStorage.clear()'); p.reload(); p.wait_for_timeout(1200)
    check('the plain link opens on the town', p.is_visible('#town') and not p.is_visible('#games') and p.evaluate("document.body.classList.contains('townmode')"))
    check('  the Town tab is selected, and the address has no hash', p.get_attribute('#tabTown', 'aria-selected') == 'true' and p.evaluate('location.hash') == '')
    check('  the painted valley has loaded', p.evaluate("$('twValley').complete && $('twValley').naturalWidth > 0"))
    check('  an empty town says welcome, with a "Make a monster to move in!" bubble',
          'Welcome' in p.text_content('#townHint') and 'Make a monster' in p.text_content('#twLayer .twbubble') and p.is_visible('#twLayer .twsoon'))
    check(f'  {N_PLOTS} empty plots, none of them asking to be built on yet',
          p.eval_on_selector_all('#twLayer .twplot', 'e => e.length') == N_PLOTS and p.eval_on_selector_all('#twLayer .twplot.ready', 'e => e.length') == 0)
    p.screenshot(path=OUT / 't1_empty.png')
    p.click('#twLayer .twsoon'); p.wait_for_timeout(400)
    check('  tapping the "?" at the gate goes to Make', p.is_visible('#make') and p.evaluate('location.hash') == '#make')
    p.click('#tabTown'); p.wait_for_timeout(400)
    check('  the Town tab comes back to the town', p.is_visible('#town') and p.get_attribute('#tabTown', 'aria-selected') == 'true')
    p.click('#tabGames'); p.wait_for_timeout(400)
    check('the Play tab opens the games page at #games', p.is_visible('#games') and p.evaluate('location.hash') == '#games'
          and not p.evaluate("document.body.classList.contains('townmode')"))
    p.goto(BASE + '?for=Sam#games'); p.wait_for_timeout(700)
    check('  #games opens the games page', p.is_visible('#games') and p.get_attribute('#tabGames', 'aria-selected') == 'true')
    p.goto(BASE + '?for=Sam#town'); p.wait_for_timeout(900)
    check('  #town opens the town', p.is_visible('#town'))
    # the signposts: four arms, each a real tap target in view
    hits = p.evaluate("""[...document.querySelectorAll('#twLayer .twarm')].map(a => { const r = a.getBoundingClientRect(), e = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                          return [a.dataset.sign, !!e && a.contains(e), Math.round(r.height)]; })""")
    check(f'signpost: four arms in view and tappable ({hits})', [h[0] for h in hits] == ['games', 'make', 'learn', 'seek'] and all(h[1] and h[2] >= 18 for h in hits))
    p.click('#twLayer .twarm[data-sign="games"]'); p.wait_for_timeout(400)
    check('signpost: Games opens the games page', p.is_visible('#games'))
    p.click('#tabTown'); p.wait_for_timeout(300); p.click('#twLayer .twarm[data-sign="make"]'); p.wait_for_timeout(400)
    check('signpost: Make opens Make a monster', p.is_visible('#make'))
    p.click('#tabTown'); p.wait_for_timeout(300); p.click('#twLayer .twarm[data-sign="learn"]'); p.wait_for_url('https://learn.mikeohalloran.au/**', timeout=8000)
    check(f'signpost: Learn goes to the Learning Lab ({p.url})', p.url == 'https://learn.mikeohalloran.au/?for=Sam')
    p.goto(BASE + '?for=Sam'); p.wait_for_timeout(900); p.click('#twLayer .twarm[data-sign="seek"]'); p.wait_for_url('https://seek.mikeohalloran.au/**', timeout=8000)
    check(f'signpost: Seek goes to Seek ({p.url})', p.url == 'https://seek.mikeohalloran.au/?for=Sam')
    ctx.close()

    # --- moving in --------------------------------------------------------------------------------------------------
    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); seed(p, MONS[:3])
    check('three monsters made: the first waits at the gate, asking for a home',
          p.get_attribute('#twLayer .twfirst', 'aria-label') == 'Fuzzbert needs a home!' and 'Fuzzbert' in p.text_content('#twLayer .twbubble'))
    check(f'  the other two wait behind, and all {N_PLOTS} plots are ready', p.eval_on_selector_all('#twLayer .twwait', 'e => e.length') == 2
          and p.eval_on_selector_all('#twLayer .twplot.ready', 'e => e.length') == N_PLOTS and p.text_content('#townHint') == 'Tap a plot to build a house!')
    # every plot's plus can really be tapped, once it's scrolled into view (nothing sits on top of it)
    blocked = p.evaluate("""(() => { const out = [];
        for (const pl of document.querySelectorAll('#twLayer .twplot')) {
          pl.scrollIntoView({block: 'nearest', inline: 'center'});
          const r = pl.querySelector('.twplus').getBoundingClientRect(), e = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
          if (!e || !pl.contains(e)) out.push(pl.dataset.plot); }
        $('townBox').scrollLeft = 0; return out; })()""")
    check(f'  every plot\'s plus is on top and tappable (blocked: {blocked})', blocked == [])
    p.screenshot(path=OUT / 't2_waiting.png')
    tap_plot(p, 0); p.wait_for_timeout(100)
    check('tap a plot: the house is saved straight away, before the monster gets there', saved_town(p) == [{'plot': 0, 'id': 'm0'}] and p.evaluate('tw.busy'))
    check('  a cottage in its colour stands there with a name sign, and Gloop is next in the queue',
          p.get_attribute('#twLayer .twhouse[data-plot="0"]', 'aria-label') == "Fuzzbert's house"
          and p.get_attribute('#twLayer .twhouse[data-plot="0"] img', 'src') == 'town/cottage-purple.webp'
          and p.text_content('#twLayer .twhouse[data-plot="0"] .twname') == 'Fuzzbert' and 'Gloop' in p.text_content('#twLayer .twbubble'))
    p.wait_for_timeout(500); p.screenshot(path=OUT / 't3_moving.png')
    check('  the monster hops over from the gate', p.eval_on_selector_all('#twLayer .twwalker', 'e => e.length') == 1)
    tap_plot(p, 1); p.wait_for_timeout(100)
    check('  tapping another plot mid-move does nothing', len(saved_town(p)) == 1)
    p.wait_for_timeout(2600)
    check('once inside: the move is done', not p.evaluate('tw.busy') and p.eval_on_selector_all('.twwalker', 'e => e.length') == 0
          and 'Fuzzbert has a new home' in p.text_content('#townHint'))
    tap_house(p, 0); p.wait_for_timeout(1300)
    check('tapping the house opens its close-up: the front lane, a purple roof, Fuzzbert at the window',
          p.is_visible('#twClose') and not p.is_visible('#townBox') and p.get_attribute('#twClose .twclosepic', 'src') == 'town/close-lane-purple.webp'
          and p.evaluate("$('twLeaner').classList.contains('waving')") and p.text_content('#twClose .twcloseName') == "Fuzzbert's house"
          and p.evaluate("$('twClose .twclosepic') === null || document.querySelector('#twClose .twclosepic').complete"))
    win = p.evaluate("""(() => { const pic = document.querySelector('#twClose .twclosepic').getBoundingClientRect(), f = $('twLeaner').getBoundingClientRect(), box = $('twClose').getBoundingClientRect();
        return {inBox: pic.left <= box.left + 1 && pic.right >= box.right - 1 && pic.top <= box.top + 1 && pic.bottom >= box.bottom - 1,
                figInBox: f.left >= box.left && f.right <= box.right}; })()""")
    check(f'  the picture covers the box and the monster is in view ({win})', win['inBox'] and win['figInBox'])
    p.screenshot(path=OUT / 't4_close.png')
    p.click('#twLeaner'); p.wait_for_timeout(300)
    check('  tapping the monster makes it wave again', p.evaluate("$('twLeaner').classList.contains('waving')"))
    p.set_viewport_size({'width': 841, 'height': 600}); p.wait_for_timeout(600)
    check('  turning the phone keeps the close-up open, laid out again', p.is_visible('#twClose') and p.evaluate('tw.open') == 0)
    p.set_viewport_size({'width': 673, 'height': 760}); p.wait_for_timeout(600)
    p.click('#twBack'); p.wait_for_timeout(500)
    check('  "Town" goes back to the valley', p.is_visible('#townBox') and not p.is_visible('#twClose'))
    # folding the phone shut halfway through a move
    tap_plot(p, 1); p.wait_for_timeout(500)
    p.set_viewport_size({'width': 344, 'height': 760}); p.wait_for_timeout(600)
    check('folding the phone shut mid-move: the house is kept, and the town redraws for the small screen',
          saved_town(p) == [{'plot': 0, 'id': 'm0'}, {'plot': 1, 'id': 'm1'}] and not p.evaluate('tw.busy')
          and p.eval_on_selector_all('.twwalker', 'e => e.length') == 0 and p.get_attribute('#twLayer .twhouse[data-plot="1"]', 'aria-label') == "Gloop's house"
          and p.get_attribute('#twLayer .twhouse[data-plot="1"] img', 'src') == 'town/cottage-orange.webp')
    p.set_viewport_size({'width': 673, 'height': 760}); p.wait_for_timeout(600)
    tap_plot(p, 17); p.wait_for_timeout(3200)
    check('  opened again, the next move works, even to the hilltop far away', len(saved_town(p)) == 3 and not p.evaluate('tw.busy'))
    check('  everyone has a home: no queue, and the plots stop asking', p.eval_on_selector_all('#twLayer .twfirst', 'e => e.length') == 0
          and p.eval_on_selector_all('#twLayer .twplot.ready', 'e => e.length') == 0)
    p.reload(); p.wait_for_timeout(1000)
    check('after a reload the town is just as it was', [p.get_attribute(f'#twLayer .twhouse[data-plot="{i}"]', 'aria-label') for i in (0, 1, 17)]
          == ["Fuzzbert's house", "Gloop's house", "Wigglebum's house"] and p.text_content('#townHint') == 'Tap a house to visit!')
    tap_house(p, 17); p.wait_for_timeout(900)
    check('  the hilltop house opens the hilltop close-up, in orange for the dragon head', p.get_attribute('#twClose .twclosepic', 'src') == 'town/close-hill-orange.webp')
    p.click('#twBack'); p.wait_for_timeout(300)
    p.screenshot(path=OUT / 't5_three.png')
    ctx.close()

    # --- deleting, backing up and restoring ---------------------------------------------------------------------------
    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); seed(p, MONS, [{'plot': 0, 'id': 'm0'}, {'plot': 1, 'id': 'm1'}, {'plot': 2, 'id': 'm2'}])
    check('an unnamed monster asks "I need a home!"', p.get_attribute('#twLayer .twfirst', 'aria-label') == 'I need a home!')
    p.click('#tabLib'); p.wait_for_timeout(500)
    p.evaluate("openCard(store.monsters.find(m => m.id === 'm1'), true)"); p.wait_for_timeout(1500)
    p.click('#del'); p.click('#del'); p.wait_for_timeout(500); p.click('#tabTown'); p.wait_for_timeout(600)
    check('deleting a monster leaves its cottage standing empty', p.get_attribute('#twLayer .twhouse[data-plot="1"]', 'aria-label') == 'An empty house'
          and 'empty' in p.get_attribute('#twLayer .twhouse[data-plot="1"]', 'class'))
    tap_house(p, 1); p.wait_for_timeout(200)
    check('  and the next monster can move into it', {'plot': 1, 'id': 'm3'} in saved_town(p))
    p.wait_for_timeout(2800)
    backup = json.loads(p.evaluate('backupText()'))
    check('Back up saves the town with the monsters', backup.get('town', {}).get('houses') == saved_town(p) and len(backup['monsters']) == 4)
    p.evaluate("localStorage.clear()"); p.reload(); p.wait_for_timeout(900)
    check('  (a cleared phone has an empty town)', p.eval_on_selector_all('#twLayer .twhouse', 'e => e.length') == 0)
    p.evaluate('t => restoreFrom(t)', json.dumps(backup)); p.wait_for_timeout(500)
    check('Restore brings back the monsters and their houses', len(saved_town(p)) == 3 and p.eval_on_selector_all('#twLayer .twhouse', 'e => e.length') == 3
          and p.evaluate('store.monsters.length') == 4
          and p.get_attribute('#twLayer .twhouse[data-plot="1"]', 'aria-label') == "A monster's house")
    bad = dict(backup, town={'houses': [{'plot': 9, 'id': 'm0'}, {'plot': 0, 'id': 'nobody'}, {'plot': -1, 'id': 'm4'}, {'plot': 40, 'id': 'm4'}, 'junk']})
    p.evaluate("localStorage.removeItem('monster-book.town'); tw.houses = []; twSave()")
    p.evaluate('t => restoreFrom(t)', json.dumps(bad)); p.wait_for_timeout(300)
    check('  a messed-up town in a backup only brings back houses that make sense', saved_town(p) == [{'plot': 9, 'id': 'm0'}])
    p.evaluate("localStorage.setItem('monster-book.town', '{\"houses\": [{\"plot\": 0, \"id\": \"m0\"}, {\"plot\": 0, \"id\": \"m4\"}, {\"plot\": 2, \"id\": \"m0\"}]}')")
    p.reload(); p.wait_for_timeout(800)
    check('  and so does messed-up saved data: one house per plot, one plot per monster', p.evaluate('tw.houses') == [{'plot': 0, 'id': 'm0'}])
    # names that need care
    p.evaluate("""() => { store.monsters.push({id: 'mx', created: '2026-10-30T00:00:00Z', h: 2, b: 2, l: 2, name: '<i>Bo</i> & "Co"', food: '', friend: '', grumpy: ''},
                                           {id: 'my', created: '2026-10-31T00:00:00Z', h: 3, b: 4, l: 5, name: 'Supercalifragilistic', food: '', friend: '', grumpy: ''});
                          persist(); tw.houses = [{plot: 0, id: 'mx'}, {plot: 1, id: 'my'}]; twSave(); renderTown(); }""")
    check('a name with < & " in it shows as text, not as code', p.eval_on_selector_all('#twLayer i', 'e => e.length') == 0
          and '<i>Bo</i> & "Co"' in p.get_attribute('#twLayer .twhouse[data-plot="0"]', 'aria-label') and p.text_content('#twLayer .twhouse[data-plot="0"] .twname') == '<i>Bo</i> & "…')
    check('  a long name is shortened on its sign', p.text_content('#twLayer .twhouse[data-plot="1"] .twname') == 'Supercalifrag…')
    p.evaluate("store.monsters.find(m => m.id === 'my').name = 'Professor Supercalifragilistic'; tw.houses = tw.houses.filter(h => h.id !== 'my'); tw.next = 'my'; renderTown()")
    check('  waiting at the gate, the bubble shortens it too, but a screen reader hears it all',
          p.text_content('#twLayer .twbubble b >> nth=0') == 'Professor Supercali…'
          and p.get_attribute('#twLayer .twfirst', 'aria-label').startswith('Professor Supercalifragilistic needs a home!'))
    ctx.close()

    # --- a big town, and a full one -------------------------------------------------------------------------------------
    ctx, p = new_page(b)
    many = [mon(i, 1 + i % 30, 1 + (i * 7) % 30, 1 + (i * 13) % 30, f'Monster {i}') for i in range(12)]
    p.goto(BASE + '?for=Sam'); seed(p, many, [{'plot': i, 'id': f'm{i}'} for i in range(5)])
    check('twelve monsters, five housed: 4 shown waiting, with "+3"', p.eval_on_selector_all('#twLayer .twwait', 'e => e.length') == 3
          and p.text_content('#twLayer .twmore') == '+3')
    check('  the valley scrolls sideways inside its box, not the page', p.evaluate("$('townBox').scrollWidth > $('townBox').clientWidth")
          and not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
    lots = [mon(i, 1 + i % 30, 1 + (i * 7) % 30, 1 + (i * 13) % 30, f'Monster {i}') for i in range(N_PLOTS + 1)]
    seed(p, lots, [{'plot': i, 'id': f'm{i}'} for i in range(N_PLOTS)])
    check(f'every plot built on, and one more monster: the valley says it\'s full ({p.text_content("#townHint")})',
          'full' in p.text_content('#townHint') and p.eval_on_selector_all('#twLayer .twhouse', 'e => e.length') == N_PLOTS)
    p.screenshot(path=OUT / 't6_full.png')
    ctx.close()

    # --- the town talks -------------------------------------------------------------------------------------------------
    said = lambda p: p.evaluate('window.__said')
    def touch_sky(p):   # a real touch on the valley's sky, where nothing is tappable
        box = p.locator('#townBox').bounding_box(); p.mouse.click(box['x'] + box['width'] * .5, box['y'] + 8)
    WELCOME = 'Welcome to your monster town! Make a monster, and it will move in.'
    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); p.evaluate('localStorage.clear()'); p.reload(); p.wait_for_timeout(1000)
    check("talk: nothing is said before the first touch (phones won't), and the welcome waits for it", said(p) == [] and p.evaluate('tw.pending') == WELCOME)
    touch_sky(p); p.wait_for_timeout(200)
    check('  the first touch says the welcome', said(p) == [WELCOME] and p.evaluate('tw.pending') is None)
    touch_sky(p); p.wait_for_timeout(200)
    check('  only once', len(said(p)) == 1)
    tap_plot(p, 3)
    check('  an empty plot, with no monsters yet: "Make a monster, and it will move in!"', said(p)[-1] == 'Make a monster, and it will move in!')
    p.click('#twLayer .twarm[data-sign="games"]'); p.wait_for_timeout(300)
    check('  the Games sign says "Games!" and opens the games', said(p)[-1] == 'Games!' and p.is_visible('#games'))
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('  coming back by the Town tab says the welcome again', said(p)[-1] == WELCOME)
    p.click('#twLayer .twarm[data-sign="make"]'); p.wait_for_timeout(300)
    check('  the Make sign says "Make a monster!"', said(p)[-1] == 'Make a monster!' and p.is_visible('#make'))
    p.click('#tabTown'); p.wait_for_timeout(300)
    p.click('#twLayer .twarm[data-sign="learn"]'); p.wait_for_timeout(500)
    check('  the Learn sign says "Learning Lab!" and waits a moment, so the word isn\'t cut off', said(p)[-1] == 'Learning Lab!' and p.url.startswith('http://127.0.0.1'))
    p.wait_for_url('https://learn.mikeohalloran.au/**', timeout=8000)
    check('  then goes to the Learning Lab', p.url == 'https://learn.mikeohalloran.au/?for=Sam')
    p.goto(BASE + '?for=Sam#whack'); p.wait_for_timeout(900)
    p.click('#whackgame .mute'); p.click('#tabTown'); p.wait_for_timeout(300); touch_sky(p); p.wait_for_timeout(200)
    check('  muted in a game: the town says nothing either', not p.evaluate('sound.on') and said(p) == [])
    p.click('#twLayer .twarm[data-sign="seek"]'); p.wait_for_timeout(350)
    check('  and the Seek sign goes straight away, with nothing to wait for', p.url == 'https://seek.mikeohalloran.au/?for=Sam')
    ctx.close()

    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); seed(p, MONS[:2])
    check('talk: with a monster waiting, the welcome waits for the first touch', said(p) == [] and p.evaluate('tw.pending') == 'Fuzzbert needs a home! Tap a plus to build a house.')
    p.click('#twLayer .twfirst'); p.wait_for_timeout(200)
    check('  a first touch on the monster at the gate says its own line instead', said(p) == ['I need a home! Tap a plus to build me a house.'])
    ctx.close()

    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam'); seed(p, MONS[:3])
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('talk: coming to the town with monsters waiting', said(p) == ['Fuzzbert needs a home! Tap a plus to build a house.'])
    tap(p, '#twLayer .twfirst')
    check('  tapping the monster at the gate asks again', said(p)[-1] == 'I need a home! Tap a plus to build me a house.')
    n = len(said(p)); tap_plot(p, 0); p.wait_for_timeout(400)
    check('  nothing is said over the hops while it moves in', len(said(p)) == n)
    p.wait_for_timeout(2800)
    check(f'  moved in, with another waiting ({said(p)[-1]})', said(p)[-1] == 'Fuzzbert has a new home! Gloop needs one too!')
    tap_plot(p, 1); p.wait_for_timeout(3200); tap_plot(p, 2); p.wait_for_timeout(3200)
    check(f'  the last one in ({said(p)[-1]})', said(p)[-1] == 'Wigglebum has a new home! Tap it to visit!')
    p.evaluate("""() => { Object.assign(store.monsters.find(m => m.id === 'm0'), {food: 'Pizza', friend: 'A snail', grumpy: 'Bath time'});
                          Object.assign(store.monsters.find(m => m.id === 'm1'), {name: '', grumpy: 'Rain'}); persist(); }""")
    tap_house(p, 0); p.wait_for_timeout(400)
    check(f'visiting: the monster says hello and its favourite food ({said(p)[-1]})', said(p)[-1] == "Hi! I'm Fuzzbert! I love Pizza!")
    facts = []
    for k in range(3): p.click('#twLeaner'); p.wait_for_timeout(150); facts.append(said(p)[-1])
    check(f'  each tap says the next thing, then starts again ({facts})', facts == ['My best friend is a snail!', 'I get grumpy about Bath time!', "Hi! I'm Fuzzbert! I love Pizza!"])
    n = len(said(p)); p.set_viewport_size({'width': 841, 'height': 600}); p.wait_for_timeout(600); p.set_viewport_size({'width': 673, 'height': 760}); p.wait_for_timeout(600)
    check('  turning the phone with the house open says nothing', len(said(p)) == n and p.is_visible('#twClose'))
    p.click('#twLeaner'); p.wait_for_timeout(150)
    check('  and the next tap carries on where it was', said(p)[-1] == 'My best friend is a snail!')
    n = len(said(p)); p.click('#twBack'); p.wait_for_timeout(300)
    check('  going back to the valley says nothing', len(said(p)) == n)
    tap_house(p, 1); p.wait_for_timeout(400); facts = [said(p)[-1]]
    for k in range(2): p.click('#twLeaner'); p.wait_for_timeout(150); facts.append(said(p)[-1])
    check(f'  no name and only a grumpy thing: the rest is skipped ({facts})', facts == ["Hi! I'm a monster!", 'I get grumpy about Rain!', "Hi! I'm a monster!"])
    p.click('#twBack'); p.wait_for_timeout(300); tap_house(p, 2); p.wait_for_timeout(400); p.click('#twLeaner'); p.wait_for_timeout(150)
    check('  nothing answered but a name: hello each time', said(p)[-2:] == ["Hi! I'm Wigglebum!", "Hi! I'm Wigglebum!"])
    p.click('#twBack'); p.wait_for_timeout(300); tap_plot(p, 5)
    check('  an empty plot with everyone housed: "Make another monster to live here!"', said(p)[-1] == 'Make another monster to live here!')
    n = len(said(p)); p.set_viewport_size({'width': 841, 'height': 600}); p.wait_for_timeout(600); p.set_viewport_size({'width': 673, 'height': 760}); p.wait_for_timeout(600)
    check('  redrawing the valley says nothing', len(said(p)) == n)
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('  coming to the town with everyone housed: "Tap a house to visit!"', said(p)[-1] == 'Tap a house to visit!')
    ctx.close()

    ctx, p = new_page(b)
    nearly = [mon(i, 1 + i % 30, 1 + (i * 7) % 30, 1 + (i * 13) % 30, f'Monster {i}') for i in range(N_PLOTS + 1)]
    p.goto(BASE + '?for=Sam'); seed(p, nearly, [{'plot': i, 'id': f'm{i}'} for i in range(N_PLOTS - 1)])
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('talk: one plot left, two waiting', said(p)[-1] == f'Monster {N_PLOTS - 1} needs a home! Tap a plus to build a house.')
    tap_plot(p, N_PLOTS - 1); p.wait_for_timeout(3200)
    check(f'  the last plot taken, with one still waiting ({said(p)[-1]})', said(p)[-1] == f'Monster {N_PLOTS - 1} has a new home! The valley is full! New places are coming soon.')
    tap(p, '#twLayer .twfirst')
    check('  the monster at the gate in a full valley', said(p)[-1] == 'I need a home! New places are coming soon.')
    p.click('#tabTown'); p.wait_for_timeout(300)
    check('  coming to a full town', said(p)[-1] == 'The valley is full! New places are coming soon.')
    ctx.close()

    # --- every screen size --------------------------------------------------------------------------------------------
    for size in SIZES:
        ctx, p = new_page(b, size, mobile=size != 'laptop')
        p.goto(BASE + '?for=Sam'); seed(p, MONS, [{'plot': 0, 'id': 'm0'}, {'plot': 1, 'id': 'm1'}, {'plot': 5, 'id': 'm2'}])
        p.wait_for_timeout(400)
        r = p.evaluate("""(() => { const w = $('townWrap').getBoundingClientRect(), world = $('townWorld').getBoundingClientRect(), v = $('townBox').getBoundingClientRect();
                         return {bottom: w.bottom, h: innerHeight, worldH: world.height, worldW: world.width, boxH: v.height, seen: v.width / world.width,
                                 wide: document.documentElement.scrollWidth > innerWidth, tabs: $('tabLib').getBoundingClientRect().right <= innerWidth,
                                 src: $('twValley').currentSrc.split('/').pop(), first: !!document.querySelector('#twLayer .twfirst')}; })()""")
        check(f'{size} ({SIZES[size][0]}x{SIZES[size][1]}): the valley fits on screen, keeps its shape, no sideways page scroll, tabs fit '
              f'({r["bottom"]:.0f}/{r["h"]}, {r["seen"]:.0%} of it across, {r["src"]})',
              r['bottom'] <= r['h'] + 1 and not r['wide'] and r['tabs'] and abs(r['worldH'] - r['boxH']) < 2 and abs(r['worldW'] / r['worldH'] - 3168 / 1344) < .01
              and r['seen'] >= .2 and r['first'])
        p.screenshot(path=OUT / f's_{size.replace(" ", "_").replace(",", "")}.png')
        tap_house(p, 0); p.wait_for_timeout(1200)
        c = p.evaluate("""(() => { const pic = document.querySelector('#twClose .twclosepic').getBoundingClientRect(), box = $('twClose').getBoundingClientRect(), f = $('twLeaner').getBoundingClientRect();
                         return pic.left <= box.left + 1 && pic.right >= box.right - 1 && pic.top <= box.top + 1 && pic.bottom >= box.bottom - 1 && f.left >= box.left && f.right <= box.right && f.top >= box.top; })()""")
        check(f'  the close-up covers the box and the monster at the window is in view', c)
        p.screenshot(path=OUT / f'c_{size.replace(" ", "_").replace(",", "")}.png')
        ctx.close()

    # --- picture answers --------------------------------------------------------------------------------------------
    ctx, p = new_page(b)
    p.goto(BASE + '?for=Sam#make'); seed(p, MONS[:2])
    p.evaluate("goTo('H', 1, 1); goTo('B', 4, 1); goTo('L', 4, 1)"); p.wait_for_timeout(500)
    p.click('#toMeet'); p.wait_for_timeout(1200)
    ideas = p.evaluate('nameIdeas')
    check(f'four name ideas, one made from the head and legs ({", ".join(ideas)})', len(ideas) == 4 and 'Uniguin' in ideas
          and p.eval_on_selector_all('#p_name .pick[data-pick]', 'e => e.length') == 4)
    check('12 foods, 12 grumpy things, and the friends start with the monsters already made',
          p.eval_on_selector_all('#p_food .pick', 'e => e.length') == 12 and p.eval_on_selector_all('#p_grumpy .pick', 'e => e.length') == 12
          and p.eval_on_selector_all('#p_friend .pick[data-id]', 'e => e.map(b => b.dataset.pick)') == ['Gloop', 'Fuzzbert']
          and p.eval_on_selector_all('#p_friend .pick', 'e => e.length') == 10)
    p.wait_for_timeout(500)
    pics = p.evaluate("[...document.querySelectorAll('#questions img.pp')].map(i => [i.getAttribute('src'), i.complete && i.naturalWidth > 0])")
    check(f'  every answer has its own 3D picture, all loaded ({len(pics)})', len(pics) == 32 and all(ok for _, ok in pics) and len({s for s, _ in pics}) == 32)
    p.click('#p_name .pick[data-pick="Uniguin"]'); p.click('#p_food [data-pick="Worms"]'); p.click('#p_friend [data-pick="Gloop"]'); p.click('#p_grumpy [data-pick="Bath time"]')
    check('tapping pictures fills in the answers and marks them', [p.input_value(f'#q_{k}') for k in ('name', 'food', 'friend', 'grumpy')] == ['Uniguin', 'Worms', 'Gloop', 'Bath time']
          and p.eval_on_selector_all('#questions .pick[aria-pressed="true"]', 'e => e.length') == 4 and p.evaluate('draft.friendId') == 'm1')
    p.screenshot(path=OUT / 'p1_meet.png', full_page=True)
    before = p.input_value('#q_name'); p.click('#makeName')
    check(f'the dice gives a different name ({before} → {p.input_value("#q_name")})', p.input_value('#q_name') not in ('', before))
    p.fill('#q_food', 'Spaghetti and pancakes')
    check('typing your own answer still works, and unmarks the pictures', p.eval_on_selector_all('#p_food .pick[aria-pressed="true"]', 'e => e.length') == 0
          and p.evaluate("pickSrc('food', 'Spaghetti and pancakes')") == '' and p.evaluate("pickSrc('grumpy', 'bath time')") == 'town/pick-grumpy-bath-time.webp')
    p.fill('#q_friend', 'A snail called Gary'); p.click('#toCard'); p.wait_for_timeout(1800)
    check('  a typed best friend forgets the picked monster', p.evaluate('draft.friendId') is None and p.evaluate('draft.friend') == 'A snail called Gary')
    p.click('#editAns'); p.wait_for_timeout(600)
    check('Change answers keeps the name and shows the same ideas', p.input_value('#q_name') != '' and p.eval_on_selector_all('#p_name .pick[data-pick]', 'e => e.length') == 4)
    p.click('#p_friend [data-pick="Fuzzbert"]'); p.click('#toCard'); p.wait_for_timeout(1800)
    check('  picking Fuzzbert as best friend remembers which monster', p.evaluate('draft.friendId') == 'm0')
    p.screenshot(path=OUT / 'p2_card.png', full_page=True)
    check('before saving, there is no "Find them a home"', not p.is_visible('#toTown'))
    p.click('#saveLib'); p.wait_for_timeout(500)
    check('saved: the best friend is kept, and "Find them a home" appears', p.evaluate('store.monsters.at(-1).friendId') == 'm0' and p.is_visible('#toTown'))
    p.click('#toTown'); p.wait_for_timeout(900)
    name = p.evaluate('store.monsters.at(-1).name')
    check(f'  which goes to the town with {name} first in the queue (ahead of older monsters)', p.is_visible('#town')
          and p.get_attribute('#twLayer .twfirst', 'aria-label') == f'{name} needs a home!')
    check(f'  and says so ({p.evaluate("window.__said.at(-1)")})', p.evaluate('window.__said.at(-1)') == f'{name} needs a home! Tap a plus to build a house.')
    tap_plot(p, 0); p.wait_for_timeout(2800)
    p.click('#tabLib'); p.wait_for_timeout(400); p.evaluate("openCard(store.monsters.at(-1), true)"); p.wait_for_timeout(1500)
    check('  once housed, its card no longer offers a home', not p.is_visible('#toTown'))
    p.evaluate("openCard(store.monsters[0], true)"); p.wait_for_timeout(1500)
    check('  an older monster with no house does', p.is_visible('#toTown'))
    ctx.close()
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
