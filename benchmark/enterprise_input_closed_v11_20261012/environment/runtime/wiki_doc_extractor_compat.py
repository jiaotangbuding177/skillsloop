"""Run unchanged original wiki extractor with the current odfdo constructor API."""
import argparse
from pathlib import Path
import runpy
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skill-dir',default='/workspace/skills/karpathy-wiki');p.add_argument('arguments',nargs=argparse.REMAINDER)
    a=p.parse_args();args=a.arguments
    if args and args[0]=='--':args=args[1:]
    script=Path(a.skill_dir).resolve()/'scripts/doc_extractor.py'
    if not script.is_file():p.error('Original wiki extractor is absent: '+str(script))
    from odfdo import Document
    if not hasattr(Document,'open'):
        Document.open=staticmethod(lambda filepath:Document(filepath))
    sys.argv=[str(script),*args]
    runpy.run_path(str(script),run_name='__main__')

if __name__=='__main__':main()
