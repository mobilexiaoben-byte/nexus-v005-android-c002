"""Atelier NEXUS: local, generic SANDBOX_ONLY command gateway.
No production adapters or credentials. Operator-owned config and policy are trusted.
The caller can supply commands, never role, proof results, paths or permissions.
"""
import argparse
from contextlib import closing
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / 'command.schema.json').read_text())
POLICY = HERE / 'sandbox.rego'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('DUPLICATE_KEY')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('NON_JSON_CONSTANT')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def validate(command):
    # Closed flat-string subset, not a general-purpose JSON Schema validator.
    if type(command) is not dict or set(command) != set(SCHEMA['required']):
        return False
    for key, rule in SCHEMA['properties'].items():
        value = command[key]
        if type(value) is not str:
            return False
        if 'enum' in rule and value not in rule['enum']:
            return False
        if 'pattern' in rule and not re.fullmatch(rule['pattern'], value):
            return False
    return True


def denied(reason):
    return {'allowed': False, 'reason': reason, 'scope': 'SANDBOX_ONLY', 'external_effect': False}


def record_bytes(record):
    # All paths and expected hashes originate in the operator configuration.
    if type(record) is not dict:
        raise ValueError('BAD_FILE_RECORD')
    path = Path(record['path'])
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('UNSAFE_OR_OVERSIZED_FILE')
    data = path.read_bytes()
    if digest(data) != record['sha256']:
        raise ValueError('FILE_HASH_MISMATCH')
    return data


def components_valid(target):
    components = target['components']
    expected = target['expected_components']
    roots = target['component_roots']
    if not roots or len(expected) != len(set(expected)) or set(expected) != set(components):
        return False
    visited, visiting = set(), set()
    def visit(cid):
        if cid in visiting or cid not in components:
            raise ValueError('DEPENDENCY_CYCLE_OR_MISSING')
        if cid in visited:
            return
        visiting.add(cid)
        component = components[cid]
        record_bytes(component)
        for dependency in component['depends_on']:
            visit(dependency)
        visiting.remove(cid)
        visited.add(cid)
    for root in roots:
        visit(root)
    return visited == set(expected)


def evidence_valid(target, wid):
    expected, proofs = target['required_evidence'], target['evidence']
    if not expected or len(set(expected)) != len(expected) or len(proofs) != len(expected):
        return False
    found = set()
    for proof in proofs:
        payload = strict_json(record_bytes(proof))
        if set(payload) != {'kind', 'workstream_id', 'candidate_sha256', 'result'}:
            return False
        if payload['workstream_id'] != wid or payload['candidate_sha256'] != target['sha256']:
            return False
        if payload['result'] != 'PASS' or payload['kind'] not in expected or payload['kind'] in found:
            return False
        found.add(payload['kind'])
    return found == set(expected)


class Gateway:
    def __init__(self, config_path, database, opa='opa'):
        self.config_path = Path(config_path)
        self.database = str(database)
        self.opa = opa
        with closing(self.connect()) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS state (
                    workstream TEXT, target TEXT, binding TEXT NOT NULL, state TEXT NOT NULL,
                    PRIMARY KEY(workstream,target));
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, response TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END;
            ''')

    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.execute('PRAGMA busy_timeout=10000')
        return db

    @staticmethod
    def verify_log(db):
        previous, expected_seq = '0' * 64, 1
        for seq, payload, prev_hash, hashed in db.execute('SELECT * FROM events ORDER BY seq'):
            if seq != expected_seq or prev_hash != previous or digest((previous + payload).encode()) != hashed:
                raise ValueError('AUDIT_INTEGRITY_FAILURE')
            expected_seq += 1
            previous = hashed

    @staticmethod
    def log(db, event):
        row = db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        previous = row[0] if row else '0' * 64
        payload = canonical(event)
        hashed = digest((previous + payload).encode())
        db.execute('INSERT INTO events(payload,prev_hash,hash) VALUES(?,?,?)', (payload, previous, hashed))

    def evaluate(self, observed):
        try:
            proc = subprocess.run(
                [self.opa, 'eval', '--format=json', '--data', str(POLICY),
                 '--stdin-input', 'data.nexus.atelier.sandbox.decision'],
                input=canonical(observed), text=True, capture_output=True, timeout=5, check=True)
            doc = strict_json(proc.stdout)
            result = doc['result'][0]['expressions'][0]['value']
            if type(result) is not dict or type(result.get('allow')) is not bool:
                return False, 'INVALID_POLICY_RESPONSE'
            return result == {'allow': True, 'scope': 'SANDBOX_ONLY'}, 'POLICY_DECISION'
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError, TypeError):
            return False, 'POLICY_UNAVAILABLE_OR_INVALID'

    def handle(self, raw, token):
        if len(raw) > 8192:
            return denied('REQUEST_TOO_LARGE')
        try:
            cfg = strict_json(self.config_path.read_bytes())
            tokens = cfg['tokens']
            if set(tokens) != {'agent', 'reviewer'} or any(
                type(v) is not str or len(v) < 32 or not v.isascii() for v in tokens.values()
            ) or tokens['agent'] == tokens['reviewer']:
                raise ValueError('INVALID_CREDENTIAL_SEPARATION')
            if type(token) is not str or not token.isascii():
                return denied('UNAUTHENTICATED')
            role = next((k for k, v in tokens.items() if hmac.compare_digest(v, token)), None)
            if role is None:
                return denied('UNAUTHENTICATED')
            command = strict_json(raw)
            if not validate(command):
                return denied('INVALID_COMMAND')
            with closing(self.connect()) as db, db:
                db.execute('BEGIN IMMEDIATE')
                self.verify_log(db)
                return self.transact(db, cfg, command, role)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, sqlite3.Error):
            return denied('CONFIG_STATE_OR_STORAGE_INVALID')

    def transact(self, db, cfg, command, role):
        fingerprint = digest(canonical({'role': role, 'command': command}).encode())
        cached = db.execute('SELECT fingerprint,response FROM requests WHERE request_id=?',
                            (command['request_id'],)).fetchone()
        if cached:
            if cached[0] != fingerprint:
                response = denied('REQUEST_ID_CONFLICT')
                self.log(db, {'role': role, 'command': command, 'response': response})
                return response
            # An old receipt is never a renewed permission to execute.
            return {'allowed': False, 'reason': 'ALREADY_PROCESSED', 'scope': 'SANDBOX_ONLY',
                    'external_effect': False, 'historical_receipt': strict_json(cached[1])}
        wid, tid = command['workstream_id'], command['target_id']
        stream = cfg['workstreams'].get(wid)
        target = stream.get('targets', {}).get(tid) if type(stream) is dict else None
        if type(target) is not dict:
            response = denied('UNKNOWN_WORKSTREAM_OR_TARGET')
            return self.save(db, command, role, fingerprint, response, {})
        binding = digest(canonical({
            'authority_revision': cfg['authority_revision'], 'stream': stream,
            'mode': cfg['mode'], 'policy_sha256': digest(POLICY.read_bytes()),
        }).encode())
        row = db.execute('SELECT binding,state FROM state WHERE workstream=? AND target=?', (wid, tid)).fetchone()
        state = row[1] if row and row[0] == binding else 'DRAFT'
        candidate_ok = baseline_ok = components_ok = evidence_ok = False
        try:
            record_bytes(target)
            candidate_ok = command['candidate_sha256'] == target['sha256']
            record_bytes(target['baseline'])
            baseline_ok = True
            components_ok = components_valid(target)
            evidence_ok = evidence_valid(target, wid)
        except (OSError, KeyError, TypeError, ValueError, RecursionError):
            pass
        expiry = cfg.get('authority_expires_at')
        fresh = (type(expiry) in (int, float) and math.isfinite(expiry) and time.time() < expiry
                 and command['authority_revision'] == cfg['authority_revision'])
        observed = {
            'mode': cfg['mode'], 'schema_valid': True, 'role': role, 'action': command['action'],
            'state': state, 'authority_fresh': fresh,
            'authority_conflict': cfg.get('authority_conflict', True),
            'candidate_match': candidate_ok, 'baseline_verified': baseline_ok,
            'components_verified': components_ok, 'evidence_verified': evidence_ok,
            'workstream_mutation_enabled': stream.get('sandbox_mutation_enabled') is True,
            'workstream_closed': stream.get('status') == 'CLOSED',
        }
        allowed, reason = self.evaluate(observed)
        transitions = {'preflight': 'CHECKED', 'approve': 'APPROVED', 'release': 'RELEASED'}
        # Unconditional adapter ceiling. No live mode or delete implementation exists.
        if cfg['mode'] != 'SANDBOX_ONLY' or command['action'] == 'delete':
            allowed, reason = False, 'ADAPTER_FORBIDDEN'
        new_state = transitions.get(command['action'], state) if allowed else state
        if allowed and command['action'] in transitions:
            db.execute('INSERT INTO state VALUES(?,?,?,?) ON CONFLICT(workstream,target) DO UPDATE SET '
                       'binding=excluded.binding,state=excluded.state', (wid, tid, binding, new_state))
        response = {'allowed': allowed, 'reason': reason, 'state': new_state,
                    'scope': 'SANDBOX_ONLY', 'external_effect': False, 'request_id': command['request_id'],
                    'workstream_id': wid, 'target_id': tid}
        return self.save(db, command, role, fingerprint, response, observed)

    def save(self, db, command, role, fingerprint, response, observed):
        db.execute('INSERT INTO requests VALUES(?,?,?)', (command['request_id'], fingerprint, canonical(response)))
        self.log(db, {'role': role, 'command': command, 'observations': observed, 'response': response})
        return response


def make_server(gateway, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.connection.settimeout(5)
            if self.path != '/v1/commands':
                self.send_error(404)
                return
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or len(self.headers.get_all('Authorization', [])) != 1:
                    self.send_error(400)
                    return
                length = int(lengths[0])
                if not 0 < length <= 8192 or self.headers.get('Transfer-Encoding'):
                    self.send_error(413)
                    return
                if self.headers.get('Content-Type') != 'application/json':
                    self.send_error(415)
                    return
                auth = self.headers.get('Authorization', '')
                token = auth[7:] if auth.startswith('Bearer ') else ''
                raw = self.rfile.read(length)
                if len(raw) != length:
                    self.send_error(400)
                    return
                result = gateway.handle(raw, token)
                body = canonical(result).encode()
                self.send_response(200 if result.get('allowed') else 403)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (ValueError, sqlite3.Error, OSError):
                self.send_error(503)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--opa', default='opa')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    os.umask(0o077)
    server = make_server(Gateway(args.config, args.database, args.opa), args.port)
    print('SANDBOX_ONLY on http://127.0.0.1:%s/v1/commands' % server.server_port, flush=True)
    server.serve_forever()
