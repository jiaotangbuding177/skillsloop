"""Run-local cache routing around the unchanged native error-analysis client.

Only an omitted ``cache_path`` is supplemented. Explicit constructor arguments,
including ``cache_path=None`` or ``use_cache=False``, retain their native meaning.
The patched module binding is process-wide: concurrent experiments should use
separate processes; workers of one run may share this context's cache directory.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
import inspect
from pathlib import Path
from unittest.mock import patch


@contextmanager
def isolate_error_analysis_cache(run_dir: str | Path):
    """Supplement an omitted cache path with ``<run>/error-analysis-cache``.

Import/bootstrap the author checkout before entering. The original native class
constructs every client and controls cache enablement, configuration and retries.
Explicit cache paths are never rewritten. Nested contexts restore their previous
binding on exit, including when the enclosed analysis raises an exception.
"""
    import analysis.error_analysis_agent as native

    original = native.OpenAIClient
    signature = inspect.signature(original)
    cache_root = Path(run_dir).resolve() / "error-analysis-cache"

    @wraps(original, updated=())
    def construct(*args, **kwargs):
        bound = signature.bind_partial(*args, **kwargs)
        if "cache_path" not in bound.arguments:
            kwargs = dict(kwargs)
            kwargs["cache_path"] = str(cache_root)
        return original(*args, **kwargs)

    with patch.object(native, "OpenAIClient", construct):
        yield cache_root
