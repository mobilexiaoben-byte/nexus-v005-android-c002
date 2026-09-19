from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from U004 UX SHELL 001, preserving its validated UX shell and AUTHFIX2 transport.
subprocess.run([
    sys.executable,
    str(repo / 'u004ux001' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Fresh Android identity/profile for SHELL 002.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u004.uxshell001"', 'applicationId = "nexus.android.u004.uxshell002"')
s = s.replace('versionCode = 40', 'versionCode = 41')
s = s.replace('versionName = "0.0.40-u004-android-ux-shell001"', 'versionName = "0.0.41-u004-android-ux-shell002-autoclose"')
assert 'nexus.android.u004.uxshell002' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_u004_android_ux_shell_001': 'nexus_provider_profile_u004_android_ux_shell_002',
    'U004-ANDROID-UX-SHELL-001-BRIDGE-001': 'U004-ANDROID-UX-SHELL-002-BRIDGE-001',
    'U004-ANDROID-UX-SHELL-001-JOB-001': 'U004-ANDROID-UX-SHELL-002-JOB-001',
    'U004-ANDROID-UX-SHELL-001-COMP-001': 'U004-ANDROID-UX-SHELL-002-COMP-001',
    'U004_ANDROID_UX_SHELL_001_V1': 'U004_ANDROID_UX_SHELL_002_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_001_OK': 'NEXUS_U004_ANDROID_UX_SHELL_002_OK',
    'U004-ANDROID-UX-SHELL-001': 'U004-ANDROID-UX-SHELL-002',
}
for old, new in replacements.items():
    s = s.replace(old, new)
for token in [
    'nexus_provider_profile_u004_android_ux_shell_002',
    'U004-ANDROID-UX-SHELL-002-JOB-001',
    'U004_ANDROID_UX_SHELL_002_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_002_OK',
]:
    assert token in s, token
p.write_text(s)

# UX SHELL 002: close only the sidebar that the AUTHFIX2 probe itself opened.
# Closing is UX-only and happens only after detectAuth() has already produced AUTHENTICATED.
p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()

old_vars = """  let authProbeUnknownSince=0;
  let authProbeAttempted=false;
  let authProbeInFlight=false;
  let authProbeLast='NOT_ATTEMPTED';
"""
new_vars = """  let authProbeUnknownSince=0;
  let authProbeAttempted=false;
  let authProbeInFlight=false;
  let authProbeLast='NOT_ATTEMPTED';
  let authProbeOpenedSidebar=false;
  let authProbeCloseAttempts=0;
  let authProbeCloseLast='NOT_ATTEMPTED';
"""
assert s.count(old_vars) == 1, 'auth probe vars mismatch'
s = s.replace(old_vars, new_vars)

anchor = """  function authProbeMeta(){
    return {
      mode:'AUTO_AUTH_MENU_PROBE',
      attempted:authProbeAttempted,
      in_flight:authProbeInFlight,
      last:authProbeLast,
      menu_click_is_auth_proof:false
    };
  }
"""
replacement = """  function findAuthMenuCloseButton(){
    const selectors=[
      'button[data-testid=\"close-sidebar-button\"]',
      '[data-testid=\"close-sidebar-button\"]',
      'button[aria-label=\"Close sidebar\"]',
      'button[aria-label=\"Fermer la barre latérale\"]',
      'button[aria-label=\"Close menu\"]',
      'button[aria-label=\"Fermer le menu\"]'
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
      menu_click_is_auth_proof:false,
      opened_sidebar_by_nexus:authProbeOpenedSidebar,
      close_attempts:authProbeCloseAttempts,
      close_last:authProbeCloseLast,
      sidebar_close_is_auth_proof:false
    };
  }

  async function maybeAutoCloseAuthMenu(status){
    // AUTO_CLOSE_IS_UX_ONLY: auth was already proven before this function is eligible.
    if(status.state!=='AUTHENTICATED') return;
    if(!authProbeOpenedSidebar) return; // never close a sidebar opened by the user.
    if(authProbeInFlight) return;
    if(authProbeCloseLast==='CLOSED_AFTER_AUTH_PROOF') return;
    if(authProbeCloseAttempts>=4) return;

    const close=findAuthMenuCloseButton();
    authProbeCloseAttempts++;
    if(!close.button){
      authProbeCloseLast=close.count===0?'CLOSE_BUTTON_NOT_VISIBLE_'+authProbeCloseAttempts:'AMBIGUOUS_CLOSE_BUTTONS_'+close.count;
      setTimeout(()=>publishStatus().catch(()=>{}),350);
      return;
    }

    authProbeCloseLast='CLOSED_AFTER_AUTH_PROOF';
    show('CHATGPT AUTH: AUTHENTICATED — fermeture automatique du menu');
    close.button.click();
    authProbeOpenedSidebar=false;
  }
"""
assert s.count(anchor) == 1, 'authProbeMeta anchor mismatch'
s = s.replace(anchor, replacement)

old_click = """    try{
      probe.button.click();
    }finally{
"""
new_click = """    try{
      probe.button.click();
      authProbeOpenedSidebar=true;
      authProbeCloseAttempts=0;
      authProbeCloseLast='WAITING_FOR_AUTH_PROOF';
    }finally{
"""
assert s.count(old_click) == 1, 'menu click anchor mismatch'
s = s.replace(old_click, new_click)

old_publish = """    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
    await maybeAutoOpenAuthMenu(s);
  }
"""
new_publish = """    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
    await maybeAutoCloseAuthMenu(s);
    await maybeAutoOpenAuthMenu(s);
  }
"""
assert s.count(old_publish) == 1, 'publishStatus tail mismatch'
s = s.replace(old_publish, new_publish)

for token in [
    'findAuthMenuCloseButton',
    'AUTO_CLOSE_IS_UX_ONLY',
    'opened_sidebar_by_nexus',
    'sidebar_close_is_auth_proof:false',
    "authProbeCloseLast='CLOSED_AFTER_AUTH_PROOF'",
]:
    assert token in s, token
p.write_text(s)
