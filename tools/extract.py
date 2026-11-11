"""Cut sprites out of the design-document figures.

Usage: python3 tools/extract.py           -> writes debug contact sheets to tools/debug/
       (imported by build_assets.py for the real atlas build)
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = lambda n: os.path.join(ROOT, 'design', f'figure-{n}.jpg')


def load(n):
    return np.asarray(Image.open(FIG(n)).convert('RGB')).astype(np.int32)


def background_mask(im, lo, hi, sat=16, enclosed=False):
    """Neutral-grey pixels in [lo, hi] connected to the image border
    (or, with enclosed=True, any such patch bigger than a speck)."""
    mx, mn = im.max(2), im.min(2)
    grey = im.sum(2) / 3
    cand = ((mx - mn) < sat) & (grey >= lo) & (grey <= hi)
    lab, n = ndimage.label(cand)
    if enclosed:
        sizes = ndimage.sum(cand, lab, range(1, n + 1))
        return np.isin(lab, 1 + np.flatnonzero(sizes > 30))
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border != 0]
    return np.isin(lab, border)


def components(im, bg, min_area, need_orange=None, fill=True):
    """Return list of (bbox, mask) for foreground blobs, in reading order."""
    fg = ~bg
    lab, n = ndimage.label(fg, structure=np.ones((3, 3)))
    out = []
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    orange = (r > 180) & (g > 50) & (g < 170) & (b < 110)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab[sl] == i
        area = int(m.sum())
        if area < min_area:
            continue
        if need_orange is not None and (orange[sl] & m).sum() / area < need_orange:
            continue
        if fill:
            m = ndimage.binary_fill_holes(m)
        y0, x0 = sl[0].start, sl[1].start
        out.append(((x0, y0, sl[1].stop, sl[0].stop), m))
    # reading order: bucket into rows by vertical centre
    out.sort(key=lambda c: (c[0][1] + c[0][3]) / 2)
    rows, cur = [], []
    for c in out:
        cy = (c[0][1] + c[0][3]) / 2
        if cur and cy - np.mean([(k[0][1] + k[0][3]) / 2 for k in cur]) > 90:
            rows.append(cur); cur = []
        cur.append(c)
    if cur:
        rows.append(cur)
    res = []
    for row in rows:
        res.extend(sorted(row, key=lambda c: c[0][0]))
    return res


def cut(im, bbox, mask):
    """RGBA sprite with a slightly feathered edge."""
    x0, y0, x1, y1 = bbox
    rgb = im[y0:y1, x0:x1].astype(np.uint8)
    m = ndimage.binary_erosion(mask, iterations=1)
    a = ndimage.gaussian_filter(m.astype(np.float32), 0.7)
    a = np.clip(a * 1.15, 0, 1) * mask
    rgba = np.dstack([rgb, (a * 255).astype(np.uint8)])
    return Image.fromarray(rgba, 'RGBA')


def fox_sheet(n):
    im = load(n)
    bg = background_mask(im, 140, 222, enclosed=True)
    return [cut(im, b, m) for b, m in components(im, bg, 2200, need_orange=0.2, fill=False)], im


def hazard_sheet():
    im = load(6)
    bg = background_mask(im, 112, 146, sat=12)
    comps = components(im, bg, 1500)
    return [(b, cut(im, b, m)) for b, m in comps], im


def contact(sprites, path, cols=8, cell=220):
    rows = (len(sprites) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * cell, rows * cell), (40, 20, 70, 255))
    d = ImageDraw.Draw(sheet)
    for i, s in enumerate(sprites):
        t = s.copy(); t.thumbnail((cell - 10, cell - 30))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.alpha_composite(t, (x + 5, y + 25))
        d.text((x + 5, y + 5), f'{i}  {s.width}x{s.height}', fill=(255, 255, 0, 255))
    sheet.convert('RGB').save(path, quality=85)


if __name__ == '__main__':
    dbg = os.path.join(ROOT, 'tools', 'debug'); os.makedirs(dbg, exist_ok=True)
    for n in range(1, 6):
        s, _ = fox_sheet(n)
        print('figure', n, len(s))
        contact(s, os.path.join(dbg, f'fox{n}.jpg'))
    hz, _ = hazard_sheet()
    print('hazards', len(hz), [b for b, _ in hz])
    contact([s for _, s in hz], os.path.join(dbg, 'haz.jpg'), cols=6)
