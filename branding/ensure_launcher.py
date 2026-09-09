from pathlib import Path
import math
import re
import struct
import sys
import zlib

work = Path(sys.argv[1]).resolve()
manifest = work / 'app/src/main/AndroidManifest.xml'
res = work / 'app/src/main/res'

if not manifest.is_file():
    raise SystemExit(f'missing manifest: {manifest}')

m = manifest.read_text(encoding='utf-8')
if 'android:icon=' in m:
    m = re.sub(r'android:icon="[^"]+"', 'android:icon="@mipmap/ic_launcher"', m, count=1)
else:
    m = m.replace('<application', '<application android:icon="@mipmap/ic_launcher"', 1)
if 'android:roundIcon=' in m:
    m = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@mipmap/ic_launcher"', m, count=1)
else:
    m = m.replace('<application', '<application android:roundIcon="@mipmap/ic_launcher"', 1)
manifest.write_text(m, encoding='utf-8')

# V4: padded legacy raster icons only. No adaptive foreground/mask path.
for rel in (
    'mipmap-anydpi/ic_launcher.xml',
    'mipmap-anydpi/ic_launcher_round.xml',
    'mipmap-anydpi-v26/ic_launcher.xml',
    'mipmap-anydpi-v26/ic_launcher_round.xml',
    'drawable/nexus_launcher_foreground.xml',
    'values/nexus_launcher_colors.xml',
):
    p = res / rel
    if p.exists():
        p.unlink()

for d in res.glob('mipmap-*'):
    if d.is_dir():
        for name in ('ic_launcher.png', 'ic_launcher_round.png', 'ic_launcher.xml', 'ic_launcher_round.xml'):
            p = d / name
            if p.exists():
                p.unlink()

def point_segment_distance(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    vv = vx * vx + vy * vy
    if vv == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / vv))
    cx, cy = ax + t * vx, ay + t * vy
    return math.hypot(px - cx, py - cy)

def render(size):
    ss = 4
    n = size * ss
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (255, 0, 0)
    pix = [white] * (n * n)

    def P(x, y):
        return x / 108.0 * n, y / 108.0 * n

    stroke = 3.0 / 108.0 * n

    def ring(cx, cy, r, color):
        cx, cy = P(cx, cy)
        rr = r / 108.0 * n
        half = stroke / 2.0
        xmin = max(0, int(cx - rr - half - 1))
        xmax = min(n - 1, int(cx + rr + half + 1))
        ymin = max(0, int(cy - rr - half - 1))
        ymax = min(n - 1, int(cy + rr + half + 1))
        for y in range(ymin, ymax + 1):
            for x in range(xmin, xmax + 1):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if abs(d - rr) <= half:
                    pix[y * n + x] = color

    def line(ax, ay, bx, by, color):
        ax, ay = P(ax, ay)
        bx, by = P(bx, by)
        half = stroke / 2.0
        xmin = max(0, int(min(ax, bx) - half - 1))
        xmax = min(n - 1, int(max(ax, bx) + half + 1))
        ymin = max(0, int(min(ay, by) - half - 1))
        ymax = min(n - 1, int(max(ay, by) + half + 1))
        for y in range(ymin, ymax + 1):
            for x in range(xmin, xmax + 1):
                if point_segment_distance(x + 0.5, y + 0.5, ax, ay, bx, by) <= half:
                    pix[y * n + x] = color

    line(54, 44.5, 54, 48.5, black)
    line(50, 59.5, 44.5, 63, black)
    line(58, 59.5, 63.5, 63, black)
    ring(54, 39, 5.5, black)
    ring(54, 54.5, 6, red)
    ring(41, 66.5, 5, black)
    ring(67, 66.5, 5, black)

    out = bytearray()
    for y in range(size):
        out.append(0)
        for x in range(size):
            rs = gs = bs = 0
            for yy in range(ss):
                for xx in range(ss):
                    r, g, b = pix[(y * ss + yy) * n + (x * ss + xx)]
                    rs += r; gs += g; bs += b
            div = ss * ss
            out.extend((rs // div, gs // div, bs // div))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    raw = bytes(out)
    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 9))
        + chunk(b'IEND', b'')
    )

sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for density, size in sizes.items():
    d = res / f'mipmap-{density}'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'ic_launcher.png').write_bytes(render(size))

print('NEXUS launcher branding source: PASS v4_legacy_raster_safe50 no_adaptive_mask')
