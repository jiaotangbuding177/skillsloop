#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def download(url, out, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent":"xiaolongxia-artifact-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(out, "wb") as f:
        shutil.copyfileobj(r, f)

def find_entrypoint(root):
    root = Path(root)
    patterns = ["00_MASTER_PROMPT*.md","MASTER_PROMPT*.md","README*.md","SKILL.md"]
    for pat in patterns:
        hits = sorted(root.rglob(pat))
        if hits:
            return str(hits[0])
    return None

def extract(path, dest):
    path = Path(path)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    lower = path.name.lower()
    if lower.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(path) as z:
            z.extractall(dest)
    elif lower.endswith((".tar.gz",".tgz",".tar")):
        import tarfile
        with tarfile.open(path) as t:
            t.extractall(dest)
    else:
        return None
    return find_entrypoint(dest)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", action="append", default=[])
    p.add_argument("--fallback", action="append", default=[])
    p.add_argument("--sha256")
    p.add_argument("--output", required=True)
    p.add_argument("--extract")
    p.add_argument("--timeout", type=int, default=12)
    args = p.parse_args()
    urls = args.url + args.fallback
    if not urls:
        p.error("at least one --url is required")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    success = None
    errors = []
    for url in urls:
        for attempt in range(1,3):
            try:
                print(f"[download] {url} attempt={attempt}", file=sys.stderr)
                tmp = out.with_suffix(out.suffix + ".part")
                if tmp.exists(): tmp.unlink()
                download(url, tmp, args.timeout)
                tmp.replace(out)
                success = url
                break
            except Exception as e:
                errors.append(f"{url} attempt {attempt}: {e}")
                time.sleep(1)
        if success:
            break
    if not success:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(3)

    actual = sha256_file(out)
    verified = None
    if args.sha256:
        verified = actual.lower() == args.sha256.lower()
        if not verified:
            print(f"SHA256 mismatch\nexpected={args.sha256}\nactual={actual}", file=sys.stderr)
            sys.exit(4)
    else:
        verified = False
        print("WARNING: no SHA256 supplied; artifact is UNVERIFIED", file=sys.stderr)

    entrypoint = None
    if args.extract:
        entrypoint = extract(out, args.extract)

    receipt = {
        "source_url": success,
        "sha256": actual,
        "verified": verified,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "output": str(out),
        "entrypoint": entrypoint,
        "errors_before_success": errors
    }
    Path(".delivery_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
