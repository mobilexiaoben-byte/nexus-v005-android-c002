from pathlib import Path
import struct
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Functional derivation remains owned by 021.
subprocess.run([
    'python3',
    str(repo / 'providerresume021' / 'derive.py'),
    str(repo),
    str(root),
], check=True)

# Branding is a mandatory, independent post-condition of every derived source.
subprocess.run([
    'python3',
    str(repo / 'branding' / 'ensure_launcher.py'),
    str(root),
], check=True)

manifest = root / 'app/src/main/AndroidManifest.xml'
fg = root / 'app/src/main/res/drawable/nexus_launcher_foreground.xml'
adaptive = root / 'app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml'
adaptive_round = root / 'app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml'

m = manifest.read_text(encoding='utf-8')
text = fg.read_text(encoding='utf-8')
assert 'android:icon="@mipmap/ic_launcher"' in m
assert 'android:roundIcon="@mipmap/ic_launcher_round"' in m
assert 'android:width="108dp"' in text
assert 'android:height="108dp"' in text
assert 'android:viewportWidth="108"' in text
assert 'android:viewportHeight="108"' in text
assert 'M54,26.195' in text
assert 'M34.976,67.171' in text
assert 'M73.024,67.171' in text
assert 'android:strokeWidth="4.39"' in text
assert 'android:scaleX=' not in text
assert 'android:scaleY=' not in text
assert adaptive.is_file()
assert adaptive_round.is_file()

expected = {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
sig = b'\x89PNG\r\n\x1a\n'
for density, size in expected.items():
    for name in ('ic_launcher.png', 'ic_launcher_round.png'):
        p = root / 'app/src/main/res' / f'mipmap-{density}' / name
        data = p.read_bytes()
        assert data.startswith(sig)
        assert struct.unpack('>II', data[16:24]) == (size, size)

print('PROVIDER_RESUME_021_CANONICAL_BRANDING_POSTCONDITION=PASS v5_android_official_adaptive_safe60')
