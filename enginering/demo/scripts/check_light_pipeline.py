"""Free regression gate; model replies are authored fixtures, never live fallback."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from skilldemo.pipeline import source_configuration


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT/'artifacts'/'lightpipeline-review'/('full-regression-'+stamp)
    folder.mkdir(parents=True)
    before = source_configuration()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    output = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    after = source_configuration()
    log = output.getvalue()
    (folder/'tests.txt').write_text(log, encoding='utf-8')
    report = {'kind':'FREE_AUTHORED_FIXTURE_REGRESSION_NOT_SEMANTIC_BENCHMARK',
        'tests':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
        'skipped':len(result.skipped), 'seconds':round(time.monotonic()-started,3),
        'modelCalls':0, 'sourceUnchanged':before==after, 'configuration':before,
        'passed':result.wasSuccessful() and before==after}
    (folder/'gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='configuration'},ensure_ascii=False))
    print(str(folder))
    if not report['passed']:
        print(log[-10000:])
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
