from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from U013 adapter 001, which itself derives from the validated U004 SHELL 004 runtime.
subprocess.run([
    sys.executable,
    str(repo / 'u013ux001' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Candidate identity.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared001"', 'applicationId = "nexus.android.u013.shared002"')
s = s.replace('versionCode = 46', 'versionCode = 47')
s = s.replace('versionName = "0.0.46-u013-android-ux-shared001"', 'versionName = "0.0.47-u013-android-ux-shared002-product"')
assert 'nexus.android.u013.shared002' in s
p.write_text(s)

# Product-first Android presentation layer.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()

# Remove the technical baseline string from the user-visible result footer.
s = s.replace(
    'android:text="BASELINE_UX_SHARED_001 · Le fournisseur LLM et les détails techniques restent accessibles depuis le menu ⋮."',
    'android:text="Le fournisseur LLM et les détails techniques restent accessibles depuis le menu ⋮."'
)

# Inject a real product home over the inherited runtime surface.
needle = '''        </LinearLayout>\n    </FrameLayout>\n'''
home = '''        </LinearLayout>\n\n        <ScrollView\n            android:id="@+id/productHome"\n            android:layout_width="match_parent"\n            android:layout_height="match_parent"\n            android:background="#F7F7F8"\n            android:fillViewport="true">\n\n            <LinearLayout\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:orientation="vertical"\n                android:paddingStart="22dp"\n                android:paddingEnd="22dp"\n                android:paddingTop="28dp"\n                android:paddingBottom="32dp">\n\n                <TextView\n                    android:layout_width="wrap_content"\n                    android:layout_height="wrap_content"\n                    android:text="NEXUS"\n                    android:textColor="#202123"\n                    android:textSize="30sp"\n                    android:textStyle="bold" />\n\n                <TextView\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="28dp"\n                    android:text="Que voulez-vous faire avec NEXUS ?"\n                    android:textColor="#202123"\n                    android:textSize="24sp"\n                    android:textStyle="bold" />\n\n                <EditText\n                    android:id="@+id/productPrompt"\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="20dp"\n                    android:minHeight="92dp"\n                    android:gravity="top|start"\n                    android:padding="16dp"\n                    android:background="#FFFFFF"\n                    android:hint="Décrivez la situation, la question ou l’affirmation…"\n                    android:inputType="textMultiLine"\n                    android:textColor="#202123"\n                    android:textColorHint="#7A7B80"\n                    android:textSize="16sp" />\n\n                <Button\n                    android:id="@+id/productAnalyse"\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="16dp"\n                    android:text="Analyser une situation"\n                    android:textAllCaps="false" />\n\n                <Button\n                    android:id="@+id/productFactCheck"\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="8dp"\n                    android:text="Vérifier une affirmation"\n                    android:textAllCaps="false" />\n\n                <TextView\n                    android:layout_width="wrap_content"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="30dp"\n                    android:text="Navigation"\n                    android:textColor="#6F7075"\n                    android:textSize="13sp"\n                    android:textStyle="bold" />\n\n                <LinearLayout\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="10dp"\n                    android:orientation="vertical"\n                    android:padding="2dp">\n\n                    <Button\n                        android:id="@+id/navNew"\n                        android:layout_width="match_parent"\n                        android:layout_height="wrap_content"\n                        android:text="+ Nouveau"\n                        android:textAllCaps="false" />\n\n                    <Button\n                        android:id="@+id/navWorks"\n                        android:layout_width="match_parent"\n                        android:layout_height="wrap_content"\n                        android:layout_marginTop="6dp"\n                        android:text="Mes travaux"\n                        android:textAllCaps="false" />\n\n                    <Button\n                        android:id="@+id/navRelations"\n                        android:layout_width="match_parent"\n                        android:layout_height="wrap_content"\n                        android:layout_marginTop="6dp"\n                        android:text="Relations"\n                        android:textAllCaps="false" />\n\n                    <Button\n                        android:id="@+id/navJourney"\n                        android:layout_width="match_parent"\n                        android:layout_height="wrap_content"\n                        android:layout_marginTop="6dp"\n                        android:text="Information Journey"\n                        android:textAllCaps="false" />\n                </LinearLayout>\n\n                <TextView\n                    android:id="@+id/productState"\n                    android:layout_width="match_parent"\n                    android:layout_height="wrap_content"\n                    android:layout_marginTop="26dp"\n                    android:text="Prêt"\n                    android:textColor="#6F7075"\n                    android:textSize="14sp" />\n            </LinearLayout>\n        </ScrollView>\n    </FrameLayout>\n'''
assert s.count(needle) == 1, 'frame injection point mismatch'
s = s.replace(needle, home)
p.write_text(s)

# Wire product home without altering provider transport semantics.
p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

# Imports for product controls if not already present.
if 'import android.widget.EditText\n' not in s:
    s = s.replace('import android.widget.Button\n', 'import android.widget.Button\nimport android.widget.EditText\n')
if 'import android.widget.ScrollView\n' not in s:
    s = s.replace('import android.widget.PopupMenu\n', 'import android.widget.PopupMenu\nimport android.widget.ScrollView\n')

s = s.replace(
    '    private lateinit var resultSummary: TextView\n',
    '    private lateinit var resultSummary: TextView\n    private lateinit var productHome: ScrollView\n    private lateinit var productPrompt: EditText\n    private lateinit var productState: TextView\n    private var productRunRequested = false\n'
)

bind_old = '''        resultPanel = findViewById(R.id.resultPanel)\n        resultSummary = findViewById(R.id.resultSummary)\n'''
bind_new = '''        resultPanel = findViewById(R.id.resultPanel)\n        resultSummary = findViewById(R.id.resultSummary)\n        productHome = findViewById(R.id.productHome)\n        productPrompt = findViewById(R.id.productPrompt)\n        productState = findViewById(R.id.productState)\n\n        findViewById<Button>(R.id.productAnalyse).setOnClickListener {\n            productRunRequested = true\n            productState.text = "Analyse · résultat NEXUS"\n            productHome.visibility = View.GONE\n            if (resultPanel.visibility == View.VISIBLE) {\n                showNexusResult()\n            } else {\n                webView.visibility = View.VISIBLE\n            }\n        }\n        findViewById<Button>(R.id.productFactCheck).setOnClickListener {\n            productState.text = "Fact Check · raccordement moteur à valider"\n        }\n        findViewById<Button>(R.id.navNew).setOnClickListener {\n            productPrompt.setText("")\n            productState.text = "Nouveau travail"\n        }\n        findViewById<Button>(R.id.navWorks).setOnClickListener { productState.text = "Mes travaux · vue produit" }\n        findViewById<Button>(R.id.navRelations).setOnClickListener { productState.text = "Relations · vue produit" }\n        findViewById<Button>(R.id.navJourney).setOnClickListener { productState.text = "Information Journey · vue produit" }\n'''
assert s.count(bind_old) == 1, 'binding point mismatch'
s = s.replace(bind_old, bind_new)

old_show = '''    private fun showNexusResult() {\n        webView.visibility = View.GONE\n        resultPanel.visibility = View.VISIBLE\n    }\n'''
new_show = '''    private fun showNexusResult() {\n        webView.visibility = View.GONE\n        resultPanel.visibility = View.VISIBLE\n        if (productRunRequested) productHome.visibility = View.GONE\n    }\n'''
assert s.count(old_show) == 1, 'showNexusResult mismatch'
s = s.replace(old_show, new_show)

# Auto-completion must not replace the product home before the user asks to see a result.
old_validated = '''        showNexusResult()\n    }\n\n    private fun showNexusResult()'''
new_validated = '''        if (productRunRequested) showNexusResult() else {\n            resultPanel.visibility = View.GONE\n            productHome.visibility = View.VISIBLE\n            productState.text = "Prêt · fournisseur disponible en arrière-plan"\n        }\n    }\n\n    private fun showNexusResult()'''
assert s.count(old_validated) == 1, 'validated result transition mismatch'
s = s.replace(old_validated, new_validated)

for token in ['productHome', 'productAnalyse', 'productFactCheck', 'navWorks', 'navRelations', 'navJourney', 'productRunRequested']:
    assert token in s, token
p.write_text(s)

# Update lock.
lock = work / 'U013_BASELINE_LOCK.txt'
lock.write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'DESIGN_BASELINE_DRIVE=19cINcqyLSyoshqeRh-SeOlKoTaFoXFOrs31Hu--J54g\n'
    'RUNTIME_BASELINE=U004_ANDROID_UX_SHELL_004\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_002\n'
    'NON_MODIFIED_ORIGINALS=transport,auth,bridge,result_pack,fail_closed\n'
    'PRODUCT_HOME=IMPLEMENTED\n'
    'PRODUCT_NAVIGATION=IMPLEMENTED\n'
    'FACTCHECK_RUNTIME=NOT_CLAIMED\n'
)
