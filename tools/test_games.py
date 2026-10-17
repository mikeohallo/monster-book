"""Play Whack-a-monster and Monster bedtime in Chromium at phone size, with the page clock fast-forwarded.
    python3 tools/test_games.py OUTDIR"""
import http.server, socketserver, sys, threading, functools, json
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent          # the repo root, where index.html lives
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
PORT = 8796
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{PORT}/index.html'
css = ("@font-face{font-family:'Fredoka';font-weight:300 700;src:url(http://127.0.0.1:%d/Fredoka.ttf)}"
       "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(http://127.0.0.1:%d/Nunito.ttf)}") % (PORT, PORT)

problems = []
def check(label, ok):
    print(('ok   ' if ok else 'FAIL ') + label)
    if not ok: problems.append(label)

def new_page(b, width=390):
    ctx = b.new_context(viewport={'width': width, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=css))
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    p = ctx.new_page()
    p.on('console', lambda m: m.type == 'error' and problems.append(f'console error: {m.text}'))
    p.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    return ctx, p

def up_holes(p, sleepy=False):
    sel = '.whole.up.sleepy' if sleepy else '.whole.up:not(.sleepy):not(.hit)'
    return p.evaluate(f"[...document.querySelectorAll('.whole')].map((e, i) => e.matches('{sel}') ? i : -1).filter(i => i >= 0)")

def play_whack(p, tap=True, tap_sleepy_once=False, shot=None, sleepy_shot=None):
    p.click('#wGo')
    shot_done = sleepy_done = tapped_sleepy = False
    global sleepy_before
    sleepy_before = None
    for step in range(900):
        p.clock.run_for(100)
        if p.is_visible('#wWin'): return tapped_sleepy
        if tap:
            for i in up_holes(p):
                if shot and not shot_done:
                    p.wait_for_timeout(260); p.screenshot(path=OUT / shot); shot_done = True
                p.locator('.whole').nth(i).dispatch_event('pointerdown')
        if tap_sleepy_once and not tapped_sleepy:
            s = up_holes(p, sleepy=True)
            if s:
                if sleepy_shot and not sleepy_done:
                    p.wait_for_timeout(260); p.screenshot(path=OUT / sleepy_shot); sleepy_done = True
                before = sleepy_before = int(p.text_content('#wScore'))
                p.locator('.whole').nth(s[0]).dispatch_event('pointerdown')
                check(f'tapping a sleepy monster makes it grumpy (score {before} -> {p.text_content("#wScore")})',
                      p.evaluate(f"document.querySelectorAll('.whole')[{s[0]}].classList.contains('grumpy')") and int(p.text_content('#wScore')) == max(0, before - 1))
                tapped_sleepy = True
    problems.append('whack round never finished')
    return tapped_sleepy

with sync_playwright() as pw:
    b = pw.chromium.launch()

    # ---------------------------------------------------------------- hub + whack
    ctx, p = new_page(b)
    p.clock.install()
    p.goto(BASE + '#games'); p.wait_for_timeout(900); p.clock.run_for(500)
    check('#games opens the games page: Make a monster, then 6 games', p.is_visible('#games') and p.is_visible('#playMake') and p.eval_on_selector_all('.gametile', 'e => e.length') == 6)
    check('Games tab selected', p.get_attribute('#tabGames', 'aria-selected') == 'true')
    check('no sideways scroll on the games page', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
    p.screenshot(path=OUT / 'g1_hub.png')
    p.click('#playWhack'); p.wait_for_timeout(300)
    check('Whack tile opens #whack with the Start button', p.evaluate('location.hash') == '#whack' and p.is_visible('#wGo'))
    check('9 holes and 20 dots', p.eval_on_selector_all('.whole', 'e => e.length') == 9 and p.eval_on_selector_all('#wDots i', 'e => e.length') == 20)
    p.screenshot(path=OUT / 'g2_whack_ready.png')

    play_whack(p, tap=True, shot='g3_whack_up.png')
    p.wait_for_timeout(700)
    check(f'Easy, tapping every monster: "{p.text_content("#wWinText")}"', '20 of 20' in p.text_content('#wWinText'))
    check('three stars for 20', p.eval_on_selector_all('#wStars svg.on', 'e => e.length') == 3)
    check('all dots green', p.eval_on_selector_all('#wDots i.hit', 'e => e.length') == 20)
    p.screenshot(path=OUT / 'g4_whack_win.png', full_page=True)
    check(f'best saved: "{p.text_content("#wBest")}"', p.text_content('#wBest') == 'Best: 20')

    p.click('#wAgain'); p.clock.run_for(100)
    check('Play again starts straight away', not p.is_visible('#wStart') and p.is_visible('#wBoard'))
    for _ in range(900):
        p.clock.run_for(100)
        if p.is_visible('#wWin'): break
    check(f'Easy, tapping nothing: "{p.text_content("#wWinText")}"', '0 of 20' in p.text_content('#wWinText') and 'best is 20' in p.text_content('#wWinText'))
    check('one star for trying', p.eval_on_selector_all('#wStars svg.on', 'e => e.length') == 1)

    # hard, with sleepy monsters
    p.click('#wLevels .level >> nth=2'); p.clock.run_for(100)
    check('Hard selected, best empty', p.get_attribute('#wLevels .level >> nth=2', 'aria-pressed') == 'true' and p.text_content('#wBest') == '')
    saw = play_whack(p, tap=True, tap_sleepy_once=True, sleepy_shot='g5_whack_sleepy.png')
    check('a sleepy monster appeared on Hard', saw)
    score = int(p.text_content('#wScore'))
    want = 20 - (1 if sleepy_before else 0)   # waking one costs a point, but the score never goes below 0
    check(f'Hard score {score} (20 bopped, minus 1 for waking one unless the score was 0 then)', score == want)

    # leaving mid-game stops it
    p.click('#wLevels .level >> nth=1'); p.click('#wGo'); p.clock.run_for(2000)
    p.click('#tabMake'); p.clock.run_for(5000)
    p.click('#tabGames'); p.click('#playWhack'); p.clock.run_for(200)
    check('leaving mid-game stops it; coming back shows Start again', p.is_visible('#wGo') and p.text_content('#wScore') == '0')
    p.click('#playWhack') if p.is_visible('#playWhack') else None
    p.click('.gamebar .back >> visible=true'); p.wait_for_timeout(200)
    check('All games button goes back to the games page', p.is_visible('#games'))
    ctx.close()

    # ---------------------------------------------------------------- bedtime
    ctx, p = new_page(b)
    saved = {'owner': 'Sam', 'monsters': [
        {'id': 'a', 'h': 18, 'b': 26, 'l': 7, 'name': 'Fuzzbert', 'food': '', 'friend': '', 'grumpy': '', 'created': '2026-10-14T09:00:00Z'},
        {'id': 'b', 'h': 27, 'b': 28, 'l': 27, 'name': 'Princess Wobble', 'food': '', 'friend': '', 'grumpy': '', 'created': '2026-10-14T09:05:00Z'}]}
    p.goto(BASE); p.evaluate(f"localStorage.setItem('monster-book.v1', {json.dumps(json.dumps(saved))})")
    p.clock.install()
    p.goto(BASE + '?for=Sam#bedtime'); p.wait_for_timeout(1500); p.clock.run_for(300)   # a new URL, so a real reload
    labels = p.eval_on_selector_all('.waiter', 'els => els.map(e => e.getAttribute("aria-label"))')
    check(f'3 monsters waiting, both saved ones among them: {labels}', len(labels) == 3 and any('Fuzzbert' in l for l in labels) and any('Princess Wobble' in l for l in labels))
    check('3 beds, all empty', p.eval_on_selector_all('.bed', 'e => e.length') == 3 and p.eval_on_selector_all('.bed.in', 'e => e.length') == 0)
    check('waiting monsters drawn', p.eval_on_selector_all('.waiter canvas', 'e => e.length') == 3)
    fuzz = [i for i, l in enumerate(labels) if 'Fuzzbert' in l][0]
    blanket = p.evaluate(f"getComputedStyle(document.querySelectorAll('.bed .blanket')[{fuzz}]).backgroundColor")
    check(f"Fuzzbert's blanket is the Alien body's purple ({blanket}), slimy pattern", blanket == 'rgb(168, 128, 214)' and p.evaluate(f"document.querySelectorAll('.bed .blanket')[{fuzz}].classList.contains('tex-slimy')"))
    check('no sideways scroll in the bedroom', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
    p.screenshot(path=OUT / 'b1_room.png', full_page=True)
    # lamp before the monster is in bed does nothing
    p.locator('.bed >> nth=0 >> .lamp').dispatch_event('click'); p.clock.run_for(200)
    check('lamp on an empty bed does nothing', p.eval_on_selector_all('.bed.asleep', 'e => e.length') == 0)
    p.locator('.waiter >> nth=0').dispatch_event('click'); p.wait_for_timeout(1100); p.clock.run_for(100); p.wait_for_timeout(500)
    check('tapping a monster puts it in its bed', p.evaluate("document.querySelectorAll('.bed')[0].classList.contains('in')"))
    check('the waiting monster has gone', p.evaluate("document.querySelectorAll('.waiter')[0].classList.contains('gone')"))
    p.screenshot(path=OUT / 'b2_one_in.png', full_page=True)
    p.locator('.bed >> nth=0 >> .lamp').dispatch_event('click'); p.clock.run_for(100)
    check('lamp off: monster asleep', p.evaluate("document.querySelectorAll('.bed')[0].classList.contains('asleep')"))
    p.locator('.waiter >> nth=1').dispatch_event('click'); p.locator('.waiter >> nth=2').dispatch_event('click'); p.wait_for_timeout(1200); p.clock.run_for(100); p.wait_for_timeout(500)
    p.locator('.bed >> nth=1 >> .lamp').dispatch_event('click'); p.wait_for_timeout(1500)
    p.screenshot(path=OUT / 'b3_two_asleep.png', full_page=True)
    p.locator('.bed >> nth=2 >> .lamp').dispatch_event('click'); p.clock.run_for(1300); p.wait_for_timeout(3500)
    gn = p.text_content('#goodnight')
    check(f'all asleep: lights out, "{gn}"', p.evaluate("document.getElementById('room').classList.contains('dark')") and gn.startswith('Goodnight, ') and 'Fuzzbert' in gn and ' and ' in gn)
    check('Good morning button shows', p.is_visible('#morning'))
    p.screenshot(path=OUT / 'b4_night.png', full_page=True)
    p.click('#morning'); p.wait_for_timeout(800); p.clock.run_for(200)
    check('Good morning: lights on, beds empty, 3 monsters waiting', not p.evaluate("document.getElementById('room').classList.contains('dark')")
          and p.eval_on_selector_all('.bed.in', 'e => e.length') == 0 and p.eval_on_selector_all('.waiter:not(.gone)', 'e => e.length') == 3)
    check('mute button toggles', (p.click('#bedgame .mute') or True) and p.get_attribute('#bedgame .mute', 'aria-pressed') == 'true')
    p.click('#bedgame .mute')
    ctx.close()

    # bedtime with nothing saved, at iPhone SE width
    ctx, p = new_page(b, 360)
    p.goto(BASE + '#bedtime'); p.wait_for_timeout(1500)
    check('nothing saved: 3 whole monsters go to bed instead', p.eval_on_selector_all('.waiter', 'e => e.length') == 3)
    check('360px: no sideways scroll', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
    p.screenshot(path=OUT / 'b5_360.png', full_page=True)
    p.goto(BASE + '#whack'); p.wait_for_timeout(800)
    check('360px whack: no sideways scroll', not p.evaluate('document.documentElement.scrollWidth > innerWidth'))
    p.screenshot(path=OUT / 'g6_whack_360.png', full_page=True)
    ctx.close()
    b.close()
srv.shutdown()
print('PROBLEMS:' if problems else 'all good', *problems, sep='\n  ')
