from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from the validated V007 clean-device candidate.
subprocess.run([
    sys.executable,
    str(repo / 'v007cleandevicee2e001' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# AUTHFIX1 gets a fresh Android sandbox and WebView profile so the retest cannot reuse V007-001 state.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.cleandevicee2e001"', 'applicationId = "nexus.android.v007.cleandevicee2e001.authfix1"')
s = s.replace('versionCode = 30', 'versionCode = 31')
s = s.replace('versionName = "0.0.30-v007-clean-device-e2e001"', 'versionName = "0.0.31-v007-clean-device-e2e001-authfix1"')
assert 'nexus.android.v007.cleandevicee2e001.authfix1' in s
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text()
s = s.replace('android:label="NEXUS V007 CLEAN DEVICE E2E 001"', 'android:label="NEXUS V007 CLEAN DEVICE AUTHFIX1"')
assert 'NEXUS V007 CLEAN DEVICE AUTHFIX1' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_v007_clean_device_e2e_001': 'nexus_provider_profile_v007_clean_device_e2e_001_authfix1',
    'V007-CLEAN-DEVICE-E2E-001-BRIDGE-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-BRIDGE-001',
    'V007-CLEAN-DEVICE-E2E-001-JOB-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-JOB-001',
    'V007-CLEAN-DEVICE-E2E-001-COMP-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-COMP-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_V1': 'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX1_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_OK': 'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX1_OK',
    'V007-ANDROID-CLEAN-DEVICE-E2E-001': 'V007-ANDROID-CLEAN-DEVICE-E2E-001-AUTHFIX1',
    'V007 CLEAN DEVICE E2E 001 — authenticate in ChatGPT; one read-only job runs after DESCRIBE PASS': 'V007 AUTHFIX1 — authenticate in ChatGPT; execution must start without opening the ChatGPT menu',
    'Return the exact frozen Result Pack for this clean-device Android E2E proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_OK.': 'Return the exact frozen Result Pack for this V007 AUTHFIX1 proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX1_OK.',
}
for old, new in replacements.items():
    s = s.replace(old, new)
required = [
    'nexus_provider_profile_v007_clean_device_e2e_001_authfix1',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-JOB-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX1_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX1_OK',
]
for token in required:
    assert token in s, token
p.write_text(s)

# Make the native top panel identify AUTHFIX1.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text().replace('android:text="V007 CLEAN DEVICE E2E 001 — initializing"', 'android:text="V007 CLEAN DEVICE AUTHFIX1 — initializing"')
p.write_text(s)

# Fix only auth-state observation. The account profile marker is authoritative even when
# ChatGPT keeps it in a collapsed/hidden sidebar. Login/signup actions are checked across
# buttons, links and role=button controls. No composer-only heuristic is accepted.
p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()
old = '''  function detectAuth(){
    const profiles=[...document.querySelectorAll('[data-testid="accounts-profile-button"]')].filter(visible);
    const authTexts=new Set(['se connecter','connexion','log in','login','inscription gratuite',"s'inscrire",'s’inscrire','sign up','signup']);
    const neg=[];
    for(const b of [...document.querySelectorAll('button')].filter(visible)){
      const t=String(b.innerText||b.textContent||'').replace(/\\s+/g,' ').trim().toLowerCase();
      if(authTexts.has(t)) neg.push(t);
    }
    let state='UNKNOWN', reason='NO_STABLE_RUNTIME_PROVEN_SIGNAL';
    if(profiles.length>0 && neg.length===0){
      state='AUTHENTICATED';
      reason='RUNTIME_PROVEN_PROFILE_BUTTON_PRESENT_AND_LOGIN_SIGNUP_ABSENT';
      lastStableAuthState='AUTHENTICATED';
    }else if(profiles.length===0 && neg.length>0){
      state='UNAUTHENTICATED';
      reason='RUNTIME_PROVEN_LOGIN_SIGNUP_PRESENT_AND_PROFILE_BUTTON_ABSENT';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(profiles.length>0 && neg.length>0){
      reason='CONFLICTING_AUTH_UI_SIGNALS';
    }else if(lastStableAuthState){
      state=lastStableAuthState;
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
    return {
      state,reason,
      observed_at:new Date().toISOString(),
      observed_at_ms:Date.now(),
      evidence:{
        positive:profiles.length?['data-testid=accounts-profile-button']:[],
        negative:[...new Set(neg)].map(x=>'visible_auth_action:'+x),
        support:['profile_button_count='+profiles.length]
      }
    };
  }
'''
new = '''  function detectAuth(){
    const profileMarkers=[...document.querySelectorAll('[data-testid="accounts-profile-button"]')];
    const visibleProfiles=profileMarkers.filter(visible);
    const authTexts=new Set(['se connecter','connexion','log in','login','inscription gratuite',"s'inscrire",'s’inscrire','sign up','signup']);
    const neg=[];
    const authControls=[...document.querySelectorAll('button,a,[role="button"]')].filter(visible);
    for(const control of authControls){
      const text=String(control.innerText||control.textContent||'').replace(/\\s+/g,' ').trim().toLowerCase();
      const aria=String(control.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim().toLowerCase();
      if(authTexts.has(text)) neg.push(text);
      if(authTexts.has(aria)) neg.push(aria);
    }
    let state='UNKNOWN', reason='NO_STABLE_RUNTIME_PROVEN_SIGNAL';
    if(profileMarkers.length>0 && neg.length===0){
      state='AUTHENTICATED';
      reason=visibleProfiles.length>0
        ? 'RUNTIME_PROVEN_VISIBLE_PROFILE_BUTTON_PRESENT_AND_LOGIN_SIGNUP_ABSENT'
        : 'RUNTIME_PROVEN_COLLAPSED_PROFILE_MARKER_PRESENT_AND_LOGIN_SIGNUP_ABSENT';
      lastStableAuthState='AUTHENTICATED';
    }else if(profileMarkers.length===0 && neg.length>0){
      state='UNAUTHENTICATED';
      reason='RUNTIME_PROVEN_LOGIN_SIGNUP_PRESENT_AND_PROFILE_MARKER_ABSENT';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(profileMarkers.length>0 && neg.length>0){
      reason='CONFLICTING_AUTH_UI_SIGNALS';
    }else if(lastStableAuthState){
      state=lastStableAuthState;
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
    return {
      state,reason,
      observed_at:new Date().toISOString(),
      observed_at_ms:Date.now(),
      evidence:{
        positive:profileMarkers.length?['data-testid=accounts-profile-button']:[],
        negative:[...new Set(neg)].map(x=>'visible_auth_action:'+x),
        support:[
          'profile_marker_count='+profileMarkers.length,
          'visible_profile_count='+visibleProfiles.length,
          'auth_control_count='+authControls.length
        ]
      }
    };
  }
'''
assert s.count(old) == 1, 'detectAuth baseline mismatch'
s = s.replace(old, new)
p.write_text(s)
