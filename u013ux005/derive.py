from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from SHARED-004, validated on device for auth return + native NEXUS result.
subprocess.run([
    sys.executable,
    str(repo / 'u013ux004' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Candidate identity.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared004"', 'applicationId = "nexus.android.u013.shared005"')
s = s.replace('versionCode = 49', 'versionCode = 50')
s = s.replace('versionName = "0.0.49-u013-android-ux-shared004-auth-state"', 'versionName = "0.0.50-u013-android-ux-shared005-llm-first"')
assert 'nexus.android.u013.shared005' in s
p.write_text(s)

# Product surface: make LLM choice explicit and visible before work actions.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()
anchor = '''                <TextView
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:layout_marginTop="28dp"
                    android:text="Que voulez-vous faire avec NEXUS ?"
                    android:textColor="#202123"
                    android:textSize="24sp"
                    android:textStyle="bold" />
'''
insert = anchor + '''
                <Button
                    android:id="@+id/productLlmChooser"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:layout_marginTop="18dp"
                    android:text="Choisir son LLM"
                    android:textAllCaps="false" />
'''
assert s.count(anchor) == 1, 'LLM chooser layout anchor mismatch'
s = s.replace(anchor, insert)
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

# State: no provider is considered selected by the product until the user explicitly chooses one.
s = s.replace(
    '    private var productRunRequested = false\n',
    '    private var productRunRequested = false\n    private var providerSelectionRequested = false\n    private var selectedProvider: String? = null\n    private lateinit var productLlmChooser: Button\n'
)

# Bind visible chooser and make it the explicit entry point to provider authentication.
bind_anchor = '''        productHome = findViewById(R.id.productHome)
        productPrompt = findViewById(R.id.productPrompt)
        productState = findViewById(R.id.productState)
'''
bind_new = bind_anchor + '''        productLlmChooser = findViewById(R.id.productLlmChooser)
        productLlmChooser.setOnClickListener { anchorView -> showLlmChooser(anchorView) }
'''
assert s.count(bind_anchor) == 1, 'LLM chooser binding anchor mismatch'
s = s.replace(bind_anchor, bind_new)

# Analyse now requires an explicit LLM selection. Session expiry still falls back to visible login.
old_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {
            productRunRequested = true
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
                productState.text = "Connexion à ChatGPT requise"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
            } else {
                productState.text = "Analyse en cours…"
                webView.visibility = View.GONE
                if (resultPanel.visibility == View.VISIBLE) {
                    showNexusResult()
                } else {
                    productHome.visibility = View.VISIBLE
                }
            }
        }
'''
new_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {
            if (selectedProvider == null) {
                productState.text = "Choisissez d’abord un LLM"
                return@setOnClickListener
            }
            productRunRequested = true
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
                productState.text = "Session expirée · reconnectez ${selectedProvider}"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
            } else {
                productState.text = "Analyse en cours…"
                webView.visibility = View.GONE
                if (resultPanel.visibility == View.VISIBLE) {
                    showNexusResult()
                } else {
                    productHome.visibility = View.VISIBLE
                }
            }
        }
'''
assert s.count(old_analyse) == 1, 'Analyse handler mismatch in SHARED-004'
s = s.replace(old_analyse, new_analyse)

# Fact Check follows the same product rule: choose provider first. Runtime engine remains explicitly unclaimed.
old_fact = '''        findViewById<Button>(R.id.productFactCheck).setOnClickListener {
            productState.text = "Fact Check · raccordement moteur à valider"
        }
'''
new_fact = '''        findViewById<Button>(R.id.productFactCheck).setOnClickListener {
            if (selectedProvider == null) {
                productState.text = "Choisissez d’abord un LLM"
            } else if (currentHeadline.startsWith("AUTH REQUIRED")) {
                productState.text = "Session expirée · reconnectez ${selectedProvider}"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
            } else {
                productState.text = "Fact Check · raccordement moteur à valider"
            }
        }
'''
assert s.count(old_fact) == 1, 'Fact Check handler mismatch'
s = s.replace(old_fact, new_fact)

# Header menu: expose the same LLM chooser as a first-class menu option.
old_menu = '''        val menuButton: Button = findViewById(R.id.nexusMenu)
        menuButton.setOnClickListener { anchorView ->
            val popup = PopupMenu(this, anchorView)
            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")
            if (proofStopped) {
                popup.menu.add(if (resultPanel.visibility == View.VISIBLE) "Voir la réponse ChatGPT" else "Afficher le résultat NEXUS")
            }
            popup.setOnMenuItemClickListener { item ->
                when (item.title.toString()) {
                    "Détails techniques", "Masquer les détails techniques" -> {
                        diagnosticExpanded = !diagnosticExpanded
                        renderStatus()
                    }
                    "Voir la réponse ChatGPT" -> showProviderResponse()
                    "Afficher le résultat NEXUS" -> showNexusResult()
                }
                true
            }
            popup.show()
        }
'''
new_menu = '''        val menuButton: Button = findViewById(R.id.nexusMenu)
        menuButton.setOnClickListener { anchorView ->
            val popup = PopupMenu(this, anchorView)
            popup.menu.add("Choisir son LLM")
            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")
            if (proofStopped) {
                popup.menu.add(if (resultPanel.visibility == View.VISIBLE) "Voir la réponse ChatGPT" else "Afficher le résultat NEXUS")
            }
            popup.setOnMenuItemClickListener { item ->
                when (item.title.toString()) {
                    "Choisir son LLM" -> showLlmChooser(anchorView)
                    "Détails techniques", "Masquer les détails techniques" -> {
                        diagnosticExpanded = !diagnosticExpanded
                        renderStatus()
                    }
                    "Voir la réponse ChatGPT" -> showProviderResponse()
                    "Afficher le résultat NEXUS" -> showNexusResult()
                }
                true
            }
            popup.show()
        }
'''
assert s.count(old_menu) == 1, 'Header menu block mismatch'
s = s.replace(old_menu, new_menu)

# Provider selector. Only ChatGPT transport exists in this Android candidate; other validated NEXUS providers
# are shown as product choices but cannot be claimed operational in this APK until their Android adapters are wired.
method_anchor = '''    private fun syncProductAuthSurface() {
'''
methods = '''    private fun showLlmChooser(anchorView: View) {
        val popup = PopupMenu(this, anchorView)
        popup.menu.add("ChatGPT")
        popup.menu.add("Claude · adaptateur Android à raccorder")
        popup.menu.add("Gemini · adaptateur Android à raccorder")
        popup.menu.add("Z.ai · adaptateur Android à raccorder")
        popup.setOnMenuItemClickListener { item ->
            when (item.title.toString()) {
                "ChatGPT" -> selectChatGptProvider()
                else -> productState.text = item.title.toString()
            }
            true
        }
        popup.show()
    }

    private fun selectChatGptProvider() {
        selectedProvider = "ChatGPT"
        productLlmChooser.text = "LLM · ChatGPT"
        productRunRequested = false
        if (currentHeadline.startsWith("AUTH REQUIRED")) {
            providerSelectionRequested = true
            productState.text = "Connexion à ChatGPT…"
            productHome.visibility = View.GONE
            resultPanel.visibility = View.GONE
            webView.visibility = View.VISIBLE
        } else {
            providerSelectionRequested = false
            webView.visibility = View.GONE
            productHome.visibility = View.VISIBLE
            productState.text = "ChatGPT connecté · prêt"
        }
    }

'''
assert s.count(method_anchor) == 1, 'syncProductAuthSurface method anchor mismatch'
s = s.replace(method_anchor, methods + method_anchor)

# Auth state synchronization: provider-selection login returns to NEXUS even when no Analyse job was requested.
old_auth_required = '''            currentHeadline.startsWith("AUTH REQUIRED") -> {
                if (productRunRequested) {
                    productState.text = "Connexion à ChatGPT requise"
                    productHome.visibility = View.GONE
                    resultPanel.visibility = View.GONE
                    webView.visibility = View.VISIBLE
                }
            }
'''
new_auth_required = '''            currentHeadline.startsWith("AUTH REQUIRED") -> {
                if (providerSelectionRequested || productRunRequested) {
                    productState.text = if (providerSelectionRequested) "Connexion à ChatGPT…" else "Connexion à ChatGPT requise"
                    productHome.visibility = View.GONE
                    resultPanel.visibility = View.GONE
                    webView.visibility = View.VISIBLE
                }
            }
'''
assert s.count(old_auth_required) == 1, 'AUTH_REQUIRED sync block mismatch'
s = s.replace(old_auth_required, new_auth_required)

old_auth_ok = '''            currentHeadline.startsWith("DESCRIBE PASS") ||
            currentHeadline.startsWith("ACK PASS") ||
            currentHeadline.startsWith("EXECUTION PROOF") -> {
                // Auth is proven: provider disappears automatically and NEXUS resumes.
                webView.visibility = View.GONE
                if (productRunRequested && !proofStopped) {
                    resultPanel.visibility = View.GONE
                    productHome.visibility = View.VISIBLE
                    productState.text = "Analyse en cours…"
                }
            }
'''
new_auth_ok = '''            currentHeadline.startsWith("DESCRIBE PASS") ||
            currentHeadline.startsWith("ACK PASS") ||
            currentHeadline.startsWith("EXECUTION PROOF") -> {
                // Auth is proven: provider disappears automatically and NEXUS resumes.
                webView.visibility = View.GONE
                if (providerSelectionRequested) {
                    providerSelectionRequested = false
                    resultPanel.visibility = View.GONE
                    productHome.visibility = View.VISIBLE
                    productLlmChooser.text = "LLM · ChatGPT"
                    productState.text = "ChatGPT connecté · prêt"
                } else if (productRunRequested && !proofStopped) {
                    resultPanel.visibility = View.GONE
                    productHome.visibility = View.VISIBLE
                    productState.text = "Analyse en cours…"
                }
            }
'''
assert s.count(old_auth_ok) == 1, 'AUTH_OK sync block mismatch'
s = s.replace(old_auth_ok, new_auth_ok)

for token in [
    'productLlmChooser',
    'Choisir son LLM',
    'selectedProvider: String? = null',
    'providerSelectionRequested',
    'selectChatGptProvider()',
    'ChatGPT connecté · prêt',
    'Choisissez d’abord un LLM',
    'Claude · adaptateur Android à raccorder',
    'Gemini · adaptateur Android à raccorder',
    'Z.ai · adaptateur Android à raccorder',
]:
    assert token in s, token
p.write_text(s)

lock = work / 'U013_BASELINE_LOCK.txt'
lock.write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'DESIGN_BASELINE_DRIVE=19cINcqyLSyoshqeRh-SeOlKoTaFoXFOrs31Hu--J54g\n'
    'RUNTIME_BASELINE=U004_ANDROID_UX_SHELL_004\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_005\n'
    'NON_MODIFIED_ORIGINALS=transport,auth_detection,bridge,result_pack,fail_closed\n'
    'LLM_SELECTION=EXPLICIT_BEFORE_ANALYSE_OR_FACTCHECK\n'
    'LLM_CHOOSER=VISIBLE_HOME_AND_HEADER_MENU\n'
    'CHATGPT_SELECTION=OPEN_PROVIDER_IF_AUTH_REQUIRED\n'
    'AUTH_OK_RETURN=NEXUS_AUTOMATIC\n'
    'ANALYSE_PROVIDER_VISIBILITY=HIDDEN_UNLESS_SESSION_EXPIRED\n'
    'FACTCHECK_PROVIDER_VISIBILITY=HIDDEN_UNLESS_SESSION_EXPIRED\n'
    'ACTIVE_ANDROID_PROVIDER_ADAPTER=ChatGPT_ONLY\n'
    'OTHER_PROVIDER_CHOICES=VISIBLE_NOT_OPERATIONALLY_CLAIMED\n'
    'NORMAL_RESULT_SURFACE=NEXUS_NATIVE\n'
    'RESULT_RENDER_FIELD=result_pack.answer\n'
    'FACTCHECK_RUNTIME=NOT_CLAIMED\n'
)
