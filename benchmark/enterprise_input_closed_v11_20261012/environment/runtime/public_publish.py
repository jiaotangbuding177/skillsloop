"""Publish one current outputs directory through a finite SSH public tunnel."""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import mimetypes
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

STATE_DIR = ".public_delivery"
EVENT_TYPE = "v1.tcpip_forward.register.accepted"
NONCE_PATH = "/__skillloop_public_delivery_nonce__"


def sha(value): return hashlib.sha256(value).hexdigest()
def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def directory_files(directory):
    files = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_symlink():
            raise ValueError("Only current directory files may be published")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = path
    if "index.html" not in files:
        raise ValueError("The selected output directory needs index.html")
    return files


def resolve_site(workspace, directory):
    workspace = Path(workspace).resolve()
    outputs = (workspace / "outputs").resolve()
    raw = Path(directory)
    raw = raw if raw.is_absolute() else workspace / raw
    site = raw.resolve()
    if site == outputs or outputs not in site.parents or not site.is_dir():
        raise ValueError("Select an explicit existing subdirectory of workspace/outputs")
    directory_files(site)
    return workspace, site


def public_url_from_event_lines(text):
    """Ignore the welcome banner and administration/docs links entirely."""
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") != EVENT_TYPE or not isinstance(event.get("data"), str):
            continue
        for candidate in re.findall(r"https://[A-Za-z0-9.-]+", event["data"]):
            host = urllib.parse.urlsplit(candidate).hostname or ""
            if (host.endswith(".lhr.life") or host.endswith(".localhost.run")) and host not in {"admin.localhost.run", "www.localhost.run"}:
                return candidate.rstrip("/")
    return None


def serve(publication_path):
    publication_path = Path(publication_path)
    state = json.loads((publication_path / "request.json").read_text(encoding="utf-8"))
    workspace, directory = resolve_site(state["workspace"], state["relative_directory"])
    files = directory_files(directory)
    state.update({"publisher_pid": os.getpid(), "files": {k: {"sha256": sha(v.read_bytes()), "bytes": v.stat().st_size} for k, v in files.items()}})
    stopping = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            path = urllib.parse.unquote(parsed.path)
            if path == NONCE_PATH:
                challenge = urllib.parse.parse_qs(parsed.query).get("challenge", [""])[0]
                body = json.dumps({"publication_id": state["publication_id"], "nonce": state["nonce"], "challenge": challenge}).encode()
                content_type = "application/json"
            else:
                relative = "index.html" if path == "/" else path.lstrip("/")
                if relative not in files or any(x in {".", ".."} for x in relative.split("/")):
                    self.send_error(404)
                    return
                current = files[relative]
                if not current.is_file() or current.is_symlink() or directory not in current.resolve().parents:
                    self.send_error(404)
                    return
                body = current.read_bytes()
                content_type = mimetypes.guess_type(relative)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log_path = publication_path / "ssh.native.log"
    command = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=accept-new", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes", "-R", "80:127.0.0.1:" + str(server.server_port),
        "nokey@localhost.run", "--", "--output", "json"]
    process = None
    def halt(signum, frame): stopping.set()
    signal.signal(signal.SIGTERM, halt)
    signal.signal(signal.SIGINT, halt)
    try:
        with log_path.open("wb") as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
            state.update({"ssh_pid": process.pid, "local_port": server.server_port,
                "publisher_cli_sha256": sha(Path(__file__).read_bytes()), "lifetime_scope": "until complete-source acceptance and explicit stop / container teardown",
                "permanent_hosting": False, "url_parse_basis": EVENT_TYPE + " event.data only"})
            write_json(publication_path / "state.json", state)
            start = time.monotonic()
            while time.monotonic() - start < 40:
                if stopping.is_set() or process.poll() is not None:
                    raise RuntimeError("Public SSH tunnel ended before a URL was assigned")
                url = public_url_from_event_lines(log_path.read_text(encoding="utf-8", errors="replace"))
                if url:
                    state["public_url"] = url
                    write_json(publication_path / "state.json", state)
                    write_json(workspace / STATE_DIR / "current.json", {"publication_id": state["publication_id"], "relative_directory": state["relative_directory"]})
                    break
                time.sleep(0.2)
            else:
                raise TimeoutError("Public SSH tunnel URL was not assigned")
            while not stopping.wait(0.5):
                if process.poll() is not None:
                    state["transport_ended_before_cleanup"] = True
                    break
    except Exception as error:
        state["error_type"] = type(error).__name__
    finally:
        if process and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=3)
        server.shutdown()
        server.server_close()
        state.update({"stopped": True, "ssh_exit_code": process.returncode if process else None, "publisher_stopped_at_unix": time.time()})
        write_json(publication_path / "state.json", state)


def publish(workspace, directory, session_id="conv_60fd9245d56a", attempt_id=None):
    workspace, site = resolve_site(workspace, directory)
    publication_id = secrets.token_hex(12)
    location = workspace / STATE_DIR / "publications" / publication_id
    location.mkdir(parents=True, exist_ok=False)
    request = {"schema": "finite-current-source-publication-v7", "publication_id": publication_id,
        "workspace": str(workspace), "relative_directory": site.relative_to(workspace).as_posix(),
        "session_id": session_id, "attempt_id": attempt_id or os.environ.get("BENCH_ATTEMPT_ID"),
        "nonce": secrets.token_hex(24), "requested_at_unix": time.time()}
    write_json(location / "request.json", request)
    with (location / "publisher.native.log").open("wb") as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_serve", "--publication-path", str(location)],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
    start = time.monotonic()
    while time.monotonic() - start < 45:
        path = location / "state.json"
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
            if state.get("public_url") and not state.get("stopped"):
                return {"publication_id": publication_id, "public_url": state["public_url"],
                    "relative_directory": request["relative_directory"], "published_file_count": len(state["files"]),
                    "lifetime_scope": state["lifetime_scope"], "public_acceptance_passed": None,
                    "verification_required_before_teardown": True}
            if state.get("error_type") or state.get("stopped"):
                raise RuntimeError("Public publisher failed; inspect its native state and logs")
        if process.poll() is not None:
            raise RuntimeError("Publisher process exited before readiness")
        time.sleep(0.2)
    if process.poll() is None:
        process.terminate()
    raise TimeoutError("Public publisher readiness timeout")


def stop_public_delivery(workspace):
    """Call in the source container's PID namespace; never kill host PID aliases."""
    workspace = Path(workspace).resolve()
    stopped, rejected = [], []
    for path in (workspace / STATE_DIR / "publications").glob("*/state.json"):
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("stopped"):
            continue
        pid = state.get("publisher_pid")
        command_path = Path("/proc") / str(pid) / "cmdline"
        if os.name != "posix" or not command_path.exists():
            rejected.append({"publication_id": state["publication_id"], "reason": "publisher PID namespace unavailable"})
            continue
        arguments = command_path.read_bytes().split(b"\0")
        if str(path.parent).encode() not in arguments or b"_serve" not in arguments:
            rejected.append({"publication_id": state["publication_id"], "reason": "PID belongs to another process"})
            continue
        os.kill(pid, signal.SIGTERM)
        stopped.append(state["publication_id"])
    start = time.monotonic()
    while time.monotonic() - start < 5:
        pending = [p for p in (workspace / STATE_DIR / "publications").glob("*/state.json")
            if json.loads(p.read_text(encoding="utf-8")).get("publication_id") in stopped
            and not json.loads(p.read_text(encoding="utf-8")).get("stopped")]
        if not pending:
            break
        time.sleep(0.2)
    return {"stopped_publication_ids": stopped, "cleanup_rejected": rejected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("publish")
    start.add_argument("--workspace", default="/workspace")
    start.add_argument("--directory", required=True)
    start.add_argument("--session-id", default="conv_60fd9245d56a")
    start.add_argument("--attempt-id")
    worker = sub.add_parser("_serve")
    worker.add_argument("--publication-path", required=True)
    stop = sub.add_parser("stop")
    stop.add_argument("--workspace", default="/workspace")
    args = parser.parse_args()
    try:
        if args.command == "_serve": serve(args.publication_path); return 0
        result = publish(args.workspace, args.directory, args.session_id, args.attempt_id) if args.command == "publish" else stop_public_delivery(args.workspace)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error_type": type(error).__name__}))
        return 2


if __name__ == "__main__": raise SystemExit(main())
