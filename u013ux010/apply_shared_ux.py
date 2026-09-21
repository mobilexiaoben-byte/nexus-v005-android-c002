from pathlib import Path
import re
import sys

root=Path(sys.argv[1]).resolve()
repo=Path(sys.argv[2]).resolve()

adapter_src=repo/"u013ux010"/"AndroidPlatformAdapter.kt"
adapter_dst=root/"app/src/main/java/nexus/android/c002/AndroidPlatformAdapter.kt"
adapter_dst.write_text(adapter_src.read_text())

main=root/"app/src/main/java/nexus/android/c002/MainActivity.kt"
s=main.read_text()

m=re.search(r'class\s+MainActivity\s*:[^{]+\{\n',s)
assert m, "MainActivity class declaration not found"
insert_at=m.end()
s=s[:insert_at]+"    private lateinit var u013PlatformAdapter: AndroidPlatformAdapter\n"+s[insert_at:]

content_anchor="        setContentView(R.layout.activity_main)\n"
assert s.count(content_anchor)==1, "setContentView anchor mismatch"
install=content_anchor+"""        u013PlatformAdapter = AndroidPlatformAdapter(this) { destination ->
            when (destination) {
                "home" -> {
                    productHome.visibility = android.view.View.VISIBLE
                    resultPanel.visibility = android.view.View.GONE
                    webView.visibility = android.view.View.GONE
                    productState.text = "NEXUS · prêt"
                }
                "fact" -> findViewById<android.widget.Button>(R.id.productFactCheck).performClick()
                "works" -> productState.text = "Mes travaux · espace local"
                "maps" -> productState.text = "Cartes · disponibles lorsque les signaux sont qualifiés"
                "subjects" -> productState.text = "Sujets persistants · espace local"
                "analyses" -> productState.text = "Analyses locales · espace local"
                "archives" -> productState.text = "Archives · espace local"
            }
        }
        u013PlatformAdapter.install()
"""
s=s.replace(content_anchor,install,1)
main.write_text(s)

gradle=root/"app/build.gradle.kts"
g=gradle.read_text()
assert "versionCode = 73" in g
assert 'versionName = "0.0.73-v007-golden-recovery001"' in g
g=g.replace("versionCode = 73","versionCode = 74",1)
g=g.replace('versionName = "0.0.73-v007-golden-recovery001"','versionName = "0.0.74-u013-shared-ux-v31-golden010"',1)
gradle.write_text(g)

(root/"U013_COMPOSITION_LOCK.txt").write_text(
"WORKSTREAM_ID=U-013\n"
"DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n"
"DESIGN_BASELINE_DRIVE=1oh2GOi2wuZF9EI8f3m-7w70hJ73dMBsP7lm5hPEyC3Y\n"
"DESIGN_REFERENCE_DRIVE_ID=1uOcutK4Pc3D19--ytix7qtADQqsh-H6W\n"
"PLATFORM=ANDROID\n"
"PLATFORM_ADAPTER=U013_ANDROID_PLATFORM_ADAPTER_010\n"
"RUNTIME_BASELINE=V007_GOLDEN_RECOVERY_001\n"
"RUNTIME_BASE_SHA=a3b001589608355b3b6914df348364f56f057576\n"
"M024=UNCHANGED\n"
"PROVIDER_ADAPTERS=UNCHANGED_GOLDEN_RECOVERY\n"
"FACTCHECK_O24=UNCHANGED\n"
"MONITORING=UNCHANGED\n"
"RESULT_PACK=UNCHANGED\n"
"CANONICAL_WRITE=false\n"
"RELEASE=none\n"
)
