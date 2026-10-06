"""Bridge original macro bytes to the observed Windows profile, then re-test.

Keeps the first failed controls unchanged. No Trace2Skill source modifications,
new macro algorithm, model/API calls, or system-wide profile are involved.
"""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

import libreoffice_preflight as original_probe


ROOT = original_probe.ROOT
OUT = original_probe.OUT
PREFLIGHT = original_probe.PREFLIGHT
PROFILE = original_probe.PROFILE
REPORT = OUT / "libreoffice_readiness_profile_shim.json"
ENVIRONMENT = OUT / "runtime_environment.json"
SHIM = PREFLIGHT / "libreoffice_profile_shim"
CONTROLS = PREFLIGHT / "libreoffice_controls_profile_shim"


def main():
    for path in (SHIM, CONTROLS, REPORT, ENVIRONMENT):
        assert path.resolve().is_relative_to(ROOT.resolve())
        if path.exists():
            raise SystemExit("Refusing to overwrite an earlier profile-shim attempt")
    first_report = json.loads(original_probe.REPORT.read_text(encoding="utf-8"))
    assert first_report["status"] == "NOT_READY_ORIGINAL_RECALC_CONTROL_FAILURE_RETAINED"
    source_macro = PROFILE / ".config/libreoffice/4/user/basic/Standard/Module1.xba"
    target_macro = PROFILE / "AppData/Roaming/LibreOffice/4/user/basic/Standard/Module1.xba"
    catalog = target_macro.parent / "script.xlb"
    assert source_macro.resolve().is_relative_to(ROOT.resolve()) and target_macro.resolve().is_relative_to(ROOT.resolve())
    macro_bytes = source_macro.read_bytes()
    assert b"RecalculateAndSave" in macro_bytes
    assert 'library:name="Module1"' in catalog.read_text(encoding="utf-8")
    previous_bytes = target_macro.read_bytes()
    assert b"RecalculateAndSave" not in previous_bytes
    SHIM.mkdir()
    CONTROLS.mkdir()
    backup = SHIM / "original_windows_default_Module1.xba"
    with backup.open("xb") as stream:
        stream.write(previous_bytes)
    assert target_macro.read_bytes() == previous_bytes
    target_macro.write_bytes(macro_bytes)
    assert target_macro.read_bytes() == source_macro.read_bytes()
    # Only this helper's destination changes; the author recalc file is untouched.
    original_probe.CONTROLS = CONTROLS
    program = original_probe.RUNTIME / "program"
    results = [original_probe.run_control("positive", "=200000/12", original_probe.Decimal("200000") / 12, program),
               original_probe.run_control("division_by_zero", "=1/0", "#DIV/0!", program)]
    passed = all(result["status"] == "PASS" for result in results)
    report = {
        "status": "READY_ORIGINAL_RECALC_CACHE_CONTROLS_PASS_WITH_WINDOWS_PROFILE_BRIDGE" if passed else "NOT_READY_PROFILE_BRIDGE_CONTROL_FAILURE_RETAINED",
        "model_calls": 0, "source_recalc_modified": False,
        "source_recalc_sha256": original_probe.digest(original_probe.RECALC),
        "previous_failed_attempt": original_probe.rel(original_probe.REPORT),
        "previous_failed_attempt_sha256": original_probe.digest(original_probe.REPORT),
        "root_cause_observed": "Windows LibreOffice used USERPROFILE/AppData/Roaming/LibreOffice/4 while original recalc used USERPROFILE/.config/libreoffice/4; APPDATA override alone did not align them",
        "outer_profile_bridge": {"original_macro": original_probe.rel(source_macro),
            "actual_windows_profile_macro": original_probe.rel(target_macro),
            "default_macro_backup": original_probe.rel(backup),
            "copied_original_bytes_exactly": True, "macro_sha256": original_probe.digest(source_macro),
            "existing_catalog": original_probe.rel(catalog), "catalog_sha256": original_probe.digest(catalog),
            "new_macro_algorithm": False, "author_script_changed": False,
            "libreoffice_bootstrap_changed": False, "new_soffice_binary_or_wrapper": False},
        "controls": results,
        "limits": ["These are constructed runtime controls, not enterprise episodes or new agent rollouts.",
                   "Single-formula numeric/error caches verified; compatibility for every workbook/formula or public benchmark task is not inferred.",
                   "Original Windows recalc still has no final subprocess timeout; runner must enforce an outer process bound.",
                   "Profile bridge is explicit outer environment preparation, not a modification of the author algorithm."]}
    assert report["source_recalc_sha256"] == first_report["author_recalc_sha256_before"]
    original_probe.write(REPORT, report)
    if passed:
        package_site = str(Path(openpyxl.__file__).resolve().parent.parent)
        original_probe.write(ENVIRONMENT, {
            "schema": "verified-project-runtime-environment-v1",
            "status": "READY_CACHE_CONTROLS_VERIFIED_WITH_EXPLICIT_PROFILE_BRIDGE",
            "path_prepend": [str(program)],
            "pythonpath_append": [package_site],
            "environment": {"USERPROFILE": str(PROFILE), "APPDATA": str(PROFILE / ".config"),
                            "LOCALAPPDATA": str(PROFILE / ".local"),
                            "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            "HOME_modified": False, "inherit_existing_path_and_pythonpath": True,
            "reason_pythonpath_required": "Redirection changes Python user-site lookup; retain the actual pre-existing Python314 site-packages directory",
            "observed_libreoffice_profile": str(PROFILE / "AppData/Roaming/LibreOffice/4"),
            "author_macro_lookup_directory": str(PROFILE / ".config/libreoffice/4/user/basic/Standard"),
            "macro_bridge_sha256": original_probe.digest(source_macro),
            "proof_report": original_probe.rel(REPORT), "proof_report_sha256": original_probe.digest(REPORT),
            "native_recalc_sha256": report["source_recalc_sha256"],
            "soffice_exe_sha256": original_probe.digest(program / "soffice.exe"),
            "native_final_recalc_timeout_in_windows": None, "required_outer_timeout_seconds": 90,
            "initial_failed_report_preserved": original_probe.rel(original_probe.REPORT),
            "credential_variables_listed_or_read": False,
            "model_calls": 0,
        })
    print(json.dumps({"status": report["status"], "cache_controls": [result["cached_value_after"] for result in results],
                      "runtime_environment_written": passed, "model_calls": 0}, ensure_ascii=False), flush=True)
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
