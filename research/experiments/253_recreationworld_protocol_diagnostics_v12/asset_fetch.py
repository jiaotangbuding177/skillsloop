"""Explicit binary-media downloader. No HTML/CSS/source/text response accepted."""
import sys,urllib.parse,urllib.request
from pathlib import Path
url,dest=sys.argv[1:]; u=urllib.parse.urlparse(url); ext=Path(u.path).suffix.lower()
target=Path(dest).resolve(); base=Path('/workspace/recreation/public').resolve()
if u.scheme!='http' or u.hostname not in ('localhost','127.0.0.1') or ext not in {'.png','.jpg','.jpeg','.webp','.gif','.ico','.woff','.woff2','.ttf','.otf'} or not target.is_relative_to(base):
 raise SystemExit('Only explicit loopback image/font URLs and candidate public destinations are allowed.')
with urllib.request.urlopen(url,timeout=60) as r:
 if urllib.parse.urlparse(r.url).hostname not in ('localhost','127.0.0.1'): raise SystemExit('Non-loopback redirect refused.')
 mime=r.headers.get_content_type(); raw=r.read()
 if mime in ('text/html','text/css','application/javascript','application/json') or raw.lstrip().lower().startswith((b'<!doctype html',b'<html')): raise SystemExit('Reference source/text response refused.')
 target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
 print('Saved binary asset:',target.name,'bytes:',len(raw),'mime:',mime)
