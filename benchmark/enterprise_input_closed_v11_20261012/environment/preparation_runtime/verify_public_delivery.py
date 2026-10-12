"""Independent current-workspace HTTP verification before container teardown."""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def verify_public_delivery(workspace, *, deadline=None):
    workspace = Path(workspace).resolve()
    receipt = {"schema": "independent-public-current-workspace-acceptance-v7", "passed": False,
        "actor_pass_flag_ignored": True, "acceptance_reads_only_selected_output_files": True,
        "acceptance_at_unix": time.time(), "checks": []}
    def check(name, passed, **fields):
        receipt["checks"].append({"name": name, "passed": bool(passed), **fields})
    try:
        pointer = json.loads((workspace / ".public_delivery/current.json").read_text(encoding="utf-8"))
        publication_id = str(pointer["publication_id"])
        if not publication_id.isalnum():
            raise ValueError("Invalid publication identity")
        state_path = workspace / ".public_delivery/publications" / publication_id / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        directory = (workspace / pointer["relative_directory"]).resolve()
        outputs = (workspace / "outputs").resolve()
        check("explicit_current_outputs_subdirectory", outputs in directory.parents and directory.is_dir())
        if not receipt["checks"][-1]["passed"]:
            return receipt
        url = str(state["public_url"]).rstrip("/")
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname or ""
        check("actual_allocated_public_https_host", parsed.scheme == "https" and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment and (host.endswith(".lhr.life") or host.endswith(".localhost.run"))
            and host not in {"admin.localhost.run", "www.localhost.run"})
        if not receipt["checks"][-1]["passed"]:
            return receipt
        receipt.update({"publication_id": publication_id, "public_url": url, "relative_directory": pointer["relative_directory"],
            "lifetime_scope": "complete-source acceptance before container cleanup; not permanent hosting"})
        actual_files = {}
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError("Exported directory contains a symlink")
            if path.is_file(): actual_files[path.relative_to(directory).as_posix()] = path
        check("current_site_has_index", "index.html" in actual_files)
        check("publish_allowlist_matches_current_output_files", set(actual_files) == set(state.get("files", {})))
        if not all(x["passed"] for x in receipt["checks"]):
            return receipt
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        def get(path):
            remaining = 20 if deadline is None else min(20, deadline - time.monotonic())
            if remaining <= 0:
                raise TimeoutError('Independent public acceptance deadline exhausted')
            request = urllib.request.Request(url + path, headers={"Cache-Control": "no-cache", "Accept-Encoding": "identity"})
            with opener.open(request, timeout=remaining) as response:
                chunks = []
                while True:
                    if deadline is not None and time.monotonic() >= deadline:
                        raise TimeoutError('Independent public acceptance deadline exhausted')
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                body = b''.join(chunks)
                if urllib.parse.urlsplit(response.geturl()).hostname != host:
                    raise ValueError("Public request redirected to another host")
                return response.status, body
        challenge = secrets.token_hex(24)
        status, body = get("/__skillloop_public_delivery_nonce__?challenge=" + challenge)
        nonce = json.loads(body.decode())
        check("fresh_public_nonce_challenge", status == 200 and nonce.get("challenge") == challenge
            and nonce.get("publication_id") == publication_id and nonce.get("nonce") == state.get("nonce"),
            challenge_sha256=hashlib.sha256(challenge.encode()).hexdigest())
        for relative, path in actual_files.items():
            expected = path.read_bytes()
            route = "/" if relative == "index.html" else "/" + urllib.parse.quote(relative, safe="/")
            status, body = get(route)
            check("actual_public_file:" + relative, status == 200 and body == expected,
                bytes=len(expected), workspace_sha256=hashlib.sha256(expected).hexdigest(), public_sha256=hashlib.sha256(body).hexdigest(), http_status=status)
        check("state_not_stopped_at_acceptance", not state.get("stopped", False))
        receipt["passed"] = all(x["passed"] for x in receipt["checks"])
        receipt["verified_files"] = len(actual_files)
    except Exception as error:
        receipt.update({"error_type": type(error).__name__, "http_status": error.code if isinstance(error, urllib.error.HTTPError) else None})
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--output")
    args = parser.parse_args()
    receipt = verify_public_delivery(args.workspace)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["passed"] else 2


if __name__ == "__main__": raise SystemExit(main())
