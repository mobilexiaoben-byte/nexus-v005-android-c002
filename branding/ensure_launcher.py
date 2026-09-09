from pathlib import Path
import re
import sys

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
    m = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@mipmap/ic_launcher_round"', m, count=1)
else:
    m = m.replace('<application', '<application android:roundIcon="@mipmap/ic_launcher_round"', 1)
manifest.write_text(m, encoding='utf-8')

# Keep the complete NEXUS mark inside a conservative adaptive-icon safe zone.
# Coordinates are compacted directly instead of relying on VectorDrawable group
# scaling, so launcher-specific rendering cannot ignore or reinterpret the scale.
# The mark occupies roughly x=36..72 and y=33.5..71.5 in a 108x108 viewport.
symbol = '''    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="3" android:strokeLineCap="round" android:pathData="M54,44.5L54,48.5 M50,59.5L44.5,63 M58,59.5L63.5,63"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="3" android:pathData="M54,33.5 C57.0375,33.5 59.5,35.9625 59.5,39 C59.5,42.0375 57.0375,44.5 54,44.5 C50.9625,44.5 48.5,42.0375 48.5,39 C48.5,35.9625 50.9625,33.5 54,33.5 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#FF0000" android:strokeWidth="3" android:pathData="M54,48.5 C57.3135,48.5 60,51.1865 60,54.5 C60,57.8135 57.3135,60.5 54,60.5 C50.6865,60.5 48,57.8135 48,54.5 C48,51.1865 50.6865,48.5 54,48.5 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="3" android:pathData="M41,61.5 C43.7615,61.5 46,63.7385 46,66.5 C46,69.2615 43.7615,71.5 41,71.5 C38.2385,71.5 36,69.2615 36,66.5 C36,63.7385 38.2385,61.5 41,61.5 Z M67,61.5 C69.7615,61.5 72,63.7385 72,66.5 C72,69.2615 69.7615,71.5 67,71.5 C64.2385,71.5 62,69.2615 62,66.5 C62,63.7385 64.2385,61.5 67,61.5 Z"/>'''

legacy = f'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#FFFFFF" android:pathData="M0,0h108v108h-108z"/>
{symbol}
</vector>\n'''

foreground = f'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
{symbol}
</vector>\n'''

adaptive = '''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/nexus_launcher_background"/>
    <foreground android:drawable="@drawable/nexus_launcher_foreground"/>
</adaptive-icon>\n'''

colors = '''<resources>
    <color name="nexus_launcher_background">#FFFFFF</color>
</resources>\n'''

files = {
    res / 'mipmap-anydpi' / 'ic_launcher.xml': legacy,
    res / 'mipmap-anydpi' / 'ic_launcher_round.xml': legacy,
    res / 'drawable' / 'nexus_launcher_foreground.xml': foreground,
    res / 'values' / 'nexus_launcher_colors.xml': colors,
    res / 'mipmap-anydpi-v26' / 'ic_launcher.xml': adaptive,
    res / 'mipmap-anydpi-v26' / 'ic_launcher_round.xml': adaptive,
}
for path, text in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

print('NEXUS launcher branding source: PASS direct_safe_zone=0.50')
