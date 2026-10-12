"""Local OpenClaw adapter namespace extending an unchanged upstream snapshot."""
from pathlib import Path

_UPSTREAM = Path(__file__).resolve().parents[1] / 'third_party' / 'sibyl_framework' / 'sibyl'
if not _UPSTREAM.is_dir():
    raise ImportError(f'Pinned Sibyl runtime is missing: {_UPSTREAM}')
__path__.append(str(_UPSTREAM))
