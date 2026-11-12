"""Build assets/atlas.png, assets/walls.jpg and inline the atlas index into index.html.

    python3 tools/build_assets.py

Source art: design/figure-1..6.jpg (the figures of the Game Asset Design Document).
"""
import json, os, re, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import ROOT, fox_sheet, hazard_sheet, load

# scale that brings every sheet to "standing fox = 128px tall"
SHEET_SCALE = {2: 0.5, 3: 0.744, 4: 0.744, 5: 1.0}

# name: (figure, index, anchor kind, flip)
FOX = {}
def seq(prefix, fig, idxs, kind, flip=False):
    for i, ix in enumerate(idxs):
        FOX[f'{prefix}{i}'] = (fig, ix, kind, flip)

seq('idleA', 3, range(0, 6), 'ground')
seq('idleB', 3, range(6, 12), 'ground')
seq('wait', 3, range(12, 19), 'ground')
seq('walk', 5, range(0, 8), 'ground')
seq('run', 5, range(8, 16), 'ground')
seq('shrink', 5, [17, 18], 'ground')
seq('grow', 5, [20, 21], 'ground')
seq('grab', 4, [0, 1], 'wall', True)      # drawn with the wall on the left -> flip
seq('regrab', 4, [21], 'wall')
seq('slide', 4, [4, 5], 'wall')
seq('dive', 4, [6, 7], 'air')
seq('kick', 4, [12], 'air')
seq('rise', 4, [13, 14], 'air')
seq('apex', 4, [15, 16], 'air')
seq('fall', 4, [17, 18], 'air')
seq('touchdown', 4, [20], 'ground')
seq('hitA', 2, [3], 'ground')
seq('hitB', 2, [4], 'air')
seq('ko', 2, [5], 'flat')

HAZ_SCALE = 0.6
# name: (index, crop box in sprite px or None, anchor in cropped sprite px or None, blanking fn or None)
def _no_streak(a):          # pendulum: drop the motion streak beside the chain
    a[:122, 100:, 3] = 0
def _no_beam(a):            # ceiling turret: drop the painted laser beam (the game draws its own)
    a[118:, :, 3] = 0
    a[20:, 140:, 3] = 0
HAZ = {
    'spikeWall': (4, None, None, None),
    'spikeFloor': (1, None, None, None),
    'saw': (5, None, None, None),
    'sawArm': (6, (0, 0, 262, 156), (85, 85), None),
    'pendulum': (7, None, (8, 3), _no_streak),
    'crusher': (13, None, None, None),
    'laser': (9, (0, 0, 74, 109), None, None),
    'cturret': (10, None, (100, 2), _no_beam),
    'gateL': (11, (0, 0, 62, 156), None, None),
    'gateR': (11, (248, 0, 310, 156), None, None),
    'barricade': (12, None, None, None),
    'acid': (14, None, None, None),
    'fireball': (16, None, None, None),
    'icicles': (3, None, None, None),
    'icicle': (3, (8, 22, 62, 151), None, None),
}

# order must match ZONE_INFO in index.html
WALLS = {'ruin': (168, 346), 'iron': (806, 1014), 'ice': (470, 681), 'crystal': (1140, 1348)}
WALL_W, WALL_H = 208, 156


def anchor(img, kind):
    a = np.asarray(img)[..., 3] > 60
    h, w = a.shape
    ys, xs = np.nonzero(a)
    if kind == 'ground':
        top = a[: int(h * 0.45)]
        return float(np.nonzero(top)[1].mean()), float(h)
    if kind == 'flat':
        return w / 2, float(h)
    if kind == 'wall':
        return float(w), h / 2
    return float(xs.mean()), float(ys.mean())


def main():
    sheets = {n: fox_sheet(n)[0] for n in (2, 3, 4, 5)}
    sprites = {}
    for name, (fig, ix, kind, flip) in FOX.items():
        im = sheets[fig][ix]
        s = SHEET_SCALE[fig]
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        sprites[name] = (im, anchor(im, kind))
    hero = sheets[2][0]
    hero = hero.resize((round(hero.width * 0.9), round(hero.height * 0.9)), Image.LANCZOS)
    sprites['hero'] = (hero, anchor(hero, 'ground'))

    hz = hazard_sheet()[0]
    for name, (ix, crop, anc, blank) in HAZ.items():
        im = hz[ix][1]
        if crop:
            im = im.crop(crop)
        if blank:
            arr = np.asarray(im).copy(); blank(arr); im = Image.fromarray(arr, 'RGBA')
        im = im.resize((round(im.width * HAZ_SCALE), round(im.height * HAZ_SCALE)), Image.LANCZOS)
        sprites[name] = (im, (anc[0] * HAZ_SCALE, anc[1] * HAZ_SCALE) if anc else (im.width / 2, im.height / 2))

    # shelf packing
    W, pad = 1536, 2
    items = sorted(sprites.items(), key=lambda kv: -kv[1][0].height)
    x = y = shelf = 0
    pos = {}
    for name, (im, _) in items:
        if x + im.width + pad > W:
            x, y, shelf = 0, y + shelf + pad, 0
        pos[name] = (x, y)
        x += im.width + pad
        shelf = max(shelf, im.height)
    H = y + shelf
    atlas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    index = {}
    for name, (im, (ax, ay)) in sprites.items():
        px, py = pos[name]
        atlas.paste(im, (px, py))
        index[name] = [px, py, im.width, im.height, round(ax, 1), round(ay, 1)]
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    arr = np.asarray(atlas).copy()
    arr[arr[..., 3] == 0] = 0                    # no hidden colour under transparent pixels
    Image.fromarray(arr, 'RGBA').save(os.path.join(ROOT, 'assets', 'atlas.png'), optimize=True)

    fig5 = load(5).astype(np.uint8)
    walls = Image.new('RGB', (WALL_W * len(WALLS), WALL_H))
    for i, (name, (x0, x1)) in enumerate(WALLS.items()):
        panel = Image.fromarray(fig5[574:730, x0:x1]).resize((WALL_W, WALL_H), Image.LANCZOS)
        walls.paste(panel, (i * WALL_W, 0))
    walls.save(os.path.join(ROOT, 'assets', 'walls.jpg'), quality=90)

    # inline the index into index.html between the ATLAS markers
    path = os.path.join(ROOT, 'index.html')
    html = open(path).read()
    blob = 'const ATLAS = ' + json.dumps(index, separators=(',', ':')) + ';'
    html, n = re.subn(r'/\*ATLAS-BEGIN\*/.*?/\*ATLAS-END\*/',
                      lambda m: '/*ATLAS-BEGIN*/' + blob + '/*ATLAS-END*/', html, flags=re.S)
    if n:
        open(path, 'w').write(html)
    print(f'atlas {W}x{H}, {len(index)} sprites, index inlined: {bool(n)}')


if __name__ == '__main__':
    main()
