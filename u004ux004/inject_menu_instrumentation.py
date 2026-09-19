from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

# Add Android instrumentation runner + dependencies to the derived candidate only.
bg = root / 'app/build.gradle.kts'
s = bg.read_text()
s = s.replace(
    '        versionName = "0.0.43-u004-android-ux-shell004-content"\n',
    '        versionName = "0.0.43-u004-android-ux-shell004-content"\n        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"\n'
)
s = s.replace(
    'dependencies {\n    implementation("androidx.webkit:webkit:1.17.0")\n}',
    '''dependencies {\n    implementation("androidx.webkit:webkit:1.17.0")\n    androidTestImplementation("androidx.test:core:1.6.1")\n    androidTestImplementation("androidx.test:runner:1.6.2")\n    androidTestImplementation("androidx.test.ext:junit:1.2.1")\n    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")\n}'''
)
assert 'AndroidJUnitRunner' in s
assert 'espresso-core' in s
bg.write_text(s)

# Instrumentation test: no provider/network claim. It starts the exact SHELL004 UI,
# forces the already DEVICE-proved terminal state, then exercises the three user menu actions.
test = root / 'app/src/androidTest/java/nexus/android/c002/U004MenuFlowTest.kt'
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text(r'''package nexus.android.c002

import android.view.View
import android.widget.LinearLayout
import android.webkit.WebView
import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.hamcrest.CoreMatchers.containsString
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class U004MenuFlowTest {
    @Test
    fun terminalMenuActionsSwitchViewsAndExposeDiagnostics() {
        val scenario = ActivityScenario.launch(MainActivity::class.java)
        scenario.onActivity { activity ->
            val proofStopped = MainActivity::class.java.getDeclaredField("proofStopped")
            proofStopped.isAccessible = true
            proofStopped.setBoolean(activity, true)

            val headline = MainActivity::class.java.getDeclaredField("currentHeadline")
            headline.isAccessible = true
            headline.set(activity, "EXECUTION PROOF PASS — STOP GATE")

            val showValidated = MainActivity::class.java.getDeclaredMethod(
                "showValidatedResult", String::class.java, String::class.java
            )
            showValidated.isAccessible = true
            showValidated.invoke(activity, "Résultat substantiel de test", "ChatGPT UI session")
        }

        // Initial NEXUS result view.
        onView(withId(R.id.resultPanel)).check(matches(isDisplayed()))
        onView(withId(R.id.providerWebView)).check(matches(withEffectiveVisibility(Visibility.GONE)))

        // 1. Voir la réponse ChatGPT.
        onView(withId(R.id.nexusMenu)).perform(click())
        onView(withText("Voir la réponse ChatGPT")).perform(click())
        onView(withId(R.id.providerWebView)).check(matches(withEffectiveVisibility(Visibility.VISIBLE)))
        onView(withId(R.id.resultPanel)).check(matches(withEffectiveVisibility(Visibility.GONE)))

        // 2. Afficher le résultat NEXUS.
        onView(withId(R.id.nexusMenu)).perform(click())
        onView(withText("Afficher le résultat NEXUS")).perform(click())
        onView(withId(R.id.resultPanel)).check(matches(isDisplayed()))
        onView(withId(R.id.providerWebView)).check(matches(withEffectiveVisibility(Visibility.GONE)))

        // 3. Détails techniques.
        onView(withId(R.id.nexusMenu)).perform(click())
        onView(withText("Détails techniques")).perform(click())
        onView(withId(R.id.status)).check(matches(withText(containsString("EXECUTION PROOF PASS — STOP GATE"))))

        scenario.close()
    }
}
''')
print('INSTRUMENTATION_INJECTED')
