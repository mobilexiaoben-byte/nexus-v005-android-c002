from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Runtime/provider lineage first; U-013 then adds only the platform UX layer.
exec((repo / "reconcile019" / "provider_runtime_019.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile019" / "provider_runtime_019.py"),
    "sys": sys,
})

adapter_src = repo / "u013ux010" / "AndroidPlatformAdapter.kt"
adapter_dst = root / "app/src/main/java/nexus/android/c002/AndroidPlatformAdapter.kt"
adapter_dst.write_text(adapter_src.read_text())

main = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main.read_text()

state_anchor = "    private var activeFactCheckJobId: String? = null\n"
if state_anchor not in s:
    state_anchor = "class MainActivity : AppCompatActivity() {\n"
    state_insert = state_anchor + "    private lateinit var platformAdapter: AndroidPlatformAdapter\n"
else:
    state_insert = state_anchor + "    private lateinit var platformAdapter: AndroidPlatformAdapter\n"
assert s.count(state_anchor) == 1, "platform adapter state anchor mismatch"
s = s.replace(state_anchor, state_insert, 1)

install_anchor = "        setContentView(R.layout.activity_main)\n"
assert s.count(install_anchor) == 1, "setContentView anchor mismatch"
install = install_anchor + """        platformAdapter = AndroidPlatformAdapter(this) { destination ->
            when (destination) {
                "home" -> {
                    productPrompt.setText("")
                    productHome.visibility = View.VISIBLE
                    resultPanel.visibility = View.GONE
                    webView.visibility = View.GONE
                    productState.text = "NEXUS · prêt"
                }
                "fact" -> findViewById<Button>(R.id.productFactCheck).performClick()
                "works" -> productState.text = "Mes travaux · espace local"
                "maps" -> productState.text = "Cartes · disponibles lorsque les signaux sont qualifiés"
                "subjects" -> productState.text = "Sujets persistants · espace local"
                "analyses" -> productState.text = "Analyses locales · espace local"
                "archives" -> productState.text = "Archives · espace local"
            }
        }
        platformAdapter.install()
"""
s = s.replace(install_anchor, install, 1)

main.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
if "versionCode = 72" in g:
    g = g.replace("versionCode = 72", "versionCode = 73", 1)
if 'versionName = "0.0.72-v007-m024-u013-provider-runtime019-gemini-capture-fix"' in g:
    g = g.replace(
        'versionName = "0.0.72-v007-m024-u013-provider-runtime019-gemini-capture-fix"',
        'versionName = "0.0.73-u013-shared-ux-v31-baseline010"',
        1
    )
gradle.write_text(g)

(root / "U013_COMPOSITION_LOCK.txt").write_text(
    "WORKSTREAM_ID=U-013\n"
    "DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n"
    "DESIGN_REFERENCE_DRIVE_ID=1uOcutK4Pc3D19--ytix7qtADQqsh-H6W\n"
    "PLATFORM=ANDROID\n"
    "PLATFORM_ADAPTER_ID=U013_ANDROID_PLATFORM_ADAPTER_010\n"
    "RUNTIME_LINEAGE=V007_PROVIDER_RUNTIME_019\n"
    "M024=UNCHANGED\n"
    "FACTCHECK_O24=UNCHANGED\n"
    "PROVIDER_ADAPTERS=UNCHANGED\n"
    "MONITORING=UNCHANGED\n"
    "RESULT_PACK=UNCHANGED\n"
    "CANONICAL_WRITE=false\n"
    "RELEASE=none\n"
)
