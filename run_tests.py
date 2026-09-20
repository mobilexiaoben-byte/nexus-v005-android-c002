import json,os,shutil,unittest
from pathlib import Path
if os.environ.get('REQUIRE_OPA')=='1' and not (os.environ.get('OPA_BIN') or shutil.which('opa')):
    raise SystemExit('OPA_REQUIRED: no skipped integration verification in CI')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
report={'scope':'SANDBOX_ONLY_SYNTHETIC_FIXTURES','tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),
        'skipped':len(r.skipped),'success':r.wasSuccessful(),'real_opa_available':bool(os.environ.get('OPA_BIN') or shutil.which('opa')),
        'production_verified':False,'chatgpt_roundtrip_verified':False}
Path('test-results.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if r.wasSuccessful() else 1)
