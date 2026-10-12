"""Record offline test results and the exact implementation tested."""
import contextlib
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import sys

SUITE=Path(__file__).resolve().parents[1]


def main():
    try:
        import pytest
    except ImportError:
        existing=Path('C:/Users/22142/AppData/Local/Programs/Python/Python311/Lib/site-packages')
        if existing.exists():sys.path.append(str(existing))
        import pytest
    output=io.StringIO()
    with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
        code=pytest.main([str(SUITE/'tests'),'-q','-p','no:asyncio'])
    log=output.getvalue()
    (SUITE/'verification/全部离线控制_GREEN.txt').write_text(log,'utf-8')
    report={'exit_code':int(code),'controls_passed':162 if code==0 and '162 passed' in log else None,
        'python':sys.version,'dependencies':{name:importlib.metadata.version(name) for name in ['Pillow','pypdf','pytest','reportlab']},
        'implementation_sha256':{str(p.relative_to(SUITE)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [SUITE/'_runtime.py',SUITE/'_artifact_extensions.py',SUITE/'_extensions.py',SUITE/'_text_extensions.py']},
        'test_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((SUITE/'tests').glob('test_*.py'))},
        'model_calls':0,'business_runs':0,'scope':'offline positive/negative/unknown controls, not task success results'}
    (SUITE/'verification/全部离线控制收据.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(log)
    print(json.dumps(report,ensure_ascii=False))
    return int(code)


if __name__=='__main__':raise SystemExit(main())
