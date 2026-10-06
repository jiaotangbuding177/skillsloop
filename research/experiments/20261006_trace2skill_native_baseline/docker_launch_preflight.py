"""Start the existing Docker Desktop once, then bounded read-only daemon probes.

No install, settings change, license acceptance, restart, image/container launch,
model request, or credential read. Records failure rather than system fallback.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RECORDS = OUT / "private/docker_launch_001"
REPORT = OUT / "docker_launch_readiness.json"
DESKTOP = Path("C:/Program Files/Docker/Docker/Docker Desktop.exe")
DOCKER = Path("C:/Program Files/Docker/Docker/resources/bin/docker.exe")
POWERSHELL = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
FORMAT = "{{.ServerVersion}}|{{.OSType}}|{{.OperatingSystem}}|{{.KernelVersion}}|{{.Architecture}}"


def utc():
    return datetime.now(timezone.utc).isoformat()


def store(name, data):
    path = RECORDS / name
    with path.open("xb") as stream:
        stream.write(data)
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main():
    for path in (RECORDS, REPORT):
        assert path.resolve().is_relative_to(ROOT.resolve())
        if path.exists():
            raise SystemExit("Refusing to overwrite/relaunch a previous Docker start attempt")
    RECORDS.mkdir(parents=True)
    report = {"schema": "existing-docker-one-launch-preflight-v1", "started_utc": utc(),
        "status": "DAEMON_NOT_VERIFIED", "desktop_path": str(DESKTOP), "docker_cli": str(DOCKER),
        "model_calls": 0, "credentials_read": False, "installs": 0,
        "settings_changed": False, "license_accepted": False, "computer_restarted": False,
        "images_downloaded": 0, "containers_started": 0, "launch_calls": 0,
        "window_style": "Hidden", "probe_deadline_seconds": 120,
        "probe_target_offsets_seconds": [0, 25, 50, 75, 100, 120], "checks": []}
    if not DESKTOP.is_file() or not DOCKER.is_file():
        report["status"] = "EXISTING_BINARY_MISSING_NO_INSTALL_ATTEMPTED"
    else:
        # One authorized UI startup, using the required hidden style. No UI interaction.
        command = "$ErrorActionPreference='Stop'; $taskDockerProcess=Start-Process -FilePath 'C:/Program Files/Docker/Docker/Docker Desktop.exe' -WindowStyle Hidden -PassThru; $taskDockerProcess | Select-Object Id,ProcessName | ConvertTo-Json -Compress"
        report["launch_calls"] = 1
        try:
            launch = subprocess.run([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", command],
                                    capture_output=True, timeout=20)
            report["launch"] = {"exit_code": launch.returncode, "command": "Start-Process -FilePath <existing Docker Desktop.exe> -WindowStyle Hidden -PassThru",
                "stdout": launch.stdout.decode("utf-8", errors="replace"), "stderr": launch.stderr.decode("utf-8", errors="replace"),
                "stdout_raw": store("launch.stdout.bin", launch.stdout), "stderr_raw": store("launch.stderr.bin", launch.stderr)}
        except subprocess.TimeoutExpired as error:
            report["status"] = "START_PROCESS_CALL_TIMED_OUT_NO_SECOND_LAUNCH"
            report["launch_timeout"] = True
            report["launch_stdout_raw"] = store("launch.stdout.bin", error.stdout or b"")
            report["launch_stderr_raw"] = store("launch.stderr.bin", error.stderr or b"")
            launch = None
        if launch is not None and launch.returncode == 0:
            began = time.monotonic()
            for index, offset in enumerate(report["probe_target_offsets_seconds"]):
                remaining_wait = offset - (time.monotonic() - began)
                if remaining_wait > 0:
                    time.sleep(remaining_wait)
                remaining = 120 - (time.monotonic() - began)
                if remaining <= 0:
                    break
                stamp = utc()
                try:
                    result = subprocess.run([str(DOCKER), "info", "--format", FORMAT], capture_output=True,
                                            timeout=min(10, remaining))
                    out, err, returncode, timeout = result.stdout, result.stderr, result.returncode, False
                except subprocess.TimeoutExpired as error:
                    out, err, returncode, timeout = error.stdout or b"", error.stderr or b"", None, True
                decoded = out.decode("utf-8", errors="replace").strip()
                fields = decoded.split("|")
                record = {"checked_utc": stamp, "elapsed_seconds": round(time.monotonic() - began, 3),
                    "exit_code": returncode, "timeout": timeout, "stdout": decoded,
                    "stderr": err.decode("utf-8", errors="replace"),
                    "stdout_raw": store(f"check_{index:02d}.stdout.bin", out),
                    "stderr_raw": store(f"check_{index:02d}.stderr.bin", err)}
                if returncode == 0 and len(fields) == 5 and fields[0] and fields[1]:
                    record["server"] = dict(zip(["ServerVersion", "OSType", "OperatingSystem", "KernelVersion", "Architecture"], fields))
                    report["status"] = "LINUX_DAEMON_AVAILABLE" if fields[1] == "linux" else "DAEMON_AVAILABLE_NON_LINUX"
                    report["server"] = record["server"]
                report["checks"].append(record)
                print(json.dumps({"check": index, "elapsed_seconds": record["elapsed_seconds"],
                    "exit_code": returncode, "status": report["status"]}, ensure_ascii=False), flush=True)
                if "server" in report:
                    break
            report["probe_elapsed_seconds"] = round(time.monotonic() - began, 3)
            if "server" not in report:
                report["status"] = "DAEMON_NOT_AVAILABLE_WITHIN_BOUND_NO_UI_ACTION_TAKEN"
                report["interaction_need"] = "Unknown; no license or setup dialog was accepted or manipulated"
        elif launch is not None:
            report["status"] = "START_PROCESS_FAILED_NO_SECOND_LAUNCH"
    report["finished_utc"] = utc()
    report["scope"] = "Existing application launch and read-only limited docker info fields only; Linux packages, shell, model runtime and LibreOffice formula caches remain untested"
    with REPORT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "server": report.get("server"),
        "report": str(REPORT.relative_to(ROOT)).replace("\\", "/"), "launch_calls": report["launch_calls"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
