#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
POLICY="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
PASS=0
FAIL=0
check(){ local id="$1"; shift; if "$@"; then echo "PASS $id"; PASS=$((PASS+1)); else echo "FAIL $id"; FAIL=$((FAIL+1)); fi; }
has(){ grep -Fq "$2" "$1"; }

check B01_package has "$ROOT/app/build.gradle.kts" 'applicationId = "nexus.android.c002.executionproof006.blockhostdiag"'
check B02_version has "$ROOT/app/build.gradle.kts" 'versionCode = 8'
check B03_label has "$ROOT/app/src/main/AndroidManifest.xml" 'android:label="NEXUS C002 BLOCKHOST DIAG"'
check B04_profile has "$MAIN" 'nexus_provider_profile_c002_executionproof006_blockhostdiag'
check B05_prefs has "$MAIN" 'BLOCKHOST_PREFS'
check B06_key has "$MAIN" 'BLOCKHOST_KEY'
check B07_persist_function has "$MAIN" 'private fun persistBlockedHost(host: String)'
check B08_persist_exact_host has "$MAIN" '.putString(BLOCKHOST_KEY, persistedBlockedHost)'
check B09_display_exact has "$MAIN" 'LAST_BLOCKED_HOST=$persistedBlockedHost'
check B10_recover_exact has "$MAIN" 'LAST_BLOCKED_HOST=${persistedBlockedHost}'
check B11_navigation_persist has "$MAIN" 'persistBlockedHost(blockedHost)'
check B12_sanitized_host has "$MAIN" 'val blockedHost = sanitizeHost(rawUrl)'
check B13_no_execute_call bash -c "! grep -Fq 'startExecutionProof(origin)' '$MAIN'"
check B14_describe_stop has "$MAIN" 'blockhost_diag_no_execution=true'
check B15_no_provider_job_headline has "$MAIN" 'no provider job'
check B16_google_exact has "$POLICY" 'host == "accounts.google.com"'
check B17_youtube_exact has "$POLICY" 'host == "accounts.youtube.com"'
check B18_no_google_wildcard bash -c "! grep -Fq 'endsWith(\".google.com\")' '$POLICY'"
check B19_no_youtube_wildcard bash -c "! grep -Fq 'endsWith(\".youtube.com\")' '$POLICY'"
check B20_debug_disabled has "$MAIN" 'WebView.setWebContentsDebuggingEnabled(false)'
check B21_policy_hash bash -c "test \"\$(sha256sum '$POLICY' | cut -d' ' -f1)\" = '80241cf1581bdac6e87f602d300acebef5785f93e9bb570de4925b99118b76b3'"
check B22_no_google_root bash -c "! grep -Eq 'host == \"google\.com\"|googleusercontent' '$POLICY'"
check B23_no_youtube_root bash -c "! grep -Eq 'host == \"youtube\.com\"' '$POLICY'"
check B24_shared_pref_only_host bash -c "grep -Fq '.putString(BLOCKHOST_KEY, persistedBlockedHost)' '$MAIN' && ! grep -Fq '.putString(BLOCKHOST_KEY, rawUrl)' '$MAIN'"

printf 'BLOCKHOST_DIAG_STATIC_RESULT pass=%d fail=%d\n' "$PASS" "$FAIL"
test "$FAIL" -eq 0
