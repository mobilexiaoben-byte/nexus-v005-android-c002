from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from AUTHFIX1, preserving the validated transport and auth evidence rules.
subprocess.run([
    sys.executable,
    str(repo / 'v007authfix1' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# AUTHFIX2 gets a fresh Android sandbox and WebView profile.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.cleandevicee2e001.authfix1"', 'applicationId = "nexus.android.v007.cleandevicee2e001.authfix2"')
s = s.replace('versionCode = 31', 'versionCode = 32')
s = s.replace('versionName = "0.0.31-v007-clean-device-e2e001-authfix1"', 'versionName = "0.0.32-v007-clean-device-e2e001-authfix2"')
assert 'nexus.android.v007.cleandevicee2e001.authfix2' in s
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text().replace('android:label="NEXUS V007 CLEAN DEVICE AUTHFIX1"', 'android:label="NEXUS V007 CLEAN DEVICE AUTHFIX2"')
assert 'NEXUS V007 CLEAN DEVICE AUTHFIX2' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_v007_clean_device_e2e_001_authfix1': 'nexus_provider_profile_v007_clean_device_e2e_001_authfix2',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-BRIDGE-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-BRIDGE-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-JOB-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-JOB-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX1-COMP-001': 'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-COMP-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX1_V1': 'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX2_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX1_OK': 'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK',
    'V007-ANDROID-CLEAN-DEVICE-E2E-001-AUTHFIX1': 'V007-ANDROID-CLEAN-DEVICE-E2E-001-AUTHFIX2',
    'V007 AUTHFIX1 — authenticate in ChatGPT; execution must start without opening the ChatGPT menu': 'V007 AUTHFIX2 — authenticate in ChatGPT; NEXUS may open the ChatGPT sidebar only to expose authoritative auth evidence',
    'Return the exact frozen Result Pack for this V007 AUTHFIX1 proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX1_OK.': 'Return the exact frozen Result Pack for this V007 AUTHFIX2 proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK.',
}
for old, new in replacements.items():
    s = s.replace(old, new)
for token in [
    'nexus_provider_profile_v007_clean_device_e2e_001_authfix2',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-JOB-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX2_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK',
]:
    assert token in s, token
p.write_text(s)

p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text().replace('android:text="V007 CLEAN DEVICE AUTHFIX1 — initializing"', 'android:text="V007 CLEAN DEVICE AUTHFIX2 — initializing"')
p.write_text(s)

# AUTHFIX2: active, fail-closed auth evidence exposure.
# The menu click is NEVER auth proof. It only exposes the already-authoritative profile marker.
p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()

# Do not retain a stale UNAUTHENTICATED state after login controls disappear.
old = """    }else if(lastStableAuthState){
      state=lastStableAuthState;
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
"""
new = """    }else if(lastStableAuthState==='AUTHENTICATED'){
      state='AUTHENTICATED';
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
"""
assert s.count(old) == 1, 'AUTHFIX1 stable-auth block mismatch'
s = s.replace(old, new)

anchor = """  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('CHATGPT AUTH: '+s.state);
    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
  }
"""
replacement = """  let authProbeUnknownSince=0;
  let authProbeAttempted=false;
  let authProbeInFlight=false;
  let authProbeLast='NOT_ATTEMPTED';

  function findAuthMenuProbeButton(){
    const selectors=[
      'button[data-testid=\"open-sidebar-button\"]',
      '[data-testid=\"open-sidebar-button\"]',
      'button[aria-label=\"Open sidebar\"]',
      'button[aria-label=\"Ouvrir la barre latérale\"]',
      'button[aria-label=\"Open menu\"]',
      'button[aria-label=\"Ouvrir le menu\"]',
      'button[aria-label=\"Menu\"]'
    ];
    const seen=new Set();
    const matches=[];
    for(const selector of selectors){
      for(const el of document.querySelectorAll(selector)){
        if(seen.has(el) || !visible(el) || el.disabled) continue;
        seen.add(el);
        matches.push(el);
      }
    }
    return {button:matches.length===1?matches[0]:null,count:matches.length};
  }

  function authProbeMeta(){
    return {
      mode:'AUTO_AUTH_MENU_PROBE',
      attempted:authProbeAttempted,
      in_flight:authProbeInFlight,
      last:authProbeLast,
      menu_click_is_auth_proof:false
    };
  }

  async function maybeAutoOpenAuthMenu(status){
    // MENU_CLICK_IS_NOT_AUTH_PROOF: only detectAuth() can produce AUTHENTICATED.
    if(running || authProbeInFlight) return;
    if(status.state==='AUTHENTICATED'){
      authProbeUnknownSince=0;
      authProbeLast='AUTH_ALREADY_PROVEN';
      return;
    }
    if(status.state==='UNAUTHENTICATED'){
      // Visible login/signup is current strong evidence. Reset so a later OAuth return can probe once.
      authProbeUnknownSince=0;
      authProbeAttempted=false;
      authProbeLast='CURRENT_UNAUTH_EVIDENCE';
      return;
    }
    if(status.state!=='UNKNOWN') return;
    if((status.evidence?.negative||[]).length>0) return;
    if(!findComposer()) return; // activation condition only; never auth evidence.
    if(!authProbeUnknownSince) authProbeUnknownSince=Date.now();
    if(Date.now()-authProbeUnknownSince<2500) return;
    if(authProbeAttempted) return;

    const probe=findAuthMenuProbeButton();
    authProbeAttempted=true;
    if(!probe.button){
      authProbeLast=probe.count===0?'NO_UNIQUE_MENU_BUTTON_FOUND':'AMBIGUOUS_MENU_BUTTONS_'+probe.count;
      return;
    }

    authProbeInFlight=true;
    authProbeLast='MENU_CLICKED_WAITING_FOR_AUTHORITATIVE_AUTH_SIGNAL';
    show('CHATGPT AUTH PROBE — ouverture automatique du menu');
    try{
      probe.button.click();
    }finally{
      setTimeout(()=>{
        authProbeInFlight=false;
        publishStatus().catch(()=>{});
      },700);
    }
  }

  async function publishStatus(){
    const s=detectAuth();
    s.auth_probe=authProbeMeta();
    if(!running) show('CHATGPT AUTH: '+s.state+(authProbeLast==='MENU_CLICKED_WAITING_FOR_AUTHORITATIVE_AUTH_SIGNAL'?' — AUTH MENU PROBE':''));
    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
    await maybeAutoOpenAuthMenu(s);
  }
"""
assert s.count(anchor) == 1, 'publishStatus anchor mismatch'
s = s.replace(anchor, replacement)
p.write_text(s)
