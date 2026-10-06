"""Independent Calc-engine diagnostic; does not invoke macro or recalc.py.

Converts two existing constructed controls into a fresh output directory with
an explicit fresh LibreOffice profile. Original controls and failed runs remain
unchanged. No model/API, credentials, author edits, or expected-value injection.
"""
from __future__ import annotations

import json
import subprocess
import time
from decimal import Decimal
from pathlib import Path

import openpyxl

import libreoffice_preflight as probe


ROOT, OUT, PREFLIGHT = probe.ROOT, probe.OUT, probe.PREFLIGHT
DIAGNOSTIC = PREFLIGHT / "libreoffice_engine_diagnostic"
PROFILE = DIAGNOSTIC / "engine_profile"
WINDOWS_PROFILE = DIAGNOSTIC / "windows_profile"
CONVERTED = DIAGNOSTIC / "converted"
REPORT = OUT / "libreoffice_engine_diagnostic.json"


def cells(path):
    cache = openpyxl.load_workbook(path, data_only=True)
    actual, actual_type = cache.active["A1"].value, cache.active["A1"].data_type
    cache.close()
    formulas = openpyxl.load_workbook(path, data_only=False)
    formula = formulas.active["A1"].value
    formulas.close()
    return formula, actual, actual_type


def main():
    for path in (DIAGNOSTIC, REPORT):
        assert path.resolve().is_relative_to(ROOT.resolve())
        if path.exists():
            raise SystemExit("Refusing to overwrite an earlier engine diagnostic")
    failed_path = OUT / "libreoffice_readiness_cli_shim.json"
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    assert failed["status"] == "NOT_READY_ONE_CLI_MECHANISM_FIX_FAILED_RETAINED"
    controls = failed["controls"]
    assert [item["control"] for item in controls] == ["positive", "division_by_zero"]
    inputs = [ROOT / item["file"] for item in controls]
    source_hashes = [probe.digest(path) for path in inputs]
    assert source_hashes == [item["file_sha256_after"] for item in controls]
    assert [cells(path) for path in inputs] == [("=200000/12", None, "n"), ("=1/0", None, "n")]
    for path in (CONVERTED, PROFILE, WINDOWS_PROFILE / ".config", WINDOWS_PROFILE / ".local", WINDOWS_PROFILE / "temporary"):
        path.mkdir(parents=True, exist_ok=True)
    program = probe.RUNTIME / "program"
    official = program / "soffice.com"
    assert probe.digest(official) == failed["compatibility_launcher"]["official_console_binary_sha256"]
    site = str(Path(openpyxl.__file__).resolve().parent.parent)
    environment = {"SystemRoot": "C:\\WINDOWS", "WINDIR": "C:\\WINDOWS",
        "COMSPEC": "C:\\WINDOWS\\system32\\cmd.exe",
        "PATH": str(program) + ";C:\\Python314;C:\\WINDOWS\\system32;C:\\WINDOWS",
        "USERPROFILE": str(WINDOWS_PROFILE), "APPDATA": str(WINDOWS_PROFILE / ".config"),
        "LOCALAPPDATA": str(WINDOWS_PROFILE / ".local"),
        "TEMP": str(WINDOWS_PROFILE / "temporary"), "TMP": str(WINDOWS_PROFILE / "temporary"),
        "PYTHONPATH": site, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    command = [str(official), "-env:UserInstallation=" + PROFILE.as_uri(),
               "--headless", "--norestore", "--convert-to", "xlsx", "--outdir", str(CONVERTED),
               *(str(path) for path in inputs)]
    started = time.monotonic()
    print("Independent Calc-engine conversion, fresh explicit profile, two constructed controls", flush=True)
    process = subprocess.Popen(command, cwd=str(DIAGNOSTIC), env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out, stop = False, None
    try:
        stdout, stderr = process.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop = subprocess.run(["C:\\WINDOWS\\system32\\taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                              capture_output=True, timeout=20)
        stdout, stderr = process.communicate(timeout=10)
    for name, data in (("stdout", stdout), ("stderr", stderr)):
        with (DIAGNOSTIC / (name + ".bin")).open("xb") as stream:
            stream.write(data)
        with (DIAGNOSTIC / (name + ".txt")).open("x", encoding="utf-8") as stream:
            stream.write(data.decode("utf-8", errors="replace"))
    results = []
    for item, source, original_hash in zip(controls, inputs, source_hashes):
        output = CONVERTED / source.name
        actual_formula, actual, actual_type = cells(output) if output.exists() else (None, None, None)
        if item["control"] == "positive":
            predicate = isinstance(actual, (int, float)) and abs(Decimal(str(actual)) - Decimal("200000") / 12) < Decimal("0.000001")
        else:
            predicate = actual == "#DIV/0!" and actual_type == "e"
        unchanged = probe.digest(source) == original_hash
        passed = process.returncode == 0 and not timed_out and output.exists() and predicate and unchanged and actual_formula == item["formula"]
        results.append({"control": item["control"], "constructed_not_enterprise_episode": True,
            "input": probe.rel(source), "input_sha256_before": original_hash,
            "input_sha256_after": probe.digest(source), "original_input_unchanged": unchanged,
            "output": probe.rel(output), "output_created": output.exists(),
            "output_sha256": probe.digest(output) if output.exists() else None,
            "formula": item["formula"], "formula_after": actual_formula,
            "actual_cached_value": actual, "actual_cached_type": actual_type,
            "expected": item["expected"], "cache_predicate_pass": predicate,
            "status": "PASS" if passed else "FAIL"})
    passed = all(item["status"] == "PASS" for item in results)
    report = {"schema": "independent-libreoffice-calc-engine-diagnostic-v1",
        "status": "CALC_ENGINE_CONVERSION_REAL_CACHE_PASS_MACRO_ROUTE_STILL_UNVALIDATED" if passed else "CALC_ENGINE_DIAGNOSTIC_FAILED_ENVIRONMENT_NOT_READY",
        "model_calls": 0, "credentials_read": False, "macro_invoked": False, "author_recalc_invoked": False,
        "author_source_modified": False, "expected_values_injected": False,
        "original_recalc_sha256": probe.digest(probe.RECALC),
        "previous_failed_report": probe.rel(failed_path), "previous_failed_report_sha256": probe.digest(failed_path),
        "official_soffice_com": probe.rel(official), "official_soffice_com_sha256": probe.digest(official),
        "command_argv": command, "fresh_explicit_profile": probe.rel(PROFILE),
        "previous_profile_reused": False, "HOME_modified": False,
        "exit_code": process.returncode, "outer_timeout": timed_out,
        "outer_timeout_seconds": 90, "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_raw": probe.rel(DIAGNOSTIC / "stdout.bin"), "stderr_raw": probe.rel(DIAGNOSTIC / "stderr.bin"),
        "stdout_utf8_display": probe.rel(DIAGNOSTIC / "stdout.txt"), "stderr_utf8_display": probe.rel(DIAGNOSTIC / "stderr.txt"),
        "stdout_text": stdout.decode("utf-8", errors="replace"), "stderr_text": stderr.decode("utf-8", errors="replace"),
        "owned_process_timeout_stop": None if stop is None else {"exit_code": stop.returncode,
            "stdout": stop.stdout.decode("utf-8", errors="replace"), "stderr": stop.stderr.decode("utf-8", errors="replace")},
        "controls": results,
        "interpretation": "This independent diagnostic tests Calc loading/calculation/saving via conversion, not the earlier macro entry. Engine PASS does not validate original macro invocation, agentic repairs, all formulas or parallel profiles.",
        "runtime_environment_published": False,
        "serial_only": True, "max_workers_tested": 1,
        "reference": "https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html"}
    assert report["original_recalc_sha256"] == failed["source_recalc_sha256"]
    probe.write(REPORT, report)
    print(json.dumps({"status": report["status"], "cached_values": [item["actual_cached_value"] for item in results],
                      "original_inputs_unchanged": all(item["original_input_unchanged"] for item in results),
                      "report": probe.rel(REPORT)}, ensure_ascii=False), flush=True)
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
