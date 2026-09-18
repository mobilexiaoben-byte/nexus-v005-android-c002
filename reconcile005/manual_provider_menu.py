from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

subprocess.run([
    sys.executable,
    str(repo / 'reconcile004' / 'add_gemini.py'),
    str(root),
    str(repo),
], check=True)

p = root / "app/src/main/res/layout/activity_main.xml"
s = p.read_text()
s = s.replace(
    '<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"\n    android:layout_width="match_parent"',
    '<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"\n    android:id="@+id/rootShell"\n    android:fitsSystemWindows="true"\n    android:layout_width="match_parent"',
    1
)
old_header = '''    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingStart="16dp"
        android:paddingEnd="8dp"
        android:background="#FFFFFF">
'''
new_header = '''    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="68dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingStart="18dp"
        android:paddingEnd="12dp"
        android:paddingTop="6dp"
        android:paddingBottom="6dp"
        android:background="#FFFFFF">
'''
assert old_header in s, "header layout anchor missing"
s = s.replace(old_header, new_header, 1)
old_button = '''        <Button
            android:id="@+id/nexusMenu"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="@android:color/transparent"
            android:text="⋮"
            android:textColor="#202123"
            android:textSize="24sp"
            android:contentDescription="Menu NEXUS" />
'''
new_button = '''        <Button
            android:id="@+id/nexusMenu"
            android:layout_width="52dp"
            android:layout_height="52dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:padding="0dp"
            android:background="@drawable/nexus_menu_button"
            android:text="⋮"
            android:textAllCaps="false"
            android:textColor="#202123"
            android:textSize="30sp"
            android:gravity="center"
            android:contentDescription="Menu NEXUS" />
'''
assert old_button in s, "nexusMenu layout anchor missing"
s = s.replace(old_button, new_button, 1)
p.write_text(s)

drawable = root / "app/src/main/res/drawable/nexus_menu_button.xml"
drawable.parent.mkdir(parents=True, exist_ok=True)
drawable.write_text('''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#F1F1F1" />
    <stroke android:width="1dp" android:color="#E2E2E2" />
    <corners android:radius="26dp" />
</shape>
''')

p = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = p.read_text()
state_anchor = '    private var selectedProvider: String? = null\n    private lateinit var productLlmChooser: Button\n'
state_new = '''    private var selectedProvider: String? = null
    private var selectedProviderOrigin: String? = null
    private var providerConfirmedByUser = false
    private val manualProviderConfirmationMode = true
    private lateinit var providerBadge: TextView
    private lateinit var productLlmChooser: Button
'''
assert state_anchor in s, "provider state anchor missing"
s = s.replace(state_anchor, state_new, 1)

bind_anchor = '''        productHome = findViewById(R.id.productHome)
        productPrompt = findViewById(R.id.productPrompt)
        productState = findViewById(R.id.productState)
        productLlmChooser = findViewById(R.id.productLlmChooser)
'''
bind_new = '''        productHome = findViewById(R.id.productHome)
        productPrompt = findViewById(R.id.productPrompt)
        productState = findViewById(R.id.productState)
        providerBadge = findViewById(R.id.providerBadge)
        providerBadge.text = "LLM"
        productLlmChooser = findViewById(R.id.productLlmChooser)
'''
assert bind_anchor in s, "product bind anchor missing"
s = s.replace(bind_anchor, bind_new, 1)

start = s.index('        val menuButton: Button = findViewById(R.id.nexusMenu)')
end_marker = '            popup.show()\n        }\n'
end = s.index(end_marker, start) + len(end_marker)
new_menu = '''        val menuButton: Button = findViewById(R.id.nexusMenu)
        menuButton.setOnClickListener { anchorView ->
            val popup = PopupMenu(this, anchorView)
            popup.menu.add("Choisir son LLM")
            selectedProvider?.let { provider ->
                val providerMenu = popup.menu.addSubMenu(provider)
                providerMenu.add("Connecté")
                providerMenu.add("Ouvrir la page")
            }
            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")
            if (proofStopped) {
                popup.menu.add(if (resultPanel.visibility == View.VISIBLE) "Voir la réponse ChatGPT" else "Afficher le résultat NEXUS")
            }
            popup.setOnMenuItemClickListener { item ->
                when (item.title.toString()) {
                    "Choisir son LLM" -> showLlmChooser(anchorView)
                    "Connecté" -> confirmSelectedProviderConnected()
                    "Ouvrir la page" -> openSelectedProviderPage()
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
s = s[:start] + new_menu + s[end:]

method_start = s.index('    private fun showLlmChooser(anchorView: View) {')
method_end = s.index('    private fun syncProductAuthSurface() {', method_start)
manual_methods = '''    private fun showLlmChooser(anchorView: View) {
        val popup = PopupMenu(this, anchorView)
        listOf("ChatGPT", "Gemini", "Claude", "Z.ai", "Grok").forEach { popup.menu.add(it) }
        popup.setOnMenuItemClickListener { item ->
            when (item.title.toString()) {
                "ChatGPT" -> selectProviderManually("ChatGPT", "https://chatgpt.com/")
                "Gemini" -> selectProviderManually("Gemini", "https://gemini.google.com/")
                "Claude" -> selectProviderManually("Claude", "https://claude.ai/")
                "Z.ai" -> selectProviderManually("Z.ai", "https://chat.z.ai/")
                "Grok" -> selectProviderManually("Grok", "https://grok.com/")
            }
            true
        }
        popup.show()
    }

    private fun selectProviderManually(provider: String, origin: String) {
        selectedProvider = provider
        selectedProviderOrigin = origin
        providerConfirmedByUser = false
        productRunRequested = false
        providerSelectionRequested = true
        productLlmChooser.text = "LLM · $provider"
        providerBadge.text = provider
        productState.text = "$provider sélectionné · connectez-vous puis confirmez via ⋮ → $provider → Connecté"
        productHome.visibility = View.GONE
        resultPanel.visibility = View.GONE
        webView.visibility = View.VISIBLE
        webView.stopLoading()
        webView.loadUrl(origin)
        recordDiagnostic("PROVIDER_NAVIGATION", origin, "MANUAL_PROVIDER_SELECTION")
    }

    private fun openSelectedProviderPage() {
        val provider = selectedProvider ?: run {
            productState.text = "Choisissez d’abord un LLM"
            return
        }
        val origin = selectedProviderOrigin ?: return
        productState.text = "$provider · page fournisseur"
        productHome.visibility = View.GONE
        resultPanel.visibility = View.GONE
        webView.visibility = View.VISIBLE
        webView.stopLoading()
        webView.loadUrl(origin)
        recordDiagnostic("PROVIDER_NAVIGATION", origin, "MANUAL_PROVIDER_REOPEN")
    }

    private fun confirmSelectedProviderConnected() {
        val provider = selectedProvider ?: run {
            productState.text = "Choisissez d’abord un LLM"
            return
        }
        providerConfirmedByUser = true
        providerSelectionRequested = false
        webView.visibility = View.GONE
        resultPanel.visibility = View.GONE
        productHome.visibility = View.VISIBLE
        productLlmChooser.text = "LLM · $provider"
        providerBadge.text = "$provider ✓"
        productState.text = "$provider · connecté (confirmé par l’utilisateur)"
        recordDiagnostic("PROVIDER_CONFIRMATION", selectedProviderOrigin ?: "", "USER_CONFIRMED_CONNECTED")
    }

'''
s = s[:method_start] + manual_methods + s[method_end:]
sync_anchor = '    private fun syncProductAuthSurface() {\n'
assert sync_anchor in s, "syncProductAuthSurface anchor missing"
s = s.replace(sync_anchor, sync_anchor + '        if (manualProviderConfirmationMode) return\n', 1)

p.write_text(s)

p = root / "app/build.gradle.kts"
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.m024.u013.reconcile004gemini"', 'applicationId = "nexus.android.v007.m024.u013.manualprovider005"')
s = s.replace('versionCode = 58', 'versionCode = 59')
s = s.replace('versionName = "0.0.58-v007-m024-u013-authfix2-reconcile004-gemini"', 'versionName = "0.0.59-v007-m024-u013-manual-provider-menu005"')
assert 'nexus.android.v007.m024.u013.manualprovider005' in s
p.write_text(s)

p = root / "app/src/main/assets/nexus/gemini_provider_c002.js"
s = p.read_text()
s = s.replace('  publishStatus();\n  setInterval(publishStatus,3000);\n  const mo=new MutationObserver(()=>{ clearTimeout(mo._t); mo._t=setTimeout(publishStatus,350); });\n  mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true});\n',
              '  // Manual connection mode: no DOM-driven auth polling.\n')
p.write_text(s)

lock = root / "RECONCILIATION_LOCK.txt"
base = lock.read_text()
lock.write_text(base +
    'PROVIDER_CONNECTION_MODE=MANUAL_USER_CONFIRMATION\n'
    'PROVIDER_DOM_AUTH_INFERENCE=DISABLED_FOR_PRODUCT_STATE\n'
    'PROVIDER_MENU=TOP_RIGHT_VISIBLE_SAFE_INSET\n'
    'PROVIDER_MENU_FLOW=CHOOSE_LLM__OPEN_HOME__USER_LOGIN__MENU_PROVIDER_CONNECTED\n'
    'PROVIDER_SELECTION_LIST=ChatGPT,Gemini,Claude,Z.ai,Grok\n'
    'PROVIDER_CONFIRMATION_AUTHORITY=USER\n'
    'BRIDGE_AUTHORITY=TECHNICAL_EXECUTION_ONLY\n'
)

main = (root / "app/src/main/java/nexus/android/c002/MainActivity.kt").read_text()
layout = (root / "app/src/main/res/layout/activity_main.xml").read_text()
adapter = (root / "app/src/main/assets/nexus/gemini_provider_c002.js").read_text()
for token in [
    'manualProviderConfirmationMode = true',
    'confirmSelectedProviderConnected()',
    'selectProviderManually("ChatGPT", "https://chatgpt.com/")',
    'selectProviderManually("Gemini", "https://gemini.google.com/")',
    'selectProviderManually("Claude", "https://claude.ai/")',
    'selectProviderManually("Z.ai", "https://chat.z.ai/")',
    'selectProviderManually("Grok", "https://grok.com/")',
    'providerMenu.add("Connecté")',
    'connectez-vous puis confirmez via ⋮',
    'USER_CONFIRMED_CONNECTED',
    'if (manualProviderConfirmationMode) return',
]:
    assert token in main, token
for token in ['android:fitsSystemWindows="true"', 'android:layout_height="68dp"', '@drawable/nexus_menu_button', 'android:textSize="30sp"']:
    assert token in layout, token
assert 'setInterval(publishStatus,3000)' not in adapter
