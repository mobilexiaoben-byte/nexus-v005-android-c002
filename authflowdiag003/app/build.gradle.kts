plugins {
    id("com.android.application")
}

android {
    namespace = "nexus.android.c002"
    compileSdk = 36

    defaultConfig {
        applicationId = "nexus.android.c002.authflowdiag003"
        minSdk = 24
        targetSdk = 36
        versionCode = 4
        versionName = "0.0.4-c002-authflowdiag003"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}

dependencies {
    implementation("androidx.webkit:webkit:1.17.0")
}
