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

legacy = '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#FFFFFF" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:strokeLineCap="round" android:pathData="M54,35L54,43 M46,65L35,72 M62,65L73,72"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:pathData="M54,13 C60.075,13 65,17.925 65,24 C65,30.075 60.075,35 54,35 C47.925,35 43,30.075 43,24 C43,17.925 47.925,13 54,13 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#FF0000" android:strokeWidth="4" android:pathData="M54,43 C60.627,43 66,48.373 66,55 C66,61.627 60.627,67 54,67 C47.373,67 42,61.627 42,55 C42,48.373 47.373,43 54,43 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:pathData="M28,69 C33.523,69 38,73.477 38,79 C38,84.523 33.523,89 28,89 C22.477,89 18,84.523 18,79 C18,73.477 22.477,69 28,69 Z M80,69 C85.523,69 90,73.477 90,79 C90,84.523 85.523,89 80,89 C74.477,89 70,84.523 70,79 C70,73.477 74.477,69 80,69 Z"/>
</vector>\n'''

foreground = '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:strokeLineCap="round" android:pathData="M54,35L54,43 M46,65L35,72 M62,65L73,72"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:pathData="M54,13 C60.075,13 65,17.925 65,24 C65,30.075 60.075,35 54,35 C47.925,35 43,30.075 43,24 C43,17.925 47.925,13 54,13 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#FF0000" android:strokeWidth="4" android:pathData="M54,43 C60.627,43 66,48.373 66,55 C66,61.627 60.627,67 54,67 C47.373,67 42,61.627 42,55 C42,48.373 47.373,43 54,43 Z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#000000" android:strokeWidth="4" android:pathData="M28,69 C33.523,69 38,73.477 38,79 C38,84.523 33.523,89 28,89 C22.477,89 18,84.523 18,79 C18,73.477 22.477,69 28,69 Z M80,69 C85.523,69 90,73.477 90,79 C90,84.523 85.523,89 80,89 C74.477,89 70,84.523 70,79 C70,73.477 74.477,69 80,69 Z"/>
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

print('NEXUS launcher branding source: PASS')
