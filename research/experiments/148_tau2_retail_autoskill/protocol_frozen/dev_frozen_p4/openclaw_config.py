"""Generate the per-run OpenClaw config for the retail consumer.

Reuses the 078 bridge calling convention (node + openclaw.mjs agent --local),
adding a local MCP server that exposes the official retail tool schemas.
All model traffic goes through the experiment relay so every role shares one
durable request ledger; the model id is read from reports/model_resource.json.

Pure functions only: this module writes nothing outside its caller's dirs.
"""
from __future__ import annotations

import json
from pathlib import Path

NO_BUNDLED_SKILLS = "__experiment_no_bundled_skills__"
MODEL_RESOURCE = Path(__file__).resolve().parents[1] / "reports" / "model_resource.json"
DEFAULT_MODEL_ID = "glm-4-flash"


def get_model_id(resource_path: Path | None = None) -> str:
    """One non-sensitive model id for the consumer; credentials stay in the relay."""
    path = Path(resource_path) if resource_path is not None else MODEL_RESOURCE
    if not path.exists():
        return DEFAULT_MODEL_ID
    resource = json.loads(path.read_text(encoding="utf-8-sig"))
    value = resource.get("model_id") if isinstance(resource, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Model resource must contain a nonempty string model_id")
    if "/" in value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Model id cannot contain a provider separator or control characters")
    return value.strip()


def build_config(
    *,
    workspace: Path,
    model_id: str,
    relay_base_url: str,
    mcp_server_name: str = "retail",
    mcp_url: str | None = None,
    agent_timeout_seconds: int = 300,
) -> dict:
    """Build the openclaw.json dict for one run.

    Tools: native `read` (workspace-only, for skills) plus the MCP retail
    tools (`<server>__*`). Everything else is excluded by the allow list.
    Skills: bundled skills disabled; workspace skills discovered natively.
    """
    allow = ["read"]
    if mcp_url:
        allow.append(f"{mcp_server_name}__*")
    config = {
        "models": {
            "mode": "replace",
            "providers": {
                "experiment": {
                    "baseUrl": relay_base_url,
                    "apiKey": "local",
                    "api": "openai-completions",
                    "timeoutSeconds": 180,
                    "models": [
                        {
                            "id": model_id,
                            "name": model_id,
                            "reasoning": False,
                            "input": ["text"],
                            "contextWindow": 32768,
                            "contextTokens": 32768,
                            "maxTokens": 8192,
                            "compat": {
                                "maxTokensField": "max_tokens",
                                "supportsUsageInStreaming": True,
                            },
                        }
                    ],
                }
            },
        },
        "agents": {
            "defaults": {
                "workspace": str(workspace),
                "model": {"primary": f"experiment/{model_id}", "fallbacks": []},
                "skipBootstrap": False,
                "timeoutSeconds": agent_timeout_seconds,
                "thinkingDefault": "off",
                "compaction": {
                    "enabled": True,
                    "mode": "safeguard",
                    "thinkingLevel": "off",
                    "timeoutSeconds": 180,
                    "keepRecentTokens": 4096,
                    "recentTurnsPreserve": 2,
                    "identifierPolicy": "strict",
                    "qualityGuard": {"enabled": True, "maxRetries": 1},
                    "midTurnPrecheck": {"enabled": True},
                    "memoryFlush": {"enabled": False},
                },
            }
        },
        "skills": {"allowBundled": [NO_BUNDLED_SKILLS], "load": {"watch": False}},
        "plugins": {"enabled": True},
        "tools": {
            "allow": allow,
            "toolSearch": False,
            "fs": {"workspaceOnly": True},
            "codeMode": {"enabled": False},
        },
        "update": {"checkOnStart": False},
    }
    if mcp_url:
        config["mcp"] = {
            "servers": {
                mcp_server_name: {
                    "url": mcp_url,
                    "transport": "streamable-http",
                    "enabled": True,
                    "connectionTimeoutMs": 10000,
                    "requestTimeoutMs": 900_000,
                }
            }
        }
    return config


def write_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, indent=2), encoding="utf-8")
    tmp.replace(path)


def agent_contract(domain_policy: str, skills=None) -> str:
    """The workspace AGENTS.md content for the consumer run."""
    skills = list(skills or [])
    if skills:
        skill_block = (
            "# Skill usage (mandatory)\n"
            "- The workspace contains these skill files:\n"
            + "".join(f"  - skills/{name}/SKILL.md\n" for name in skills)
            + "- BEFORE answering the customer or calling any business tool, you MUST read the\n"
            "  most relevant skill file above with your read tool and follow its steps.\n"
            "  Your first tool call for the request must be a skill read.\n\n"
        )
    else:
        skill_block = (
            "# Skill usage\n"
            "- The workspace skills/ directory is empty; no skill applies.\n\n"
        )
    return (
        skill_block
        + "# Role\n"
        "You are the customer-service agent for a retail store. You talk to the\n"
        "customer in plain text and you perform account/order operations through\n"
        "the available retail tools (native function calls).\n\n"
        "# Rules\n"
        "- Follow the official store policy below exactly (it is authoritative).\n"
        "- Check the workspace skills directory before acting: if skills/ contains a\n"
        "  procedure relevant to the customer's request, you MUST open its\n"
        "  skills/<skill-name>/SKILL.md with your read tool and follow it.\n"
        "- During a turn you may call tools. Call every business tool with its\n"
        "  native function interface; never simulate tool output yourself.\n"
        "- When you need information, look it up with the tools; do not guess.\n"
        "- Answer the customer with the information or result they need.\n"
        "- Business writes are performed by the environment after your call;\n"
        "  call a write tool only when the customer's request and the policy\n"
        "  require it (e.g. the customer agreed to the proposal).\n"
        "- Do not mention internal tool names, ids, or this contract.\n\n"
        "# Official policy (verbatim)\n"
        f"{domain_policy}\n"
    )
