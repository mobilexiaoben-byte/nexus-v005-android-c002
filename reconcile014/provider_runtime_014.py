from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile013" / "provider_runtime_013.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile013" / "provider_runtime_013.py"),
    "sys": sys,
})

manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text()
old = """        <activity
            android:name=".MainActivity"
            android:exported="true">"""
new = """        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden">"""
assert old in m, "MainActivity manifest anchor missing"
manifest.write_text(m.replace(old, new, 1))

main = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main.read_text()
if "import android.content.res.Configuration" not in s:
    package_anchor = """package nexus.android.c002

"""
    assert package_anchor in s, "MainActivity package anchor missing"
    s = s.replace(
        package_anchor,
        """package nexus.android.c002

import android.content.res.Configuration
""",
        1,
    )

method_anchor = """    private fun handleBridgeMessage(origin: String, payload: String) {
"""
method = """    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        val orientationLabel = when (newConfig.orientation) {
            Configuration.ORIENTATION_LANDSCAPE -> "LANDSCAPE"
            Configuration.ORIENTATION_PORTRAIT -> "PORTRAIT"
            else -> "UNDEFINED"
        }
        recordDiagnostic(
            "CONFIGURATION_CHANGED_PRESERVED",
            if (::webView.isInitialized) webView.url else selectedProviderOrigin,
            "orientation=" + orientationLabel +
                ";execution_started=" + executionStarted +
                ";ack=" + ackPassed +
                ";terminal=" + terminalReceived +
                ";provider=" + (selectedProvider ?: "NONE")
        )
        if (::status.isInitialized) renderStatus()
    }

"""
assert method_anchor in s, "handleBridgeMessage anchor missing"
s = s.replace(method_anchor, method + method_anchor, 1)
main.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 66" in g
assert 'versionName = "0.0.66-v007-m024-u013-provider-runtime013-multiprovider"' in g
g = g.replace("versionCode = 66", "versionCode = 67", 1)
g = g.replace(
    'versionName = "0.0.66-v007-m024-u013-provider-runtime013-multiprovider"',
    'versionName = "0.0.67-v007-m024-u013-provider-runtime014-rotation-preserve"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME014_BASE=RUNTIME013\n"
    "ANDROID_ROTATION_POLICY=ACTIVITY_NOT_RECREATED_ON_ORIENTATION_SCREEN_SIZE_CHANGE\n"
    "ANDROID_ROTATION_STATE=WEBVIEW_BRIDGE_JOB_ACK_TERMINAL_STATE_PRESERVED_IN_PROCESS\n"
    "ANDROID_ROTATION_NAVIGATION=NO_LOADURL_ON_CONFIGURATION_CHANGE\n"
    "ANDROID_ROTATION_DEVICE_REPLAY=REQUIRED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

manifest_text = manifest.read_text()
main_text = main.read_text()
assert 'android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden"' in manifest_text
assert "override fun onConfigurationChanged(newConfig: Configuration)" in main_text
assert "CONFIGURATION_CHANGED_PRESERVED" in main_text
