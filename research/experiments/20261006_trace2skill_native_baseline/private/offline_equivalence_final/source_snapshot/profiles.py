"""Frozen native configuration profiles. No client, credentials or network access."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BASELINE = PROJECT / "research/baselines/Trace2Skill"
BASELINE_COMMIT = "3d0b52a140f002a512930252b613c49048f7d5ac"


def load_profile(name: str = "release_readme") -> dict:
    document = json.loads((HERE / "profiles.json").read_text(encoding="utf-8"))
    if document["official_commit"] != BASELINE_COMMIT:
        raise ValueError("Profile/source commit mismatch")
    if name not in document["profiles"]:
        raise ValueError(f"Unknown profile: {name}")
    profile = deepcopy(document["common"])
    profile["evolver"]["merge_batch_size"] = document["profiles"][name]["merge_batch_size"]
    profile.update(name=name, official_commit=BASELINE_COMMIT,
                   basis=document["profiles"][name]["basis"], paper_version=document["paper_version"])
    return profile


def generation_config_for(profile: dict, phase: str, seed: int | None = None) -> dict:
    """Load the released JSON unchanged; send seed only where README sends it."""
    mode = "instruct" if phase in {"react", "rollout", "error_analysis"} else "thinking"
    config = json.loads((BASELINE / profile["generation_files"][mode]).read_text(encoding="utf-8"))
    if phase not in {"error_analysis", "success_analysis"}:
        config["seed"] = profile["seed_policy"]["default_seed"] if seed is None else seed
    elif seed is not None:
        config["seed"] = seed  # Explicit protocol deviation, never silently supplied.
    return config


def effective_request_config(profile: dict, phase: str, settings=None, seed: int | None = None) -> dict:
    """Document the author's merge order; offline capture also executes native chat()."""
    config = generation_config_for(profile, phase, seed)
    if settings is not None:
        config.update(settings.to_dict() if hasattr(settings, "to_dict") else dict(settings))
    return config


def native_evolver_kwargs(profile: dict) -> dict:
    return deepcopy(profile["evolver"])
