#!/usr/bin/env python3
"""Experiment 148 model relay: the single door for every model call.

All experiment roles go through this local relay so that (a) credentials
never leave it, (b) every upstream request is counted and logged, and
(c) a hard request cap can stop the whole experiment at a phase boundary.

Routes (forwarded to the upstream base, keeping the sub-path):
  /tau2_retail/consumer/v1/<rest> -> BigModel chat   (glm-4-flash)
  /tau2_retail/user/v1/<rest>     -> BigModel chat
  /tau2_retail/judge/v1/<rest>    -> BigModel chat
  /tau2_retail/embed/v1/<rest>    -> ECNU embeddings (ecnu-embedding-small)

Credentials are read from connection files outside the repo
(~/.skillsloop148 on Windows / /mnt/c/Users/22142/.skillsloop148 in WSL);
they are never written to the ledger, logs, or responses.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path(os.environ.get("TAU2_RETAIL_LEDGER", str(ROOT / "ledger")))
CRED_DIRS = [
    Path("/mnt/c/Users/22142/.skillsloop148"),
    Path.home() / ".skillsloop148",
    Path("C:/Users/22142/.skillsloop148"),
]
PORT = int(os.environ.get("TAU2_RETAIL_RELAY_PORT", "8141"))
DEFAULT_CAP = int(os.environ.get("TAU2_RETAIL_MAX_REQUESTS", "20000"))
UPSTREAMS = {
    "consumer": ("chat", "deepseek_connection.json"),
    "user": ("chat", "deepseek_connection.json"),
    "judge": ("chat", "upstream_connection.json"),
    "autoskill": ("chat", "upstream_connection.json"),
    "plus": ("chat", "embeddings_connection.json"),
    "embed": ("embed", "embeddings_connection.json"),
}

_lock = threading.Lock()
_state = {"requests_reserved": 0, "started_epoch": time.time(), "max_requests": DEFAULT_CAP}


def load_connection(kind: str, filename: str) -> dict:
    for directory in CRED_DIRS:
        candidate = directory / filename
        if candidate.exists():
            data = json.loads(candidate.read_text(encoding="utf-8-sig"))
            if data.get("base_url") and data.get("api_key"):
                return data
    raise SystemExit(f"connection file not found: {filename}")


def reserve() -> int | None:
    with _lock:
        if _state["requests_reserved"] >= _state["max_requests"]:
            return None
        _state["requests_reserved"] += 1
        seq = _state["requests_reserved"]
    save_state()
    return seq


def save_state() -> None:
    LEDGER.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER / "budget_state.json.tmp"
    tmp.write_text(json.dumps(_state, indent=2), encoding="utf-8")
    tmp.replace(LEDGER / "budget_state.json")


def record(entry: dict) -> None:
    LEDGER.mkdir(parents=True, exist_ok=True)
    with _lock:
        with (LEDGER / "requests.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep stderr quiet; the ledger is the record
        pass

    def _fail(self, code: int, message: str) -> None:
        payload = json.dumps({"error": {"message": message}}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):  # health
        if self.path.startswith("/health"):
            payload = json.dumps(
                {
                    "status": "ok",
                    "port": PORT,
                    "requests_reserved": _state["requests_reserved"],
                    "max_requests": _state["max_requests"],
                    "started_epoch": _state["started_epoch"],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self._fail(404, "not found")

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        # /tau2_retail/<role>/v1/<rest...>
        if len(parts) < 4 or parts[0] != "tau2_retail" or parts[2] != "v1":
            return self._fail(404, "unknown route")
        role, rest = parts[1], "/".join(parts[3:])
        if role not in UPSTREAMS:
            return self._fail(404, f"unknown role {role}")
        kind, filename = UPSTREAMS[role]
        connection = load_connection(kind, filename)

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        seq = reserve()
        started = time.time()
        if seq is None:
            record({"seq": None, "role": role, "status": "rejected_by_cap", "started_epoch": started})
            return self._fail(429, "experiment request cap reached")

        upstream_url = connection["base_url"].rstrip("/") + "/" + rest
        request = urllib.request.Request(
            upstream_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": self.headers.get("Content-Type", "application/json"),
                "Authorization": f"Bearer {connection['api_key']}",
                "Accept": self.headers.get("Accept", "application/json"),
            },
        )
        raw_dir = LEDGER / "judge_raw"
        if role == "judge":
            raw_dir.mkdir(parents=True, exist_ok=True)
            try:
                (raw_dir / f"{seq:06d}_request.json").write_bytes(body)
            except OSError:
                pass
        entry = {
            "seq": seq,
            "role": role,
            "route": self.path,
            "upstream": connection["base_url"],
            "model_hint": connection.get("model"),
            "started_at": started,
            "request_bytes": len(body),
        }
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                entry["upstream_status"] = response.status
                self.send_response(response.status)
                for name in ("Content-Type",):
                    if response.headers.get(name):
                        self.send_header(name, response.headers[name])
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                received = 0
                captured = bytearray() if role == "judge" else None
                while True:
                    chunk = response.read1(16384)
                    if not chunk:
                        break
                    received += len(chunk)
                    if captured is not None and len(captured) < 2_000_000:
                        captured.extend(chunk)
                    self.wfile.write(chunk)
                    self.wfile.flush()
                if captured is not None:
                    try:
                        (raw_dir / f"{seq:06d}_response.raw").write_bytes(bytes(captured))
                    except OSError:
                        pass
                entry["response_bytes"] = received
                entry["status"] = "completed"
        except urllib.error.HTTPError as error:
            body_bytes = error.read()
            entry.update(status="upstream_http_error", upstream_status=error.code,
                         error_class="HTTPError", response_bytes=len(body_bytes))
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(body_bytes)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body_bytes)
        except Exception as error:  # transport / timeout
            entry.update(status="transport_error", error_class=type(error).__name__)
            try:
                self._fail(502, f"relay upstream error: {type(error).__name__}")
            except OSError:
                pass
        finally:
            entry["latency_seconds"] = round(time.time() - started, 3)
            record(entry)
        self.close_connection = True


def main() -> None:
    LEDGER.mkdir(parents=True, exist_ok=True)
    save_state()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    (LEDGER / "relay_status.json").write_text(
        json.dumps({"port": PORT, "started_epoch": time.time(), "max_requests": DEFAULT_CAP}),
        encoding="utf-8",
    )
    print(f"relay ready on 127.0.0.1:{PORT} (cap={DEFAULT_CAP})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
