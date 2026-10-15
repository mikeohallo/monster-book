"""Make the website's strip images from the final book pages.

For each monster page: build a solid silhouette of the whole monster (so white tummies stay
opaque), drop the colour dots, codes and cut lines, then cut it into head / body / legs at the
book's cut lines and save each as a transparent WebP. Also writes monsters.json for the site.

    python3 make_web_strips.py PAGES_DIR OUT_DIR
PAGES_DIR holds p03.png ... p32.png (pages 3-32 of the book's print PDF = monsters 01-30).
monsters_src.json beside this script lists each monster's code, colour and texture.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

PPI = 300
def mm(v): return v / 25.4 * PPI

CUT1, CUT2 = 120.0, 186.0
X0, X1 = 20.0, 205.0            # page columns kept (mm)
PX_MM = 5                        # web resolution: 5 px per mm -> 925 px wide strips

NAMES = {'01': 'Unicorn', '02': 'Dinosaur', '03': 'Ballerina', '04': 'Penguin', '05': 'Octopus',
         '06': 'Banana', '07': 'Mermaid', '08': 'Owl', '09': 'Yeti', '10': 'Frog', '11': 'Bumblebee',
         '12': 'Pumpkin', '13': 'Flamingo', '14': 'Bat', '15': 'Shark', '16': 'Forest Troll',
         '17': 'Chick', '18': 'Fox', '19': 'Axolotl', '20': 'Chameleon', '21': 'Snow Monster',
         '22': 'Parrot', '23': 'Pineapple', '24': 'Dragon', '25': 'Cupcake', '26': 'Alien',
         '27': 'Jellyfish', '28': 'Cactus', '29': 'Snail', '30': 'Firebird'}
DOTS = {'pink': [236, 106, 168], 'purple': [168, 128, 214], 'blue': [84, 166, 226],
        'green': [104, 178, 66], 'yellow': [242, 200, 40], 'orange': [244, 136, 44]}


def silhouette(a):
    sat = a.max(axis=2) - a.min(axis=2)
    m = (sat > 22) | (a.min(axis=2) < 120)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    coms = ndi.center_of_mass(m, lab, range(1, n + 1))
    for i, (s, (cy, cx)) in enumerate(zip(sizes, coms), start=1):
        if s < 2500 and cx > mm(185):          # colour dots by the strip codes
            m[lab == i] = False
    m = ndi.binary_closing(m, iterations=3)
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    return np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 1500])


def main(pages, out):
    pages, out = Path(pages), Path(out)
    (out / 'strips').mkdir(parents=True, exist_ok=True)
    meta = json.load(open(Path(__file__).with_name('monsters_src.json')))
    info = {m['code']: m for m in meta['monsters'] if not m.get('test')}
    c1, c2 = int(round(mm(CUT1))), int(round(mm(CUT2)))
    x0, x1 = int(round(mm(X0))), int(round(mm(X1)))
    W = int(round((X1 - X0) * PX_MM))
    parts = {'H': (0, c1, CUT1), 'B': (c1, c2, CUT2 - CUT1), 'L': (c2, 3508, 297 - CUT2)}
    monsters, total = [], 0
    for k in range(1, 31):
        code = f'{k:02d}'
        a = np.asarray(Image.open(pages / f'p{k + 2:02d}.png').convert('RGB'))
        sil = silhouette(a.astype(np.int16))
        # the printed cut line also crosses pale tummies at the joins: paint it out there
        a = a.copy()
        for c in (c1, c2):
            band = a[c - 4: c + 5].astype(np.int16)
            sat = band.max(axis=2) - band.min(axis=2)
            grey = (sat < 14) & (band.max(axis=2) > 110) & (band.max(axis=2) < 205) & sil[c - 4: c + 5]
            if grey.any():
                above, below = a[c - 7].astype(np.int16), a[c + 7].astype(np.int16)
                for r in range(9):
                    t = r / 8
                    row = ((1 - t) * above + t * below).astype(np.uint8)
                    a[c - 4 + r][grey[r]] = row[grey[r]]
        alpha = (ndi.gaussian_filter(sil.astype(np.float32), 0.8) * 255).clip(0, 255).astype(np.uint8)
        rgba = np.dstack([a, alpha])
        for p, (r0, r1, h_mm) in parts.items():
            tile = Image.fromarray(rgba[r0:r1, x0:x1], 'RGBA')
            tile = tile.resize((W, int(round(h_mm * PX_MM))), Image.LANCZOS)
            f = out / 'strips' / f'{p}{code}.webp'
            tile.save(f, 'WEBP', quality=84, method=6)
            total += f.stat().st_size
        m = info[code]
        monsters.append({'code': code, 'name': NAMES[code], 'colour': m['colour'],
                         'texture': m['texture'], 'dot': DOTS[m['colour']]})
        print(code, NAMES[code])
    geometry = {'pxPerMm': PX_MM, 'width': W,
                'heights': {p: int(round(h * PX_MM)) for p, (_, _, h) in parts.items()}}
    json.dump({'geometry': geometry, 'monsters': monsters}, open(out / 'monsters.json', 'w'), indent=1)
    print(f'{total / 1e6:.1f} MB of strips; geometry {geometry}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
