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
m = manifest.read_text(encoding='utf-8')
assert 'android:icon="@mipmap/ic_launcher"' in m
assert 'android:roundIcon="@mipmap/ic_launcher"' in m
expected = {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
sig = b'\x89PNG\r\n\x1a\n'
for density, size in expected.items():
    p = root / 'app/src/main/res' / f'mipmap-{density}' / 'ic_launcher.png'
    data = p.read_bytes()
    assert data.startswith(sig)
    assert struct.unpack('>II', data[16:24]) == (size, size)
for rel in (
    'app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml',
    'app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml',
    'app/src/main/res/drawable/nexus_launcher_foreground.xml',
):
    assert not (root / rel).exists(), rel
print('PROVIDER_RESUME_021_CANONICAL_BRANDING_POSTCONDITION=PASS v4_raster_no_adaptive')
