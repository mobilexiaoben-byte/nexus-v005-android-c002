from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from AUTH WINDOW 013. Provider assets, OriginPolicy and bridge stay byte-identical.
subprocess.run([
    'python3', str(repo / 'claudeauthwindow013' / 'derive.py'), str(repo), str(work)
], check=True)

p = work / 'app/build.gradle.kts'
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.claudeauthwindow013"', 'applicationId = "nexus.android.c002.claudeoauthhandoff014"'),
    ('versionCode = 14', 'versionCode = 15'),
    ('versionName = "0.0.14-c002-claude-authwindow013"', 'versionName = "0.0.15-c002-claude-oauthhandoff014"'),
]:
    assert g.count(before) == 1, f'gradle anchor mismatch: {before}'
    g = g.replace(before, after)
p.write_text(g)

p = work / 'app/src/main/AndroidManifest.xml'
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE AUTH WINDOW 013"'
assert m.count(old_label) == 1, 'manifest label mismatch'
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE OAUTH HANDOFF 014"'))

main = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()

# Add bounded OAuth handoff state to the controller only.
state_anchor = '    private var authPopupSawExternalAuthHost = false\n'
assert s.count(state_anchor) == 1
s = s.replace(state_anchor, state_anchor +
    '    private var oauthHandoffPending = false\n'
    '    private var oauthHandoffFallbackUsed = false\n'
    '    private var oauthHandoffGeneration = 0\n')

# Provider close: close popup without immediate parent reload, then observe the parent passively.
old_close_window = '                closeAuthPopup("provider_window_close", reloadMain = true)\n'
new_close_window = ('                closeAuthPopup("provider_window_close")\n'
                    '                beginOAuthHandoffObservation("provider_window_close")\n')
assert s.count(old_close_window) == 1, 'provider close anchor mismatch'
s = s.replace(old_close_window, new_close_window)

# OAuth return-to-Claude path: same rule, no forced reload.
old_return_close = '                            closeAuthPopup("oauth_returned_claude", reloadMain = true)\n'
new_return_close = ('                            closeAuthPopup("oauth_returned_claude")\n'
                    '                            beginOAuthHandoffObservation("oauth_returned_claude")\n')
assert s.count(old_return_close) == 1, 'oauth return close anchor mismatch'
s = s.replace(old_return_close, new_return_close)

# Back navigation is not an OAuth completion signal.
old_back = '            closeAuthPopup("user_back", reloadMain = false)\n'
assert s.count(old_back) == 1, 'user back anchor mismatch'
s = s.replace(old_back, '            closeAuthPopup("user_back")\n')

# Replace 013 close helper: detach immediately, but do not stop loading/destroy until grace expires;
# never reload the parent here. This preserves a chance for opener/postMessage handoff to settle.
old_helper_start = '    private fun closeAuthPopup(reason: String, reloadMain: Boolean) {\n'
helper_start = s.index(old_helper_start)
helper_end_marker = '\n    private fun disposeAuthPopup() {\n'
helper_end = s.index(helper_end_marker, helper_start)
old_helper = s[helper_start:helper_end]
new_helper = '''    private fun beginOAuthHandoffObservation(reason: String) {
        if (executionStarted || proofStopped) return
        if (oauthHandoffPending) {
            recordDiagnostic(
                event = "OAUTH_HANDOFF_WAIT_ALREADY_ACTIVE",
                rawUrl = webView.url,
                detail = "reason=${sanitizeCode(reason)}"
            )
            return
        }
        oauthHandoffPending = true
        oauthHandoffFallbackUsed = false
        oauthHandoffGeneration += 1
        authenticatedStableSinceMs = null
        authenticatedStableCount = 0
        authenticatedStableReason = null
        val generation = oauthHandoffGeneration
        recordDiagnostic(
            event = "OAUTH_HANDOFF_WAIT_STARTED",
            rawUrl = webView.url,
            detail = "reason=${sanitizeCode(reason)};passive_wait_ms=$OAUTH_HANDOFF_PASSIVE_WAIT_MS"
        )
        currentHeadline = OAUTH_HANDOFF_WAIT_HEADLINE
        currentBody = null
        renderStatus()
        scheduleOAuthHandoffTimeout(generation, OAUTH_HANDOFF_PASSIVE_WAIT_MS)
    }

    private fun scheduleOAuthHandoffTimeout(generation: Int, delayMs: Long) {
        handler.postDelayed({
            if (!oauthHandoffPending || oauthHandoffGeneration != generation || executionStarted || proofStopped) {
                return@postDelayed
            }
            if (!oauthHandoffFallbackUsed) {
                oauthHandoffFallbackUsed = true
                recordDiagnostic(
                    event = "OAUTH_HANDOFF_FALLBACK_RELOAD",
                    rawUrl = webView.url,
                    detail = "single_reload=true;fallback_wait_ms=$OAUTH_HANDOFF_FALLBACK_WAIT_MS"
                )
                currentHeadline = OAUTH_HANDOFF_FALLBACK_HEADLINE
                currentBody = null
                renderStatus()
                webView.reload()
                scheduleOAuthHandoffTimeout(generation, OAUTH_HANDOFF_FALLBACK_WAIT_MS)
            } else {
                block("CLAUDE_OAUTH_HANDOFF_NOT_ESTABLISHED")
            }
        }, delayMs)
    }

    private fun completeOAuthHandoff(origin: String, reason: String) {
        if (!oauthHandoffPending) return
        oauthHandoffPending = false
        oauthHandoffGeneration += 1
        recordDiagnostic(
            event = "OAUTH_HANDOFF_AUTHENTICATED",
            rawUrl = origin,
            detail = "fallback_used=$oauthHandoffFallbackUsed;reason=${sanitizeCode(reason)}"
        )
    }

    private fun closeAuthPopup(reason: String) {
        val popup = authPopupWebView ?: return
        authPopupWebView = null
        authPopupSawExternalAuthHost = false
        recordDiagnostic(
            event = "AUTH_WINDOW_CLOSED",
            rawUrl = popup.url,
            detail = "reason=${sanitizeCode(reason)};reload_main=false;destroy_grace_ms=$AUTH_POPUP_DESTROY_GRACE_MS"
        )
        runCatching { popup.visibility = View.GONE }
        runCatching { (popup.parent as? ViewGroup)?.removeView(popup) }
        handler.postDelayed({
            runCatching { popup.destroy() }
        }, AUTH_POPUP_DESTROY_GRACE_MS)
    }
'''
s = s[:helper_start] + new_helper + s[helper_end:]

# While OAuth handoff is pending, transient UNKNOWN/UNAUTHENTICATED are observations, not terminal/auth-required UI.
when_anchor = '        when (authState) {\n'
assert s.count(when_anchor) == 1
handoff_gate = '''        if (oauthHandoffPending) {
            if (authState == "AUTHENTICATED") {
                completeOAuthHandoff(origin, authReason)
            } else {
                if (authChanged) {
                    recordDiagnostic(
                        event = "OAUTH_HANDOFF_WAIT_STATUS",
                        rawUrl = origin,
                        detail = "auth_state=${sanitizeCode(authState)};fallback_used=$oauthHandoffFallbackUsed"
                    )
                }
                currentHeadline = if (oauthHandoffFallbackUsed) {
                    OAUTH_HANDOFF_FALLBACK_HEADLINE
                } else {
                    OAUTH_HANDOFF_WAIT_HEADLINE
                }
                currentBody = null
                renderStatus()
                return
            }
        }

'''
s = s.replace(when_anchor, handoff_gate + when_anchor)

# Defense in depth: even if a future controller path accidentally reaches startExecutionProof,
# dispatch remains forbidden while handoff is pending.
start_anchor = '''    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
        if (authPopupWebView != null) {
'''
assert s.count(start_anchor) == 1, 'startExecutionProof anchor mismatch'
s = s.replace(start_anchor, '''    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
        if (oauthHandoffPending) {
            block("CLAUDE_OAUTH_HANDOFF_PENDING_AT_EXECUTION")
            return
        }
        if (authPopupWebView != null) {
''')

# Identity and proof contract.
for before, after in [
    ('nexus_provider_profile_c002_claude_authwindow013', 'nexus_provider_profile_c002_claude_oauthhandoff014'),
    ('V005-C002-CLAUDE-AUTH-WINDOW-013-BRIDGE-001', 'V005-C002-CLAUDE-OAUTH-HANDOFF-014-BRIDGE-001'),
    ('V005-C002-CLAUDE-AUTH-WINDOW-013-001', 'V005-C002-CLAUDE-OAUTH-HANDOFF-014-001'),
    ('V005-C002-CLAUDE-AUTH-WINDOW-013-COMP-001', 'V005-C002-CLAUDE-OAUTH-HANDOFF-014-COMP-001'),
    ('V005_CLAUDE_AUTH_WINDOW_013_V1', 'V005_CLAUDE_OAUTH_HANDOFF_014_V1'),
    ('NEXUS_CLAUDE_AUTH_WINDOW_013_OK', 'NEXUS_CLAUDE_OAUTH_HANDOFF_014_OK'),
    ('this Android Claude auth-window transport proof', 'this Android Claude OAuth-handoff transport proof'),
    ('.put("contract", "V005-C002-CLAUDE-AUTH-WINDOW-013")', '.put("contract", "V005-C002-CLAUDE-OAUTH-HANDOFF-014")'),
    ('CLAUDE AUTH WINDOW 013 — authenticate in the isolated NEXUS window; execution remains blocked until it closes', 'CLAUDE OAUTH HANDOFF 014 — authenticate with Google; parent handoff is observed before any execution'),
]:
    assert before in s, f'identity/content anchor missing: {before}'
    s = s.replace(before, after)

# Replace 013 reload timing constant with bounded handoff timings.
old_constants = ('        const val AUTH_WINDOW_ACTIVE_HEADLINE = "CLAUDE AUTH WINDOW 013 — authentication window active — no DESCRIBE or dispatch"\n'
                 '        const val AUTH_POPUP_RETURN_SETTLE_MS = 1_500L\n'
                 '        const val AUTH_POPUP_MAIN_RELOAD_DELAY_MS = 250L\n')
new_constants = ('        const val AUTH_WINDOW_ACTIVE_HEADLINE = "CLAUDE OAUTH HANDOFF 014 — authentication window active — no DESCRIBE or dispatch"\n'
                 '        const val OAUTH_HANDOFF_WAIT_HEADLINE = "CLAUDE OAUTH HANDOFF — waiting for parent session transfer — no DESCRIBE or dispatch"\n'
                 '        const val OAUTH_HANDOFF_FALLBACK_HEADLINE = "CLAUDE OAUTH HANDOFF — single fallback reload used — waiting for authenticated session"\n'
                 '        const val AUTH_POPUP_RETURN_SETTLE_MS = 1_500L\n'
                 '        const val AUTH_POPUP_DESTROY_GRACE_MS = 750L\n'
                 '        const val OAUTH_HANDOFF_PASSIVE_WAIT_MS = 6_000L\n'
                 '        const val OAUTH_HANDOFF_FALLBACK_WAIT_MS = 8_000L\n')
assert s.count(old_constants) == 1, '013 constants anchor mismatch'
s = s.replace(old_constants, new_constants)

# Fail closed if immediate-reload mechanics from 013 survive.
assert 'AUTH_POPUP_MAIN_RELOAD_DELAY_MS' not in s
assert 'reloadMain' not in s
assert 'OAUTH_HANDOFF_FALLBACK_RELOAD' in s
assert 'CLAUDE_OAUTH_HANDOFF_NOT_ESTABLISHED' in s
assert 'CLAUDE_AUTH_STABLE_MIN_MS = 1_500L' in s
assert 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' in s
main.write_text(s)
