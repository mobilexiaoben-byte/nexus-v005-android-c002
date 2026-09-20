"""SYNTHETIC fixtures only. No real proofs or credentials are imported."""
import argparse, copy, json, os, secrets, time
from pathlib import Path
from atelier.gateway import canonical, digest, HERE


def create_demo(directory, all_open=False):
    directory=Path(directory).resolve(); directory.mkdir(parents=True,exist_ok=True); directory.chmod(0o700)
    snapshot=json.loads((HERE/'workstreams.snapshot.json').read_text())
    def put(name,data):
        p=directory/name; p.write_bytes(data); p.chmod(0o600)
        return {'path':str(p),'sha256':digest(data)}
    candidate=put('SYNTHETIC_candidate.txt',b'NOT AN APK. SYNTHETIC CANDIDATE.\n')
    baseline=put('SYNTHETIC_baseline.txt',b'SYNTHETIC BASELINE\n')
    leaf=dict(put('SYNTHETIC_dependency.txt',b'DEPENDENCY\n'),depends_on=[])
    root=dict(put('SYNTHETIC_root.txt',b'ROOT\n'),depends_on=['dependency'])
    cfg={'mode':'SANDBOX_ONLY','fixture':True,
         'tokens':{'agent':secrets.token_hex(32),'reviewer':secrets.token_hex(32)},
         'authority_revision':digest(canonical(snapshot).encode()),
         'authority_expires_at':time.time()+3600,'authority_conflict':False,'workstreams':{}}
    for item in snapshot['workstreams']:
        wid=item['id']
        target=dict(candidate,baseline=baseline,components={'root':root,'dependency':leaf},
                    component_roots=['root'],expected_components=['root','dependency'],
                    required_evidence=['TECH','REAL'],evidence=[])
        for kind in target['required_evidence']:
            payload={'kind':kind,'workstream_id':wid,'candidate_sha256':candidate['sha256'],'result':'PASS'}
            target['evidence'].append(put(f'SYNTHETIC_{wid}_{kind}.json',canonical(payload).encode()))
        cfg['workstreams'][wid]={'status':'SYNTHETIC_OPEN' if all_open else item['status'],
                                'sandbox_mutation_enabled':bool(all_open),'targets':{'fixture':copy.deepcopy(target)}}
    p=directory/'operator-config.json'; p.write_text(json.dumps(cfg,indent=2)); p.chmod(0o600)
    c=directory/'agent-client.json'
    c.write_text(json.dumps({'token':cfg['tokens']['agent'],'endpoint':'http://127.0.0.1:8765/v1/commands'})); c.chmod(0o600)
    return p,cfg

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directory'); p.add_argument('--synthetic-open',action='store_true')
    a=p.parse_args(); os.umask(0o077); path,_=create_demo(a.directory,a.synthetic_open)
    print('SYNTHETIC fixtures only. Private operator configuration:',path)
