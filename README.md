# Monster Lab

A tiny website for young children. Flip a monster's head, body and legs, answer four questions about the monster you made, and get a card to print. Then give it a house in a little 3D valley, and play games with the monsters.

**Try it:** [monsters.mikeohalloran.au](https://monsters.mikeohalloran.au/)

Built with [Claude](https://claude.ai) in a day, alongside the printed book it goes with.

![The monster town: a toy-model valley with a signpost to the games, Make, Learn and Seek, a monster at the gate asking for a home and cottages with name signs; a close-up of one cottage with its monster waving from the window; and Meet your monster, with name ideas and pictures of foods and friends to tap](docs/town.jpg)

## The story

I made my daughter a mix-and-match flip book: 30 monsters, each page cut into three strips, so she can flip heads, bodies and legs independently. That's 27,000 monsters in one coil-bound book. The art came from Google AI Studio, the page layout and print files from Python, and the printing from Officeworks.

The book's last page asks four questions about the monster you just made: What's their name? What's their favourite food? Who is their best friend? What makes them grumpy? Her answers deserved somewhere to live, so the book got a website.

The site does the same thing as the book, on a phone:

1. **Flip.** The strips turn over like real pages, by arrow or by swipe. Shuffle picks three at random, or you can type the codes printed on the book's strips (H12, B03, L27).
2. **Meet your monster.** The four questions, each with answers to tap, so a child who can't read or type yet can answer them herself:
   - name ideas made from the monster's own pieces (a unicorn head on penguin legs is a Uniguin), and a dice for more;
   - pictures of foods, some of them silly (socks, worms, smelly shoes);
   - the other monsters she's made, as best friends;
   - things that make monsters grumpy.

   The phone reads each one out. Typing still works.
3. **Make the card.** A picture with the name in rainbow letters, the monster, the answers, the date and the strip codes. Save it, print it, stick it on the fridge.
4. **My monsters.** Every saved monster, on that device, with backup and restore.

A gift copy of the book gets a link like `?for=Max`, and the site becomes Max's Monster Lab.

Then it got things the book can't do. The site opens on **the town**: a wide toy-model valley, with a lane, a forest, a lake, a hill and the mountains, that scrolls sideways.

- Monsters you've made wait at the gate ("Fuzzbert needs a home!").
- Tap one of the 22 plots and a cottage pops up with its roof in the monster's colour. The monster hops over, getting smaller as it goes further away, and moves in.
- Tap a house for a close-up of that part of the valley, with its monster leaning out of the window, waving.
- A signpost at the gate leads to the games, Make, the Learning Lab and Seek.

![The games page with Make a monster at the top, flipping a monster, Whack-a-monster and Monster bedtime](docs/screenshot.png)

And there are games made from the same 30 monsters, on the games page, with **Make a monster** as the big first tile and the games beneath it.

- **Monster match.** A memory game. Cards start face down; turn two over, and if they're the same monster they stay. Four levels, from 6 pairs up to all 30 (60 cards).
- **Whack-a-monster.** Monsters pop up out of holes and you bop them. A round is 20 monsters, not a countdown. Hard adds sleepy monsters you have to leave alone, or they wake up grumpy.
- **Monster bedtime.** Your own saved monsters go to bed. Tap one and it hops onto a pillow, under a blanket in the colour and texture of its body; tap its lamp and it starts snoring. When they're all asleep the lights go down, the stars come out and Twinkle Twinkle plays on a music box. No score, no way to lose.

For Halloween, three spooky ones:

- **Torch hunt.** The lights are off and monsters are hiding. Drag a finger to shine the torch; hold it on a monster and it pops out with a friendly "boo!" and a giggle. Find them all and the lights come on. Two rooms:
  - **The bedroom:** behind the couch, in the toy box, under the bed and behind the curtains. Easy hides 3, Tiny torch hides 10.
  - **The witch's cottage:** twice as wide as the screen, so the room slides along when the torch gets near an edge. Monsters hide in the cauldron, under the witch's hat, between the spell books, behind the black cat, upside down in the drying herbs and in 12 other places. Easy hides 4, Tiny torch hides 12.

  On Hard and Tiny torch three of the faces wait in the tray to be found first, and a hidden monster giggles when the torch gets close, louder the closer it gets. Tiny torch has a much smaller beam, and some monsters hide deeper, so only their horns or eyes show.
- **Pumpkin face maker.** Tap the pumpkin's eyes, nose or mouth to change them, light it up, save the picture. Then print the face as a carving stencil on A4, at a real size (a 12, 15 or 18 cm face), with a 5 cm bar to check the printer didn't shrink it.
- **Monster masks.** Pick any of the 30 monsters' heads and print it on A4 as a mask to wear: kid size (eye holes 5 cm apart) or grown-up size (6.3 cm), with a grey line to cut along, eye holes, two dots for elastic and the same 5 cm check bar.

And four witchy ones, under their own heading with a witch's hat:

- **Witch's cauldron.** Tap three things from the shelf into the pot (a frog, a bat wing, a spider, a star, some slime or a mushroom). Each one splashes in and turns the potion its colour. Then stir it round three times with a finger: the spoon follows it, the froth builds up, and a star lights up for each time round. On the third it bubbles over, and with a *poof* a monster climbs out wearing a witch's hat. The three things pick its head, body and legs, in any order, so the same three always make the same monster: 50 different recipes, plus six secret ones, where three of the same make a whole monster from the book. Then it's off to "Meet your monster" and My monsters like any other.
- **Potion shop.** The cauldron again, as a shop. A monster peeks in at the cottage window and asks for a potion in a speech bubble: two spiders and two mushrooms, say. Drop in just that, stir it round three times, and it drinks it up ("Yum! Thank you!"). The wrong potion goes yucky and the monster says what's wrong ("Oops! I didn't want a frog!"), then you have another go. Five customers and the shop closes. Easy asks for one kind of thing, Medium two, and Tricky shows a number by each thing instead of the pictures to count.
- **Wand spells.** Your finger is a magic wand. A monster in a witch's hat sits on the witch's table, and each spell is a dotted shape to trace: a circle makes it big, a wave makes it float, a zigzag makes it rainbow coloured, a spiral makes it spin and a star makes it sparkle. The dots light up gold as you cover them, and the spells stack, so by the end it's a very silly monster. Any direction counts and you can lift your finger part way; only scribbling all over makes a spell fizzle. Circles, waves, zigzags, spirals and stars are the shapes children practise before letters.
- **Broomstick ride.** The monster on your flip book, in a witch's hat, flies home to the witch's cottage across the night sky. It goes up and down to wherever your finger is, catches stars, bumps the odd bat (an "eek" and a wobble, nothing lost) and swoops past the moon. Gentle or Speedy. Nothing to lose; the stars are the score.

The plain link opens the town. The games page is `/#games`, and each game has its own link (`/#make`, `/#match`, `/#whack`, `/#bedtime`, `/#torch`, `/#cottage`, `/#pumpkin`, `/#masks`, `/#cauldron`, `/#potions`, `/#wand`, `/#broom`). Best scores are kept on the device.

### Keeping them safe, and 3D monsters

Everything lives on the phone, and a phone can be lost, wiped or replaced. So a family can link a phone to **a small private store of their own**. It's a separate Cloudflare Worker, in a private repo, that answers only under `/store/` on this site's own address.

- **Linking:** a grown-up opens `/#keep` on the child's phone. The phone makes its own key (the private half can't be read out of the browser) and shows **three monster faces**. The grown-up taps the same three on the store's grown-up page, signed in with a passkey.
- **Saving:** from then on, every change is copied to the store: the same contents as the Back up file.
- **A new phone:** linked to the same child, it brings everything back by itself.
- **3D monsters:** a linked phone also gets each monster **in 3D**. The first time a head, body and legs combination is saved, the phone draws the book monster and the store asks Google's Gemini image model to make it as a soft 3D toy, from that drawing and one example. The phone cuts the white background away, and that monster then waits at the gate and leans out of its window in 3D. Each combination is made once and shared by every linked phone, so there's nothing personal in it.

A phone that isn't linked never talks to the store at all.


The counting and letter games started here too, then outgrew the monster site and moved to their own: the **Learning Lab**, at [learn.mikeohalloran.au](https://learn.mikeohalloran.au/) ([learning-lab](https://github.com/mikeohallo/learning-lab)). Old `/#letters`, `/#count` and `/#quick` links go there.

The three sites sit behind one front door, [play.mikeohalloran.au](https://play.mikeohalloran.au/): Monster Lab (this one), Learning Lab, and Seek Lab, the sister seek-and-find book ([seek-book](https://github.com/mikeohallo/seek-book)). A "More to play" button at the bottom of each site goes back to it.

## How it's built

**It's one HTML file and about 190 images.** No framework, no build step, no accounts, no analytics. Hosting is Cloudflare Pages on the free plan, which comfortably covers the handful of families who have the book.

That was the main design decision. The obvious version of this site has user accounts, cloud saves and an API. For a thing used by a handful of families, each of those is a cost, a privacy question and something to maintain. So everything works on the phone alone, and the one backend (the private store above) is something a family opts into, with no accounts: a phone is approved by a grown-up's passkey, not signed in. Beyond that:

- **The monster is assembled in the browser.** The site holds 90 transparent strip images (30 heads, bodies and legs, about 3 MB in total), cut from the real print files so they match the book exactly. Three `<img>` tags stacked in a column are a monster.
- **The card is drawn in the browser** on a canvas: 1200 × 1600 px, with the same fonts and colours as the printed book. Saving it is just saving a PNG.
- **The library lives in `localStorage`.** Each saved monster is three codes, four answers and a date, a couple of hundred bytes. The card is redrawn from the strips every time, so nothing bulky is stored. The town is just a list of which monster lives on which plot. Backup and restore move the library and the town between devices as a small JSON file.
- **The town is one painted picture,** a toy-model valley made in Google AI Studio with its plots left empty. The page places everything on top, in units of that picture, and draws nearer things in front:

  - the cottages, one picture in six roof colours;
  - the monsters, which are their own three strip images, so they wave with no new art;
  - the signpost, whose arms are buttons.

  Each close-up is a painting of one area with its window cut out. The monster sits behind it, so it really leans out.
- **Privacy.** Answers, saved monsters and scores stay in this browser unless you export or share them, or a grown-up links the phone to the family's store. The display name is included in personalised links between the sites (a gift link like `?for=Max`, and "More to play" once a name is set), so the hosting service receives it when those links are opened. The page also loads its fonts from Google Fonts. The picture answers are read out by the device's own voice, and the page picks one that runs on the device where there is one, because on some computers the only voices are online ones. A phone linked to the family's store sends it the Back up contents, and, for each new head, body and legs combination, a drawing of the book monster for Gemini to make in 3D. A phone that isn't linked never talks to the store. (One more thing moves, once, in a browser set up for the Learning Lab's Letters game: the first time the Learning Lab opens there, this site hands the old saved Letters progress across in the part of the address after the `#`, which browsers don't send to a server.)
- **Not meant for search.** A `noindex` tag asks search engines not to list the site. It's for families with the book, who arrive by QR code, gift link or home-screen icon.

### Things that turned out to matter

- **A page turn, not a fade.** The first version faded between strips. Flipping a real strip in the book turns it over, so the site does the same: a 3D rotate on the strip, hinged at the coil. It's one CSS transform and it made the thing feel like the book.
- **White tummies.** Cutting the monsters out of the print files by colour left the white tummies transparent. The fix was to build a solid silhouette of each monster first, then use that as the alpha mask. Same trick for the printed cut lines that cross pale tummies at the joins.
- **iPhones delete site data.** Safari removes a site's saved data if you don't open it for seven days of Safari use. Adding the site to the Home Screen avoids that. It's why there's a backup button.
- **Nothing to type.** A young child can't type H12, but she can swipe. The codes are the parent's shortcut; the swipe is hers. The same went for the four questions: she couldn't fill them in, so a grown-up always had to. With pictures to tap, and every answer read out, she makes monsters on her own.
- **Flat monsters looked odd in a 3D house.** The book's monsters are flat paintings, and leaning out of a 3D cottage they looked like stickers. So they got bigger, with a soft shadow, and linked phones get each one made in 3D. Gemini keeps a book monster recognisable when it's given the monster itself, drawn from its strips, rather than a description of it.
- **Nothing to read, either.** Each tab has a picture above its label (a house for Town, a game controller for Play, a monster for Make, a heart for My monsters), the games page is a set of big pictures, and the town's signpost has a picture on each arm, so she can find a game herself. The address follows the tabs, so a reload keeps her where she was.
- **Forgiving shapes, but finished ones.** Wand spells doesn't mark a stroke the way a handwriting app would: any direction counts, lifting the finger is fine, a corner cut short fills in, and a spell only fizzles when most of what's been drawn is nowhere near the shape. The first version was forgiving in the wrong way, though. It lit every dot within a finger's reach, so where the star's lines cross, two lines lit most of the star and the spell finished halfway. Now a dot only lights when the finger travels along the shape to it (through a crossing it stays on the line it's following), and a spell finishes only when both ends are reached and most of it is lit, or for the circle and the star, whose ends meet, nearly all of it. The tests trace every shape steady and wobbly, both ways round, and check none finishes before 90% of the way.
- **Stirring, not a button.** The first cauldron had a "Stir the pot" button. Stirring it yourself is the fun part, so now the pot follows a finger round. It counts every bit of the way round in either direction, even back and forth, so a wobbly circle works, and stopping part way keeps what's been stirred.
- **One hat, 30 heads.** The witch's hat first sat at a fixed spot, which left it floating above short heads and sunk into tall ones. Now it looks for the top of each head in the middle (so horns, antennae and ears at the sides don't count) and sizes itself to the head's width there.
- **Sounds without sound files.** The boings, the snores and the lullaby are all made in the browser with the Web Audio API, so the games need nothing but the HTML file and the images. There's a mute button, and it's remembered.
- **Make first, then play.** The games page's first and biggest tile is Make a monster, showing whatever monster is on the flip book. Since the town became the front page, the monster waiting at the gate does the same job: an empty town shows a question mark asking her to make one, and a saved card offers "Find them a home", which goes straight to the town with that monster first in the queue.
- **A stencil has to be carvable.** A pumpkin face that looks fine on screen can fall apart under a knife. Every eye, nose and mouth combination (144 of them) is checked: teeth, fangs and tongues stay joined to the pumpkin, and no two holes come closer than 9 mm, even on the smallest stencil. The stencil also keeps each face the size it is on the pumpkin: the first version stretched every face to the chosen width, so a one-eyed "Ooh" face came out bigger than the page.

## What's in this repo

| Path | What it is |
|---|---|
| `index.html` | The whole site: markup, styles and script in one file |
| `tools/make_web_strips.py` | Cuts the 90 strip images and 30 face icons from the book's print pages |
| `tools/build_site.py` | Wraps the page for hosting and sets the generic title |
| `tools/test_site.py` | Drives the site in Chromium at phone size: flipping, swiping, codes, saving, deleting, backup, restore, no sideways scroll; any failed step or page error fails the run |
| `tools/test_match.py` | Plays the match game: a wrong pair flips back, a full game ends in a win, the best score sticks, every level fits a phone |
| `tools/test_links.py` | The tab bar (Town, Play, Make, My monsters) fits at 360–430 px; the plain link opens the town and `#games` the games page with Make a monster first; the `#make`, `#match`, `#whack`, `#bedtime` and `#monsters` links and gift links work; and the old Letters and Numbers links go to the Learning Lab |
| `tools/test_games.py` | Plays Whack-a-monster and Monster bedtime with the page clock fast-forwarded: a perfect round, an empty round, a sleepy monster on Hard, a full bedtime from tuck-in to Good morning |
| `tools/test_town.py` | The town at five screen sizes, from a folding phone's inner and outer screens to a laptop: every plot can be tapped; moving in, with the cottage in the monster's colour; the close-ups, in the right area and colour; turning the phone with a close-up open; folding it mid-move; a deleted monster's empty cottage; backup and restore of the town; long and odd names; a full valley; and the picture answers, with all 32 pictures loaded |
| `tools/test_keep.py` | Keeping monsters safe, against the private store run on the same machine with a pretend Gemini and a pretend passkey: an unlinked phone never calls the store; linking by three faces; saving every change; a new phone bringing the monsters, houses and 3D art back; the 3D monster at the gate and in the window; removing a phone. It needs the private store's repo beside this one, and says so and skips without it |
| `tools/test_spooky.py` | The Spooky and Witches games. Plays Torch hunt at every level in both rooms by moving the torch onto each monster (in the witch's cottage, holding it at the edge until the room slides along), checks the sliding with a mouse and a finger, the faces to find first, the giggle hints, that no two hiding places overlap, and the cottage at four screen sizes; brews in the Witch's cauldron: each splash colour, stirring with the mouse, a finger, either way round or the Space key (and that a tap isn't a stir), that the same three in any order make the same monster, that all 50 recipes make different monsters and the six secrets are whole ones, the hat on all 30 heads, emptying the pot or leaving part way through, Meet your monster and saving; and the Pumpkin face maker: changing parts, lighting it, saving the picture, measuring each printed stencil (12, 15 and 18 cm, and the 5 cm bar), and checking all 144 faces fit the page at every size; prints masks at both sizes and checks the eye-hole spacing, and that all 30 heads fit the page with the eye holes and elastic dots on the monster; serves five customers in the Potion shop (right and wrong potions, emptying the pot, a thousand orders at each level checked against its rules), casts all five wand spells with a wobbly mouse (half way and carrying on, the other way round, a scribble that fizzles, the Enter key) and checks no spell finishes before the end of its shape, or when she stops short, and flies the broomstick ride home (steering, a bat, every star in reach, both speeds, the keyboard) |
| `town/` | The town's pictures: the valley (two sizes), the cottage in six colours, the signpost, 30 close-ups (five areas, six colours) and 32 answer pictures |
| `docs/` | Screenshots |

The monster images aren't in the repo; they're the book. The town's pictures are, because they're the site's own. Nor is `site/app.html`, the working copy that `build_site.py` wraps into `index.html`, so that script won't run from a clean clone; `index.html` is its built result and is complete. The image tools and the tests are all here.

## Running it locally

Serve the page rather than opening the file directly. Browsers treat `file://` pages differently from one another (saving to the device and drawing the card can both behave differently or fail), and a local server gives reliable browser behaviour, the same as the real site.

```
python3 -m http.server 8000
```

Then open `http://localhost:8000`. Without the `strips/` and `faces/` folders you'll get the layout with empty frames, which is enough to see how it works.

## Credits

Monster art, the town and the answer pictures generated with Google AI Studio. Fonts: [Fredoka](https://fonts.google.com/specimen/Fredoka) and [Nunito](https://fonts.google.com/specimen/Nunito), both Open Font Licence. Site and tools written with Claude.

Made for my daughter.
