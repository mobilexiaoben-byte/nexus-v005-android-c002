from pathlib import Path
import sys

r = Path(sys.argv[1])

def replace_once(path: Path, old: str, new: str, label: str):
    s = path.read_text()
    if s.count(old) != 1:
        raise SystemExit(f"{label} mismatch count={s.count(old)}")
    path.write_text(s.replace(old, new))

p = r / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.c002"', 'applicationId = "nexus.android.c002.executionproof006.blockhostdiag"')
s = s.replace('versionCode = 2', 'versionCode = 8')
s = s.replace('versionName = "0.0.2-c002"', 'versionName = "0.0.8-c002-executionproof006-blockhostdiag"')
p.write_text(s)

replace_once(
    r / 'app/src/main/AndroidManifest.xml',
    'android:label="NEXUS Android C002"',
    'android:label="NEXUS C002 BLOCKHOST DIAG"',
    'manifest label',
)

replace_once(
    r / 'app/src/main/res/layout/activity_main.xml',
    'android:padding="12dp"\n        android:text="NEXUS C002 — initializing"',
    'android:padding="8dp"\n        android:maxLines="2"\n        android:ellipsize="end"\n        android:clickable="true"\n        android:focusable="true"\n        android:text="BLOCKHOST DIAG — initializing"',
    'layout',
)

replace_once(
    r / 'app/src/main/java/nexus/android/c002/web/OriginPolicy.kt',
    '            host == "anthropic.com" || host.endsWith(".anthropic.com")\n',
    '            host == "anthropic.com" || host.endsWith(".anthropic.com") ||\n            host == "accounts.google.com" ||\n            host == "accounts.youtube.com"\n',
    'policy',
)

p = r / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

def rep(old: str, new: str, label: str):
    global s
    if s.count(old) != 1:
        raise SystemExit(f"MainActivity {label} mismatch count={s.count(old)}")
    s = s.replace(old, new)

rep(
    '    private var lastAuthState: String? = null\n',
    '    private var lastAuthState: String? = null\n    private var persistedBlockedHost: String? = null\n',
    'field',
)

rep(
'''        status.setOnClickListener {
            diagnosticExpanded = !diagnosticExpanded
            renderStatus()
        }
''',
'''        status.setOnClickListener {
            diagnosticExpanded = !diagnosticExpanded
            renderStatus()
        }
        persistedBlockedHost = getSharedPreferences(BLOCKHOST_PREFS, MODE_PRIVATE).getString(BLOCKHOST_KEY, null)
        if (!persistedBlockedHost.isNullOrBlank()) {
            currentHeadline = "LAST_BLOCKED_HOST RECOVERED — tap for exact host"
            currentBody = "LAST_BLOCKED_HOST=${persistedBlockedHost}"
        }
''',
    'onCreate persistence',
)

rep(
'''                return if (allowed) {
                    false
                } else {
                    block("ANDROID_NAVIGATION_ORIGIN_BLOCKED:${sanitizeHost(rawUrl)}")
                    true
                }
''',
'''                return if (allowed) {
                    false
                } else {
                    val blockedHost = sanitizeHost(rawUrl)
                    persistBlockedHost(blockedHost)
                    block("ANDROID_NAVIGATION_ORIGIN_BLOCKED:$blockedHost")
                    true
                }
''',
    'navigation block',
)

rep(
'''                    currentHeadline = ACTIVE_HEADLINE
                    currentBody = null
                    recordDiagnostic("onPageStarted", url, "main_frame=true")
''',
'''                    currentHeadline = if (persistedBlockedHost.isNullOrBlank()) ACTIVE_HEADLINE else "LAST_BLOCKED_HOST RECOVERED — tap for exact host"
                    currentBody = persistedBlockedHost?.let { "LAST_BLOCKED_HOST=$it" }
                    recordDiagnostic("onPageStarted", url, "main_frame=true")
''',
    'navigation reset',
)

rep(
'''        describePassed = true
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true")
        currentHeadline = "DESCRIBE PASS — execution proof starting"
        currentBody = null
        renderStatus()
        startExecutionProof(origin)
''',
'''        describePassed = true
        proofStopped = true
        recordFinalEvent("DESCRIBE_PASS", "authenticated=true;blockhost_diag_no_execution=true")
        currentHeadline = "BLOCKHOST DIAG PASS — authenticated DESCRIBE; no provider job"
        currentBody = persistedBlockedHost?.let { "LAST_BLOCKED_HOST=$it" } ?: "LAST_BLOCKED_HOST=<none observed in this run>"
        renderStatus()
''',
    'describe stop',
)

rep(
'    private fun sanitizeUrl(rawUrl: String): String {\n',
'''    private fun persistBlockedHost(host: String) {
        if (host.isBlank() || host == "<invalid>" || host == "<no-host>") return
        persistedBlockedHost = host.lowercase()
        getSharedPreferences(BLOCKHOST_PREFS, MODE_PRIVATE)
            .edit()
            .putString(BLOCKHOST_KEY, persistedBlockedHost)
            .apply()
        currentBody = "LAST_BLOCKED_HOST=$persistedBlockedHost"
    }

    private fun sanitizeUrl(rawUrl: String): String {
''',
    'persist function',
)

s = s.replace(
    'const val PROFILE_NAME = "nexus_provider_profile_c002_executionproof006"',
    'const val PROFILE_NAME = "nexus_provider_profile_c002_executionproof006_blockhostdiag"',
)
rep(
    '        const val ACTIVE_HEADLINE = "EXECUTION PROOF 006 — authenticate in ChatGPT; one read-only proof job will run after DESCRIBE PASS"\n',
    '        const val BLOCKHOST_PREFS = "nexus_v005_blockhost_diag"\n        const val BLOCKHOST_KEY = "last_blocked_host"\n        const val ACTIVE_HEADLINE = "BLOCKHOST DIAG — authenticate only; no provider job will run"\n',
    'constants',
)
s = s.replace(
    'const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; execution starts only after authenticated DESCRIBE PASS"',
    'const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; BLOCKHOST DIAG only, no provider execution"',
)
p.write_text(s)
