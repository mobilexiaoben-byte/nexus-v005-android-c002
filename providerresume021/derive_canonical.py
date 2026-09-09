from pathlib import Path
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

fg = root / 'app/src/main/res/drawable/nexus_launcher_foreground.xml'
manifest = root / 'app/src/main/AndroidManifest.xml'
text = fg.read_text(encoding='utf-8')
m = manifest.read_text(encoding='utf-8')
assert 'M54,33.5' in text and 'M41,61.5' in text
assert 'android:scaleX=' not in text
assert 'android:icon="@mipmap/ic_launcher"' in m
assert 'android:roundIcon="@mipmap/ic_launcher_round"' in m
print('PROVIDER_RESUME_021_CANONICAL_BRANDING_POSTCONDITION=PASS')
