# Monster Book

A tiny website for a young child. Flip a monster's head, body and legs, answer four questions about the monster you made, and get a card to print. Or play games with the monsters.

**Try it:** [monsters.mikeohalloran.au](https://monsters.mikeohalloran.au/)

Built with [Claude](https://claude.ai) in a day, alongside the printed book it goes with.

![Flip a monster, make its card, then play Whack-a-monster and Monster bedtime](docs/screenshot.png)

## The story

I made my daughter a mix-and-match flip book: 30 monsters, each page cut into three strips, so she can flip heads, bodies and legs independently. That's 27,000 monsters in one coil-bound book. The art came from Google AI Studio, the page layout and print files from Python, and the printing from Officeworks.

The book's last page asks four questions about the monster you just made: What's their name? What's their favourite food? Who is their best friend? What makes them grumpy? Sam's answers deserved somewhere to live, so the book got a website.

The site does the same thing as the book, on a phone:

1. **Flip.** The strips turn over like real pages, by arrow or by swipe. Shuffle picks three at random, or you can type the codes printed on the book's strips (H12, B03, L27).
2. **Meet your monster.** The four questions, with a "make up a name" button for when a young child is stuck.
3. **Make the card.** A picture with the name in rainbow letters, the monster, the answers, the date and the strip codes. Save it, print it, stick it on the fridge.
4. **My monsters.** Every saved monster, on that device, with backup and restore.

A gift copy of the book gets a link like `?for=Max`, and the site becomes Max's Monster Book.

Then it got things the book can't do: a **Games** tab, with three games made from the same 30 monsters.

- **Monster match.** A memory game. Cards start face down; turn two over, and if they're the same monster they stay. Four levels, from 6 pairs up to all 30 (60 cards).
- **Whack-a-monster.** Monsters pop up out of holes and you bop them. A round is 20 monsters, not a countdown. Hard adds sleepy monsters you have to leave alone, or they wake up grumpy.
- **Monster bedtime.** Your own saved monsters go to bed. Tap one and it hops onto a pillow, under a blanket in the colour and texture of its body; tap its lamp and it starts snoring. When they're all asleep the lights go down, the stars come out and Twinkle Twinkle plays on a music box. No score, no way to lose.

Each game has its own link (`/#match`, `/#whack`, `/#bedtime`), and best scores are kept on the device.

## How it's built

**It's one HTML file and 120 images.** No framework, no build step, no server, no database, no accounts, no analytics. Hosting is Cloudflare Pages on the free plan, and it will stay free however many families use it.

That was the main design decision. The obvious version of this site has user accounts, cloud saves and an API. For a thing used by a handful of families, each of those is a cost, a privacy question and something to maintain. So instead:

- **The monster is assembled in the browser.** The site holds 90 transparent strip images (30 heads, bodies and legs, about 3 MB in total), cut from the real print files so they match the book exactly. Three `<img>` tags stacked in a column are a monster.
- **The card is drawn in the browser** on a canvas: 1200 × 1600 px, with the same fonts and colours as the printed book. Saving it is just saving a PNG.
- **The library lives in `localStorage`.** Each saved monster is three codes, four answers and a date, a couple of hundred bytes. The card is redrawn from the strips every time, so nothing bulky is stored. Backup and restore move the library between devices as a small JSON file.
- **Nothing anyone types leaves their phone.** The only outside request is Google Fonts.

### Things that turned out to matter

- **A page turn, not a fade.** The first version faded between strips. Flipping a real strip in the book turns it over, so the site does the same: a 3D rotate on the strip, hinged at the coil. It's one CSS transform and it made the thing feel like the book.
- **White tummies.** Cutting the monsters out of the print files by colour left the white tummies transparent. The fix was to build a solid silhouette of each monster first, then use that as the alpha mask. Same trick for the printed cut lines that cross pale tummies at the joins.
- **iPhones delete site data.** Safari removes a site's saved data if you don't open it for seven days of Safari use. Adding the site to the Home Screen avoids that. It's why there's a backup button.
- **Nothing to type.** A young child can't type H12, but she can swipe. The codes are the parent's shortcut; the swipe is hers.
- **Nothing to read, either.** Each tab has a picture above its label (a monster for Make, a game controller for Games, a heart for My monsters), and the games page is three big pictures, so she can find a game herself. The address follows the tabs, so a reload keeps her where she was.
- **Sounds without sound files.** The boings, the snores and the lullaby are all made in the browser with the Web Audio API, so the site is still one HTML file and the images. There's a mute button, and it's remembered.
- **One link for the book.** The printed book's QR code still opens on Make. The games are a tab, not the front door, so nobody coming from the book has an extra tap.

## What's in this repo

| Path | What it is |
|---|---|
| `index.html` | The whole site: markup, styles and script in one file |
| `tools/make_web_strips.py` | Cuts the 90 strip images and 30 face icons from the book's print pages |
| `tools/build_site.py` | Wraps the page for hosting and sets the generic title |
| `tools/test_site.py` | Drives the site in Chromium at phone size: flipping, swiping, codes, saving, backup, restore |
| `tools/test_match.py` | Plays the match game: a wrong pair flips back, a full game ends in a win, the best score sticks, every level fits a phone |
| `tools/test_links.py` | The tab bar fits at 360–430 px, and the `#games`, `#match`, `#whack`, `#bedtime` and `#monsters` links and gift links work |
| `tools/test_games.py` | Plays Whack-a-monster and Monster bedtime with the page clock fast-forwarded: a perfect round, an empty round, a sleepy monster on Hard, a full bedtime from tuck-in to Good morning |
| `docs/` | Screenshots |

The monster images aren't in the repo; they're the book. Everything else is.

## Running it locally

The page needs to be served, not opened from a file, because browsers block images from `file://` pages.

```
python3 -m http.server 8000
```

Then open `http://localhost:8000`. Without the `strips/` and `faces/` folders you'll get the layout with empty frames, which is enough to see how it works.

## Credits

Monster art generated with Google AI Studio. Fonts: [Fredoka](https://fonts.google.com/specimen/Fredoka) and [Nunito](https://fonts.google.com/specimen/Nunito), both Open Font Licence. Site and tools written with Claude.

Made for my daughter.
