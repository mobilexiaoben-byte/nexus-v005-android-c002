from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
subprocess.run([sys.executable, str(repo / 'u013ux006' / 'derive.py'), str(repo), str(work)], check=True)

p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared006"', 'applicationId = "nexus.android.u013.shared007"')
s = s.replace('versionCode = 51', 'versionCode = 52')
s = s.replace('versionName = "0.0.51-u013-android-ux-shared006-real-prompt"', 'versionName = "0.0.52-u013-android-ux-shared007-o24-bridge"')
assert 'nexus.android.u013.shared007' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

state_anchor = '    private var activeUserQuestion: String? = null\n'
assert s.count(state_anchor) == 1
s = s.replace(state_anchor, state_anchor + '    private var activeFactCheckJobId: String? = null\n')

old_fact = '''        findViewById<Button>(R.id.productFactCheck).setOnClickListener {
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
new_fact = '''        findViewById<Button>(R.id.productFactCheck).setOnClickListener {
            if (selectedProvider == null) {
                productState.text = "Choisissez d’abord un LLM"
                return@setOnClickListener
            }
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
                productState.text = "Session expirée · reconnectez ${selectedProvider}"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
                return@setOnClickListener
            }
            val rawClaim = productPrompt.text.toString().trim()
            if (rawClaim.isBlank()) {
                productState.text = "Saisissez l’affirmation à vérifier"
                return@setOnClickListener
            }
            ensureO24TokenThenCapture(rawClaim)
        }
'''
assert s.count(old_fact) == 1, 'Fact Check handler mismatch in SHARED-006'
s = s.replace(old_fact, new_fact)

method_anchor = '    private fun showLlmChooser(anchorView: View) {\n'
methods = '''    private fun ensureO24TokenThenCapture(rawClaim: String) {
        val prefs = getSharedPreferences(O24_PREFS, MODE_PRIVATE)
        val existing = prefs.getString(O24_TOKEN_KEY, "").orEmpty().trim()
        if (existing.isNotBlank()) {
            startO24Capture(rawClaim, existing)
            return
        }

        val input = android.widget.EditText(this).apply {
            hint = "Token bridge O24"
            inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
            setSingleLine(true)
        }
        android.app.AlertDialog.Builder(this)
            .setTitle("Connexion Fact Check O24")
            .setMessage("Saisissez une fois le token du bridge. Il reste stocké localement dans cette candidate de test.")
            .setView(input)
            .setNegativeButton("Annuler", null)
            .setPositiveButton("Enregistrer") { _, _ ->
                val token = input.text.toString().trim()
                if (token.isBlank()) {
                    productState.text = "Token O24 manquant"
                } else {
                    prefs.edit().putString(O24_TOKEN_KEY, token).apply()
                    startO24Capture(rawClaim, token)
                }
            }
            .show()
    }

    private fun startO24Capture(rawClaim: String, token: String) {
        val jobId = "ANDROID-O24-" + System.currentTimeMillis()
        activeFactCheckJobId = jobId
        productState.text = "Fact Check · transmission O24…"

        Thread {
            try {
                val payload = org.json.JSONObject()
                    .put("token", token)
                    .put("operation", "capture")
                    .put("job_id", jobId)
                    .put("raw_claim", rawClaim)

                val conn = java.net.URL(O24_BRIDGE_URL).openConnection() as java.net.HttpURLConnection
                conn.requestMethod = "POST"
                conn.connectTimeout = 15000
                conn.readTimeout = 30000
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                conn.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
                val code = conn.responseCode
                val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
                conn.disconnect()

                val json = org.json.JSONObject(body)
                val result = json.optString("result")
                val status = json.optString("status")
                val returnedJob = json.optString("job_id", jobId)
                val engineCalled = json.optBoolean("engine_called", false)
                val errorCode = json.optString("error_code")

                runOnUiThread {
                    activeFactCheckJobId = returnedJob
                    productState.text = when {
                        code !in 200..299 -> "Fact Check · erreur HTTP $code"
                        result == "ACCEPTED" && status == "PENDING_RESEARCH" && !engineCalled ->
                            "Fact Check transmis · recherche externe en attente"
                        errorCode.isNotBlank() -> "Fact Check · $errorCode"
                        else -> "Fact Check · $result $status".trim()
                    }
                }
            } catch (t: Throwable) {
                runOnUiThread {
                    productState.text = "Fact Check · bridge indisponible"
                    recordDiagnostic("O24_BRIDGE_ERROR", O24_BRIDGE_URL, t.javaClass.simpleName + ":" + (t.message ?: ""))
                }
            }
        }.start()
    }

'''
assert s.count(method_anchor) == 1
s = s.replace(method_anchor, methods + method_anchor)

const_anchor = '        const val ANSWER_PLACEHOLDER = "__NEXUS_MODEL_ANSWER__"\n'
assert s.count(const_anchor) == 1
s = s.replace(const_anchor, const_anchor + '''        const val O24_BRIDGE_URL = "https://script.google.com/macros/s/AKfycbyuhtzd6uM2o4W8V7BC2RtD5nwOBCkD-qEGns1WccBy5V3Jkn-35I8UaZ1lVYFOkv4r2Q/exec"
        const val O24_PREFS = "nexus_o24_bridge"
        const val O24_TOKEN_KEY = "bridge_token"
''')

for token in [
    'ensureO24TokenThenCapture(rawClaim)',
    'operation", "capture"',
    'Fact Check transmis · recherche externe en attente',
    'O24_BRIDGE_URL',
    'activeFactCheckJobId',
]:
    assert token in s, token
p.write_text(s)

(work / 'U013_BASELINE_LOCK.txt').write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_007\n'
    'INHERITED_DEVICE_VALIDATION=SHARED_006_ANALYSE_REAL_PROMPT_PASS\n'
    'ANALYSE_RUNTIME=UNCHANGED_FROM_SHARED_006\n'
    'FACTCHECK_ENTRY=productFactCheck\n'
    'FACTCHECK_BRIDGE=O24_ANDROID_WEBAPP_V0.1\n'
    'FACTCHECK_BRIDGE_OPERATION=capture\n'
    'FACTCHECK_EXPECTED_ACCEPT_STATUS=PENDING_RESEARCH\n'
    'FACTCHECK_ENGINE_CALL_ON_CAPTURE=false\n'
    'FACTCHECK_TOKEN_STORAGE=LOCAL_SHARED_PREFERENCES_TEST_CANDIDATE\n'
    'FACTCHECK_EXTERNAL_ORCHESTRATOR=NOT_YET_WIRED_FROM_ANDROID\n'
    'FACTCHECK_FINALIZE=NOT_AUTOMATIC\n'
    'CANONICAL_ENGINE_MODIFIED=false\n'
    'CANONICAL_GATEWAY_MODIFIED=false\n'
    'ACTIVE_ANDROID_PROVIDER_ADAPTER=ChatGPT_ONLY\n'
)
