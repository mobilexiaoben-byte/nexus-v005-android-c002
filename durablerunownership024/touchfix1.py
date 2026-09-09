from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()


def one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected 1 match, found {count}"
    return text.replace(old, new, 1)

layout = root / 'app/src/main/res/layout/activity_main.xml'
x = layout.read_text()
x = one(x, 'android:padding="8dp"\n        android:maxLines="2"', 'android:padding="4dp"\n        android:maxLines="1"', 'compact status layout')
x = one(x, 'android:focusable="true"', 'android:focusable="false"', 'status focus')
x = one(x, 'android:maxLines="7"\n        android:textSize="11sp"', 'android:maxLines="2"\n        android:ellipsize="end"\n        android:focusable="false"\n        android:textSize="10sp"', 'compact evidence layout')
layout.write_text(x)

main = root / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()
old = '''        status.setOnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n'''
new = '''        val toggleDiagnostics = View.OnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n        status.setOnClickListener(toggleDiagnostics)\n        runEvidence.setOnClickListener(toggleDiagnostics)\n        webView.isFocusable = true\n        webView.isFocusableInTouchMode = true\n        webView.setOnTouchListener { view, _ ->\n            if (!view.hasFocus()) view.requestFocus(View.FOCUS_DOWN)\n            false\n        }\n'''
s = one(s, old, new, 'diagnostic toggle and webview touch focus')
s = one(
    s,
    '''    private fun renderRunEvidence() {\n        if (!::runEvidence.isInitialized || !::runLatch.isInitialized) return\n''',
    '''    private fun renderRunEvidence() {\n        if (!::runEvidence.isInitialized || !::runLatch.isInitialized) return\n        runEvidence.maxLines = if (diagnosticExpanded) EXPANDED_EVIDENCE_LINES else COMPACT_EVIDENCE_LINES\n''',
    'dynamic evidence lines',
)
s = one(s, '        const val COMPACT_STATUS_LINES = 2\n        const val EXPANDED_STATUS_LINES = 10\n', '        const val COMPACT_STATUS_LINES = 1\n        const val EXPANDED_STATUS_LINES = 10\n        const val COMPACT_EVIDENCE_LINES = 2\n        const val EXPANDED_EVIDENCE_LINES = 7\n', 'compact constants')
main.write_text(s)
