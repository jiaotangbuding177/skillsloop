"""Serve the latest explicitly scoped snapshot via CodeGraphMCP stdio."""
from pathlib import Path
import json
import subprocess
import sys

base = Path(__file__).resolve().parent
latest = json.loads((base / 'latest.json').read_text(encoding='utf-8'))
exe = Path.home() / '.local/share/codegraph-mcp/v1.1.0/runtime/src/CodeGraphMcp/bin/Release/net10.0/CodeGraphMcp.exe'
sys.exit(subprocess.call([str(exe), latest['scope'], latest['database']], cwd=latest['scope']))
