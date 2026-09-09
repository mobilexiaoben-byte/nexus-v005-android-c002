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

# Android Developers adaptive-icon contract used here:
# - every adaptive layer is 108x108 dp
# - logo is centered and must be 48..66 dp
# - outer 18 dp on every side is reserved for OEM masking/effects
# NEXUS uses a 60 dp high mark (about 57 dp wide including strokes), centered.
# Ref: https://developer.android.com/develop/ui/compose/system/icon_design_adaptive

m = manifest.read_text(encoding='utf-8')
if 'android:icon=' in m:
    m = re.sub(r'android:icon="[^"]+"', 'android:icon="@mipmap/ic_launcher"', m, count=1)
else:
    m = m.replace('<application', '<application android:icon="@mipmap/ic_launcher"', 1)
if 'android:roundIcon=' in m:
    m = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@mipmap/ic_launcher_round"', m, count=1)
else:
    m = m.replace('<application', '<application android:roundIcon="@mipmap/ic_launcher_round"', 1)
manifest.write_text(m, encoding='utf-8')

# Remove only stale launcher resources before regenerating the canonical set.
for rel in (
    'mipmap-anydpi/ic_launcher.xml',
    'mipmap-anydpi/ic_launcher_round.xml',
    'drawable/nexus_launcher_foreground.xml',
    'values/nexus_launcher_colors.xml',
    'mipmap-anydpi-v26/ic_launcher.xml',
    'mipmap-anydpi-v26/ic_launcher_round.xml',
):
    p = res / rel
    if p.exists():
        p.unlink()
for d in res.glob('mipmap-*'):
    if d.is_dir():
        for name in ('ic_launcher.png', 'ic_launcher_round.png'):
            p = d / name
            if p.exists():
                p.unlink()

# Canonical 60 dp NEXUS logo geometry in the 108 dp adaptive-icon canvas.
# Including strokes, the visible mark is approximately x=25.46..82.54,
# y=24..84, therefore entirely inside the official 66x66 safe zone.
STROKE = 4.390
LINES = [
    (54.000, 42.293, 54.000, 48.146),
    (48.146, 64.244, 40.098, 69.366),
    (59.854, 64.244, 67.902, 69.366),
]
RINGS = [
    (54.000, 34.244, 8.049, '#000000'),
    (54.000, 56.927, 8.780, '#FF0000'),
    (34.976, 74.488, 7.317, '#000000'),
    (73.024, 74.488, 7.317, '#000000'),
]

def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')

def circle_path(cx, cy, r):
    # Four cubic Beziers using the standard kappa approximation.
    k = r * 0.5522847498307936
    return (
        f'M{fmt(cx)},{fmt(cy-r)} '
        f'C{fmt(cx+k)},{fmt(cy-r)} {fmt(cx+r)},{fmt(cy-k)} {fmt(cx+r)},{fmt(cy)} '
        f'C{fmt(cx+r)},{fmt(cy+k)} {fmt(cx+k)},{fmt(cy+r)} {fmt(cx)},{fmt(cy+r)} '
        f'C{fmt(cx-k)},{fmt(cy+r)} {fmt(cx-r)},{fmt(cy+k)} {fmt(cx-r)},{fmt(cy)} '
        f'C{fmt(cx-r)},{fmt(cy-k)} {fmt(cx-k)},{fmt(cy-r)} {fmt(cx)},{fmt(cy-r)} Z'
    )

paths = []
for ax, ay, bx, by in LINES:
    paths.append(
        f'    <path android:fillColor="@android:color/transparent" '
        f'android:strokeColor="#000000" android:strokeWidth="{fmt(STROKE)}" '
        f'android:strokeLineCap="round" '
        f'android:pathData="M{fmt(ax)},{fmt(ay)}L{fmt(bx)},{fmt(by)}"/>'
    )
for cx, cy, r, color in RINGS:
    paths.append(
        f'    <path android:fillColor="@android:color/transparent" '
        f'android:strokeColor="{color}" android:strokeWidth="{fmt(STROKE)}" '
        f'android:pathData="{circle_path(cx, cy, r)}"/>'
    )
symbol = '\n'.join(paths)

foreground = f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
{symbol}
</vector>
'''

adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/nexus_launcher_background"/>
    <foreground android:drawable="@drawable/nexus_launcher_foreground"/>
</adaptive-icon>
'''

colors = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="nexus_launcher_background">#FFFFFF</color>
</resources>
'''

files = {
    res / 'drawable' / 'nexus_launcher_foreground.xml': foreground,
    res / 'values' / 'nexus_launcher_colors.xml': colors,
    res / 'mipmap-anydpi-v26' / 'ic_launcher.xml': adaptive,
    res / 'mipmap-anydpi-v26' / 'ic_launcher_round.xml': adaptive,
}
for path, text in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

# Generate density-specific legacy PNGs, as Image Asset Studio does for
# pre-API-26 launchers. The same official 60 dp geometry is rendered on white.
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

    stroke = STROKE / 108.0 * n

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

    for ax, ay, bx, by in LINES:
        line(ax, ay, bx, by, black)
    for cx, cy, r, color in RINGS:
        ring(cx, cy, r, red if color == '#FF0000' else black)

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

    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(bytes(out), 9))
        + chunk(b'IEND', b'')
    )

sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for density, size in sizes.items():
    d = res / f'mipmap-{density}'
    d.mkdir(parents=True, exist_ok=True)
    png = render(size)
    (d / 'ic_launcher.png').write_bytes(png)
    (d / 'ic_launcher_round.png').write_bytes(png)

print('NEXUS launcher branding source: PASS v5_android_official_adaptive_safe60')
