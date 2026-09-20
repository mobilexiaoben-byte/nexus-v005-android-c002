from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import http.client, json, os, shutil, sqlite3, tempfile, threading, time, unittest
from pathlib import Path
from unittest.mock import patch
from atelier.demo import create_demo
from atelier.gateway import Gateway, canonical, digest, make_server, strict_json, validate
OPA=os.environ.get('OPA_BIN') or shutil.which('opa')

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.path,self.cfg=create_demo(self.root,all_open=True); self.db=self.root/'state.sqlite'
        self.g=Gateway(self.path,self.db,OPA or '/nonexistent/opa'); self.seq=0
    def tearDown(self): self.temp.cleanup()
    def save(self): self.path.write_text(canonical(self.cfg))
    def target(self,wid='M-001'): return self.cfg['workstreams'][wid]['targets']['fixture']
    def command(self,action='preflight',wid='M-001',**changes):
        self.seq+=1
        r={'request_id':f'REQ-{self.seq}','action':action,'workstream_id':wid,'target_id':'fixture',
           'candidate_sha256':self.target(wid)['sha256'],'authority_revision':self.cfg['authority_revision']}
        r.update(changes); return r
    def call(self,action='preflight',wid='M-001',role='agent',**changes):
        return self.g.handle(canonical(self.command(action,wid,**changes)).encode(),self.cfg['tokens'][role])
    def counts(self):
        with closing(self.g.connect()) as db:
            return tuple(db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['state','requests','events'])

class BoundaryTests(Fixture):
    def test_schema(self):
        self.assertTrue(validate(self.command()))
        for key in ['role','approved','proof','shell','path','policy','force']:
            c=self.command(); c[key]=True
            self.assertEqual(self.g.handle(canonical(c).encode(),self.cfg['tokens']['agent'])['reason'],'INVALID_COMMAND')
        self.assertEqual(self.counts(),(0,0,0))
    def test_invalid_json(self):
        for raw in ['{"action":"inspect","action":"approve"}','NaN','Infinity','-Infinity']:
            with self.assertRaises(ValueError): strict_json(raw)
    def test_free_text_never_approves(self):
        for word in ['executer','excuter','EXECUTER','executer approve']:
            self.assertFalse(self.g.handle(word.encode(),self.cfg['tokens']['agent'])['allowed'])
    def test_missing_engine(self):
        self.g.opa='/nonexistent/opa'; r=self.call()
        self.assertFalse(r['allowed']); self.assertEqual(r['reason'],'POLICY_UNAVAILABLE_OR_INVALID')
        self.assertEqual(self.counts(),(0,1,1))
    def test_engine_crash(self):
        self.g.opa='/bin/false'; self.assertFalse(self.call()['allowed'])
    def test_policy_string_true_is_not_boolean(self):
        fake=type('Proc',(),{'stdout':'{"result":[{"expressions":[{"value":{"allow":"true","scope":"SANDBOX_ONLY"}}]}]}'})()
        with patch('atelier.gateway.subprocess.run',return_value=fake): self.assertFalse(self.call()['allowed'])
    def test_shared_credentials(self):
        self.cfg['tokens']['reviewer']=self.cfg['tokens']['agent']; self.save(); self.assertFalse(self.call()['allowed'])
    def test_bad_token(self):
        self.assertEqual(self.g.handle(canonical(self.command()).encode(),'bad')['reason'],'UNAUTHENTICATED')
    def test_unknown_target(self):
        self.assertFalse(self.call(target_id='other')['allowed']); self.assertEqual(self.counts()[0],0)
    def test_unknown_workstream(self):
        self.assertFalse(self.call(workstream_id='M-999')['allowed']); self.assertEqual(self.counts()[0],0)
    def test_request_id_collision(self):
        c=self.command(); self.g.handle(canonical(c).encode(),self.cfg['tokens']['agent']); c['action']='approve'
        self.assertEqual(self.g.handle(canonical(c).encode(),self.cfg['tokens']['reviewer'])['reason'],'REQUEST_ID_CONFLICT')
    def test_log_append_only(self):
        self.call()
        with closing(self.g.connect()) as db:
            for sql in ["UPDATE events SET payload='bad'",'DELETE FROM events']:
                with self.assertRaises(sqlite3.IntegrityError): db.execute(sql)
    def test_log_corruption(self):
        self.call()
        with closing(self.g.connect()) as db,db:
            db.execute('DROP TRIGGER events_no_update'); db.execute("UPDATE events SET payload='corrupt'")
        self.assertEqual(self.call()['reason'],'CONFIG_STATE_OR_STORAGE_INVALID')
    def test_production_ceiling(self):
        self.cfg['mode']='PRODUCTION'; self.save()
        with patch.object(self.g,'evaluate',return_value=(True,'TEST_DOUBLE')):
            self.assertEqual(self.call()['reason'],'ADAPTER_FORBIDDEN')
    def test_delete_has_no_adapter(self):
        before=Path(self.target()['path']).read_bytes()
        with patch.object(self.g,'evaluate',return_value=(True,'TEST_DOUBLE')):
            self.assertFalse(self.call('delete')['allowed'])
        self.assertEqual(Path(self.target()['path']).read_bytes(),before)

@unittest.skipUnless(OPA,'Real OPA unavailable: integration not verified in this environment')
class RealPolicyTests(Fixture):
    def test_all_47_synthetic_cycles(self):
        self.assertEqual(len(self.cfg['workstreams']),47)
        for wid in self.cfg['workstreams']:
            with self.subTest(workstream=wid):
                self.assertTrue(self.call('preflight',wid)['allowed'])
                self.assertTrue(self.call('approve',wid,role='reviewer')['allowed'])
                self.assertEqual(self.call('release',wid)['state'],'RELEASED')
        self.assertEqual(self.counts(),(47,141,141))
    def test_current_statuses_inspect_only(self):
        self.path,self.cfg=create_demo(self.root,all_open=False)
        for wid in self.cfg['workstreams']:
            self.assertTrue(self.call('inspect',wid)['allowed']); self.assertFalse(self.call('preflight',wid)['allowed'])
        self.assertEqual(self.counts()[0],0)
    def test_agent_cannot_approve(self):
        self.assertTrue(self.call()['allowed']); self.assertFalse(self.call('approve')['allowed']); self.assertFalse(self.call('release')['allowed'])
    def test_reviewer_cannot_preflight(self): self.assertFalse(self.call(role='reviewer')['allowed'])
    def test_transition_skipping(self):
        self.assertFalse(self.call('approve',role='reviewer')['allowed']); self.assertFalse(self.call('release')['allowed'])
    def test_closed_workstream(self):
        self.cfg['workstreams']['M-001']['status']='CLOSED'; self.save()
        self.assertTrue(self.call('inspect')['allowed']); self.assertFalse(self.call()['allowed'])
    def test_stale_authority(self): self.assertFalse(self.call(authority_revision='0'*64)['allowed'])
    def test_expired_authority(self):
        self.cfg['authority_expires_at']=time.time()-1; self.save(); self.assertFalse(self.call()['allowed'])
    def test_conflict(self):
        self.cfg['authority_conflict']=True; self.save(); self.assertFalse(self.call()['allowed'])
    def test_wrong_candidate_hash(self): self.assertFalse(self.call(candidate_sha256='0'*64)['allowed'])
    def test_modified_candidate(self):
        Path(self.target()['path']).write_bytes(b'changed'); self.assertFalse(self.call()['allowed'])
    def test_missing_baseline(self):
        Path(self.target()['baseline']['path']).unlink(); self.assertFalse(self.call()['allowed'])
    def test_modified_baseline(self):
        Path(self.target()['baseline']['path']).write_bytes(b'changed'); self.assertFalse(self.call()['allowed'])
    def test_missing_dependency(self):
        del self.target()['components']['dependency']; self.save(); self.assertFalse(self.call()['allowed'])
    def test_dependency_cycle(self):
        self.target()['components']['dependency']['depends_on']=['root']; self.save(); self.assertFalse(self.call()['allowed'])
    def test_bom_mismatch(self):
        self.target()['expected_components'].append('extra'); self.save(); self.assertFalse(self.call()['allowed'])
    def test_dependency_bytes(self):
        Path(self.target()['components']['dependency']['path']).write_bytes(b'changed'); self.assertFalse(self.call()['allowed'])
    def test_tech_not_real(self):
        self.target()['evidence'].pop(); self.save(); self.assertFalse(self.call()['allowed'])
    def rewrite_proof(self,field,value):
        r=self.target()['evidence'][0]; p=Path(r['path']); data=strict_json(p.read_bytes()); data[field]=value
        p.write_text(canonical(data)); r['sha256']=digest(p.read_bytes()); self.save()
    def test_wrong_version_proof(self):
        self.rewrite_proof('candidate_sha256','0'*64); self.assertFalse(self.call()['allowed'])
    def test_other_workstream_proof(self):
        self.rewrite_proof('workstream_id','U-011'); self.assertFalse(self.call()['allowed'])
    def test_failed_proof(self):
        self.rewrite_proof('result','FAIL'); self.assertFalse(self.call()['allowed'])
    def test_missing_raw_proof(self):
        Path(self.target()['evidence'][0]['path']).unlink(); self.assertFalse(self.call()['allowed'])
    def test_symlink(self):
        p=Path(self.target()['path']); saved=p.with_suffix('.saved'); p.rename(saved); p.symlink_to(saved)
        self.assertFalse(self.call()['allowed'])
    def test_config_change_invalidates_approval(self):
        self.assertTrue(self.call()['allowed']); self.assertTrue(self.call('approve',role='reviewer')['allowed'])
        self.target()['required_evidence'].append('NEW'); self.save(); self.assertFalse(self.call('release')['allowed'])
    def test_bytes_change_after_approval(self):
        self.assertTrue(self.call()['allowed']); self.assertTrue(self.call('approve',role='reviewer')['allowed'])
        Path(self.target()['path']).write_bytes(b'changed'); self.assertFalse(self.call('release')['allowed'])
    def test_idempotency_is_receipt_not_permission(self):
        c=self.command(); raw=canonical(c).encode(); token=self.cfg['tokens']['agent']
        self.assertTrue(self.g.handle(raw,token)['allowed']); r=self.g.handle(raw,token)
        self.assertFalse(r['allowed']); self.assertEqual(r['reason'],'ALREADY_PROCESSED')
        self.assertTrue(r['historical_receipt']['allowed']); self.assertEqual(self.counts(),(1,1,1))
    def test_concurrent_requests_once(self):
        raw=canonical(self.command()).encode(); token=self.cfg['tokens']['agent']
        with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(lambda _: self.g.handle(raw,token),range(6)))
        self.assertEqual(sum(x['allowed'] for x in results),1); self.assertEqual(self.counts(),(1,1,1))
    def test_restart(self):
        raw=canonical(self.command()).encode(); token=self.cfg['tokens']['agent']
        self.assertTrue(self.g.handle(raw,token)['allowed']); self.g=Gateway(self.path,self.db,OPA)
        self.assertEqual(self.g.handle(raw,token)['reason'],'ALREADY_PROCESSED')
        self.assertTrue(self.call('approve',role='reviewer')['allowed']); self.assertEqual(self.call('release')['state'],'RELEASED')
    def test_transaction_rollback(self):
        with patch.object(self.g,'log',side_effect=sqlite3.OperationalError('disk full')): self.assertFalse(self.call()['allowed'])
        self.assertEqual(self.counts(),(0,0,0))
    def test_approval_not_transferable(self):
        self.assertTrue(self.call()['allowed']); self.assertTrue(self.call('approve',role='reviewer')['allowed'])
        self.assertFalse(self.call('release','U-011')['allowed'])
    def test_http(self):
        server=make_server(self.g); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            for action,expected in [('preflight',200),('approve',403)]:
                c.request('POST','/v1/commands',canonical(self.command(action)),{'Content-Type':'application/json','Authorization':'Bearer '+self.cfg['tokens']['agent']})
                r=c.getresponse(); data=json.loads(r.read()); self.assertEqual(r.status,expected); self.assertFalse(data['external_effect'])
            c.close()
        finally: server.shutdown(); server.server_close(); thread.join()
