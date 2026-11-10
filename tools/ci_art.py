"""Stand-in art for running the tests without the book's own pictures (CI, or a fresh clone).

The monster art (faces/, strips/) is the book itself and stays out of this repo, but the tests need a picture at every
path the page loads. This makes plain numbered shapes at the book's real sizes (the strip geometry the page uses:
925 px wide; heads 600, bodies 330, legs 555 px tall), so layout, loading and every game still run. Never upload these.

    python3 tools/ci_art.py [SITE]     (SITE defaults to the repo root; existing art is never overwritten)
"""
import colorsys, sys
from pathlib import Path
from PIL import Image, ImageDraw

SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
N = 30
HEIGHTS = {'H': 600, 'B': 330, 'L': 555}
WIDTH, FACE = 925, 400


def colour(n):
    r, g, b = colorsys.hsv_to_rgb((n * 0.137) % 1, 0.55, 0.9)
    return int(r * 255), int(g * 255), int(b * 255), 255


def save(img, path):
    if path.exists():
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, 'WEBP', quality=60)
    return 1


made = 0
for n in range(1, N + 1):
    face = Image.new('RGBA', (FACE, FACE), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    d.ellipse((20, 20, FACE - 20, FACE - 20), fill=colour(n), outline=(58, 40, 82, 255), width=8)
    d.text((FACE // 2 - 20, FACE // 2 - 10), f'{n:02d}', fill=(58, 40, 82, 255))
    made += save(face, SITE / 'faces' / f'F{n:02d}.webp')
    for part, h in HEIGHTS.items():
        strip = Image.new('RGBA', (WIDTH, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(strip)
        d.rounded_rectangle((40, 10, WIDTH - 40, h - 10), radius=60, fill=colour(n), outline=(58, 40, 82, 255), width=8)
        d.text((WIDTH // 2 - 20, h // 2 - 10), f'{part}{n:02d}', fill=(58, 40, 82, 255))
        made += save(strip, SITE / 'strips' / f'{part}{n:02d}.webp')
print(f'stand-in art: {made} files made in {SITE} (faces/, strips/)')
