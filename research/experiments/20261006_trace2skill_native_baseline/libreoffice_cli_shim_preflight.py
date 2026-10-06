"""One explicit Windows CLI compatibility fix; original author code stays intact.

Builds a project-only soffice.exe launcher, delegates to the official soffice.com,
maps only the author's exact application macro URI, and tests real XLSX caches.
Previous failed attempts are immutable. No model, credentials, or static values.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import openpyxl

import libreoffice_preflight as probe


ROOT, OUT, PREFLIGHT, PROFILE = probe.ROOT, probe.OUT, probe.PREFLIGHT, probe.PROFILE
SHIM = PREFLIGHT / "libreoffice_cli_shim"
CONTROLS = PREFLIGHT / "libreoffice_controls_cli_shim"
REPORT = OUT / "libreoffice_readiness_cli_shim.json"
ENVIRONMENT = OUT / "runtime_environment.json"
COMPILER = Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
SOURCE = r'''using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;

class LibreOfficeCliCompatibility {
    const string OriginalUri = "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application";
    const string CompatibilityUri = "macro:///Standard.Module1.RecalculateAndSave";
    // Windows CreateProcess quoting, including arguments containing spaces or quotes.
    static string Quote(string value) {
        var result = new StringBuilder("\"");
        int backslashes = 0;
        foreach (char c in value) {
            if (c == '\\') { backslashes++; continue; }
            if (c == '"') {
                result.Append('\\', backslashes * 2 + 1); result.Append(c); backslashes = 0;
            } else {
                result.Append('\\', backslashes); result.Append(c); backslashes = 0;
            }
        }
        result.Append('\\', backslashes * 2); result.Append('"');
        return result.ToString();
    }
    static int Main(string[] args) {
        string official = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
            "..", "libreoffice_runtime", "program", "soffice.com"));
        if (!File.Exists(official)) { Console.Error.WriteLine("Project official soffice.com missing"); return 126; }
        var outgoing = new List<string>();
        bool macro = false;
        foreach (string arg in args) {
            if (arg == OriginalUri) { macro = true; continue; }
            outgoing.Add(arg);
        }
        // Document loading is listed before invoking the same global application macro.
        if (macro) outgoing.Add(CompatibilityUri);
        var quoted = new List<string>();
        foreach (string arg in outgoing) quoted.Add(Quote(arg));
        var start = new ProcessStartInfo(official, string.Join(" ", quoted.ToArray()));
        start.UseShellExecute = false;
        start.CreateNoWindow = true;
        using (Process child = Process.Start(start)) {
            if (!child.WaitForExit(80000)) {
                var stop = new ProcessStartInfo("C:\\WINDOWS\\system32\\taskkill.exe",
                    "/PID " + child.Id + " /T /F");
                stop.UseShellExecute = false; stop.CreateNoWindow = true;
                using (Process ownedStop = Process.Start(stop)) ownedStop.WaitForExit(10000);
                Console.Error.WriteLine("Project soffice.com child exceeded 80-second compatibility bound");
                return 124;
            }
            return child.ExitCode;
        }
    }
}
'''


def main():
    for path in (SHIM, CONTROLS, REPORT, ENVIRONMENT):
        assert path.resolve().is_relative_to(ROOT.resolve())
        if path.exists():
            raise SystemExit("Refusing to overwrite previous CLI-shim attempt")
    first = json.loads(probe.REPORT.read_text(encoding="utf-8"))
    profile_report = OUT / "libreoffice_readiness_profile_shim.json"
    assert json.loads(profile_report.read_text(encoding="utf-8"))["status"] == "NOT_READY_PROFILE_BRIDGE_CONTROL_FAILURE_RETAINED"
    program = probe.RUNTIME / "program"
    source_macro = PROFILE / ".config/libreoffice/4/user/basic/Standard/Module1.xba"
    actual_macro = PROFILE / "AppData/Roaming/LibreOffice/4/user/basic/Standard/Module1.xba"
    assert actual_macro.read_bytes() == source_macro.read_bytes()
    assert probe.digest(probe.RECALC) == first["author_recalc_sha256_before"]
    assert COMPILER.is_file() and (program / "soffice.com").is_file()
    SHIM.mkdir()
    CONTROLS.mkdir()
    source = SHIM / "soffice_cli_compatibility.cs"
    with source.open("x", encoding="utf-8") as stream:
        stream.write(SOURCE)
    executable = SHIM / "soffice.exe"
    compiled = subprocess.run([str(COMPILER), "/nologo", "/target:exe", "/out:" + str(executable), str(source)],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert compiled.returncode == 0, compiled.stderr or compiled.stdout
    # Only the launcher PATH destination changes; original recalc and macro stay intact.
    probe.CONTROLS = CONTROLS
    results = [probe.run_control("positive", "=200000/12", probe.Decimal("200000") / 12, SHIM),
               probe.run_control("division_by_zero", "=1/0", "#DIV/0!", SHIM)]
    passed = all(result["status"] == "PASS" for result in results)
    report = {
        "schema": "libreoffice-one-cli-compatibility-control-v1",
        "status": "READY_ORIGINAL_RECALC_REAL_CACHES_WITH_EXPLICIT_WINDOWS_CLI_SHIM" if passed else "NOT_READY_ONE_CLI_MECHANISM_FIX_FAILED_RETAINED",
        "model_calls": 0, "credentials_read": False, "author_source_modified": False,
        "source_recalc_sha256": probe.digest(probe.RECALC),
        "original_macro_bytes_sha256": probe.digest(source_macro),
        "same_macro_in_actual_windows_profile": source_macro.read_bytes() == actual_macro.read_bytes(),
        "previous_failed_reports": [{"path": probe.rel(path), "sha256": probe.digest(path)}
                                    for path in (probe.REPORT, profile_report)],
        "compatibility_launcher": {"source": probe.rel(source), "source_sha256": probe.digest(source),
            "binary": probe.rel(executable), "binary_sha256": probe.digest(executable),
            "compiler": str(COMPILER), "compiler_exit_code": compiled.returncode,
            "delegates_to": probe.rel(program / "soffice.com"),
            "official_console_binary_sha256": probe.digest(program / "soffice.com"),
            "exact_original_uri": "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
            "mapped_uri": "macro:///Standard.Module1.RecalculateAndSave",
            "document_before_macro": True, "console_child_waits_synchronously": True,
            "child_bound_seconds": 80, "all_other_arguments_delegated": True,
            "macro_algorithm_changed": False, "static_expected_cache_injected": False},
        "controls": results,
        "references": {"official_windows_console_and_parameters": "https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html",
            "public_dispatch_source": "https://raw.githubusercontent.com/LibreOffice/core/master/desktop/source/app/dispatchwatcher.cxx"},
        "interpretation": "Two previous null-cache failures were observed; public source supports both URI families. This combined console/URI/order control cannot isolate which changed factor causes any observed improvement.",
        "limits": ["Single-formula constructed runtime controls, not enterprise episodes or benchmark outcomes.",
                   "Shared profile is validated only for serial execution, maximum workers=1; no 128-worker equivalence is claimed.",
                   "This is explicit Windows environment/CLI adaptation, not an unchanged Linux runtime.",
                   "No claim that all workbooks, formulas, public tasks or agentic repaired outputs are valid."]}
    assert report["source_recalc_sha256"] == first["author_recalc_sha256_before"]
    probe.write(REPORT, report)
    if passed:
        site = str(Path(openpyxl.__file__).resolve().parent.parent)
        probe.write(ENVIRONMENT, {
            "schema": "verified-project-runtime-environment-v1", "validated": True,
            "status": "READY_REAL_CACHE_CONTROLS_WITH_EXPLICIT_WINDOWS_CLI_SHIM",
            "path_prepend": [str(SHIM), str(program)], "pythonpath_append": [site],
            "environment": {"USERPROFILE": str(PROFILE), "APPDATA": str(PROFILE / ".config"),
                "LOCALAPPDATA": str(PROFILE / ".local"), "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            "HOME_modified": False, "inherit_existing_path_and_pythonpath": True,
            "reason_pythonpath_required": "USERPROFILE redirection changes Python user-site lookup; retain genuine existing Python314 packages",
            "observed_libreoffice_profile": str(PROFILE / "AppData/Roaming/LibreOffice/4"),
            "author_macro_lookup_directory": str(source_macro.parent),
            "macro_bridge_sha256": probe.digest(source_macro),
            "proof_report": probe.rel(REPORT), "proof_report_sha256": probe.digest(REPORT),
            "native_recalc_sha256": report["source_recalc_sha256"],
            "launcher_source_sha256": probe.digest(source), "launcher_exe_sha256": probe.digest(executable),
            "official_soffice_com_sha256": probe.digest(program / "soffice.com"),
            "official_soffice_exe_sha256": probe.digest(program / "soffice.exe"),
            "max_workers": 1, "shared_profile_concurrency_verified": False,
            "native_final_recalc_timeout_in_windows": None,
            "launcher_child_timeout_seconds": 80, "required_outer_timeout_seconds": 90,
            "source_controls": [{"control": item["control"], "status": item["status"],
                "actual_cached_value": item["cached_value_after"], "file": item["file"]} for item in results],
            "credential_variables_listed_or_read": False, "model_calls": 0})
    print(json.dumps({"status": report["status"], "cache_controls": [item["cached_value_after"] for item in results],
                      "runtime_environment_written": passed, "model_calls": 0}, ensure_ascii=False), flush=True)
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
