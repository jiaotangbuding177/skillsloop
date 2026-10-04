"""tau2 HalfDuplex agent adapter that drives native OpenClaw as the consumer.

Design (see protocol.md section 4):
- tau2 keeps ownership of tool execution. Every retail tool call emitted by
  OpenClaw is captured by the in-process MCP bridge (suspend-and-relay) and
  returned to tau2 as an ``AssistantMessage.tool_calls``; tau2 executes it
  exactly once on the official environment and hands the result back; the
  adapter delivers the result to the waiting MCP handler so OpenClaw
  continues in the same session/process.
- One OpenClaw invocation starts on each user message and ends when OpenClaw
  emits the assistant's final text for this turn (no tool calls pending).
- Skills: the run workspace contains a native ``skills/`` directory (empty
  for B0, the frozen library for B1); OpenClaw discovers and reads skills
  with its own read tool. The adapter never injects skill bodies.

The agent instance is created per simulation by the tau2 runner; runtime
objects (relay, MCP server, subprocess) live on the instance only.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from tau2.agent.base_agent import HalfDuplexAgent, ValidAgentInputMessage
from tau2.data_model.message import (
    AssistantMessage,
    Message,
    MultiToolMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)

from mcp_retail_bridge import McpBridgeServer, PendingCall, RetailRelay
from openclaw_config import agent_contract, build_config, get_model_id, write_config

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]

# Reuse the verified OpenClaw 2026.9.7 runtime from experiment 078, using its
# Linux-FS copies: loading node_modules from /mnt/d (9p) or writing a child's
# stdout there blocks the child in p9_client_rpc (observed 2026-10-02).
# Overridable for dev.
DEFAULT_NODE = Path("/var/tmp/skillsloop078/node-v26.1.0-linux-x64/bin/node")
DEFAULT_CLI = Path(
    "/var/tmp/skillsloop078/runtime_openclaw_fast/node_modules/openclaw/openclaw.mjs"
)


class InvocationHandle:
    """One OpenClaw invocation (one agent turn), real or simulated."""

    def poll(self) -> Optional[int]:
        raise NotImplementedError

    def terminate(self) -> None:
        raise NotImplementedError

    def final_text(self) -> str:
        raise NotImplementedError


class SubprocessInvocation(InvocationHandle):
    """One OpenClaw CLI invocation whose logs stay on the Linux FS.

    A child process whose stdout/stderr point at /mnt/d (9p) can block in
    p9_client_rpc for minutes (observed 2026-10-02). Prompt and logs are
    written natively and synced into the session dir after the process exits.
    """

    def __init__(
        self,
        proc: subprocess.Popen,
        native_stdout: Path,
        native_stderr: Path,
        session_stdout: Path,
        session_stderr: Path,
    ):
        self.proc = proc
        self.native_stdout = native_stdout
        self.native_stderr = native_stderr
        self.session_stdout = session_stdout
        self.session_stderr = session_stderr

    def poll(self) -> Optional[int]:
        return self.proc.poll()

    def terminate(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def sync(self) -> None:
        """Copy native logs into the session dir; safe once the process ended."""
        for source, target in (
            (self.native_stdout, self.session_stdout),
            (self.native_stderr, self.session_stderr),
        ):
            try:
                if source.exists():
                    shutil.copyfile(source, target)
            except OSError:
                pass

    def final_text(self) -> str:
        raw = self.native_stdout.read_text(encoding="utf-8", errors="replace")
        stderr = self.native_stderr.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"OpenClaw output was not JSON ({error}); stderr tail: {stderr[-500:]}"
            )
        if data.get("error") or (data.get("meta") or {}).get("aborted"):
            raise RuntimeError(f"OpenClaw reported a failed invocation: {json.dumps(data)[:800]}")
        return extract_payload_text(data)


def extract_payload_text(data) -> str:
    """Same extraction as the 078 bridge: payloads[].text, recursively."""
    if isinstance(data, dict):
        if "payloads" in data:
            return "\n".join(p.get("text", "") for p in data["payloads"]).strip()
        if isinstance(data.get("result"), dict):
            return extract_payload_text(data["result"])
    raise ValueError("No OpenClaw payloads in response")


@dataclass
class OpenClawRetailState:
    session_id: str
    session_dir: Path
    turn_index: int = 0
    first_context: str = ""


@dataclass
class SessionRuntime:
    """Per-simulation runtime objects (not part of the tau2 agent state)."""

    session_id: str
    session_dir: Path
    workspace: Path
    native_workspace: Path
    state_dir: Path
    relay: RetailRelay
    bridge: McpBridgeServer
    config_path: Path
    skills_dir: Optional[Path] = None
    proc: Optional[InvocationHandle] = None
    pending: list[PendingCall] = field(default_factory=list)
    invocation_index: int = 0


def serialize_history(message_history: Optional[list[Message]]) -> str:
    """Plain-text view of prior user/assistant text (tool activity excluded)."""
    lines: list[str] = []
    for message in message_history or []:
        if isinstance(message, UserMessage) and message.content:
            lines.append(f"customer: {message.content}")
        elif isinstance(message, AssistantMessage) and message.content:
            lines.append(f"you: {message.content}")
    return "\n".join(lines).strip()


class OpenClawRetailAgent(HalfDuplexAgent):
    """Native OpenClaw consumer for the retail domain, tau2-stepped."""

    def __init__(
        self,
        tools,
        domain_policy: str,
        llm: Optional[str] = None,
        llm_args: Optional[dict] = None,
        task=None,
        *,
        run_root: Path,
        group: str,
        skills_dir: Optional[Path] = None,
        model_id: Optional[str] = None,
        relay_base_url: str = "http://127.0.0.1:8141/tau2_retail/consumer/v1",
        node_bin: Path = DEFAULT_NODE,
        openclaw_cli: Path = DEFAULT_CLI,
        agent_timeout_seconds: int = 300,
        turn_timeout_seconds: int = 900,
        settle_seconds: float = 0.35,
        launcher: Optional[Callable] = None,
    ):
        super().__init__(tools=tools, domain_policy=domain_policy)
        self.llm = llm
        self.llm_args = llm_args or {}
        self.task = task
        self.run_root = Path(run_root)
        self.group = group
        self.skills_dir = Path(skills_dir) if skills_dir else None
        self.model_id = model_id or get_model_id()
        self.relay_base_url = relay_base_url
        self.node_bin = Path(node_bin)
        self.openclaw_cli = Path(openclaw_cli)
        self.agent_timeout_seconds = agent_timeout_seconds
        self.turn_timeout_seconds = turn_timeout_seconds
        self.settle_seconds = settle_seconds
        self._launcher = launcher  # test hook: (runtime, prompt, turn) -> InvocationHandle
        self._runtime: Optional[SessionRuntime] = None
        self._lock = threading.Lock()
        self._index_path = self.run_root / "index.jsonl"

    # ------------------------------------------------------------------ init
    def schemas(self) -> list[dict]:
        out = []
        for tool in self.tools:
            schema = tool.openai_schema
            fn = schema.get("function", schema)
            out.append(
                {
                    "name": fn.get("name", tool.name),
                    "description": fn.get("description", ""),
                    "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                }
            )
        return out

    def get_init_state(self, message_history: Optional[list[Message]] = None) -> OpenClawRetailState:
        session_id = uuid.uuid4().hex
        task_id = getattr(self.task, "id", "unknown_task") if self.task else "unknown_task"
        session_dir = self.run_root / self.group / f"task_{task_id}" / session_id
        workspace = session_dir / "workspace"
        state_dir = session_dir / "openclaw_state"
        native_dir = Path("/var/tmp/skillsloop267") / hashlib.sha256(
            str(session_dir).encode()
        ).hexdigest()[:24]
        native_workspace = native_dir / "workspace"
        for path in (workspace, state_dir, native_workspace):
            path.mkdir(parents=True, exist_ok=True)
        (native_dir / "tmp").mkdir(mode=0o700, exist_ok=True)

        # Skills: only the frozen library (B1) or nothing (B0) enters the workspace.
        if self.skills_dir is not None:
            shutil.copytree(self.skills_dir, workspace / "skills", dirs_exist_ok=True)
        else:
            (workspace / "skills").mkdir(exist_ok=True)
        skill_names = sorted(
            path.parent.name for path in (workspace / "skills").rglob("SKILL.md")
        )
        self._skill_names = skill_names
        (workspace / "AGENTS.md").write_text(
            agent_contract(self.domain_policy, skill_names), encoding="utf-8"
        )

        def record(entry: dict) -> None:
            entry["session_id"] = session_id
            with (session_dir / "bridge_calls.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        relay = RetailRelay(
            self.schemas(),
            call_timeout=self.turn_timeout_seconds,
            record_sink=record,
        )
        bridge = McpBridgeServer(relay)
        mcp_url = bridge.start()

        config = build_config(
            workspace=native_workspace,
            model_id=self.model_id,
            relay_base_url=self.relay_base_url,
            mcp_url=mcp_url,
            agent_timeout_seconds=self.agent_timeout_seconds,
        )
        config_path = native_dir / "openclaw.json"
        write_config(config_path, config)

        self._runtime = SessionRuntime(
            session_id=session_id,
            session_dir=session_dir,
            workspace=workspace,
            native_workspace=native_workspace,
            state_dir=native_dir,
            relay=relay,
            bridge=bridge,
            config_path=config_path,
            skills_dir=self.skills_dir,
        )
        index_entry = {
            "session_id": session_id,
            "group": self.group,
            "task_id": task_id,
            "session_dir": str(session_dir),
            "started_at": time.time(),
            "model_id": self.model_id,
            "skills_dir": str(self.skills_dir) if self.skills_dir else None,
        }
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self._index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(index_entry, ensure_ascii=False) + "\n")

        return OpenClawRetailState(
            session_id=session_id,
            session_dir=session_dir,
            first_context=serialize_history(message_history),
        )

    # ------------------------------------------------------------------ turns
    def generate_next_message(
        self, message: ValidAgentInputMessage, state: OpenClawRetailState
    ) -> tuple[AssistantMessage, OpenClawRetailState]:
        if isinstance(message, (ToolMessage, MultiToolMessage)):
            self._deliver_results(message)
            return self._wait_and_respond(state)
        if isinstance(message, UserMessage):
            text = (message.content or "").strip()
            self._start_invocation(state, text)
            return self._wait_and_respond(state)
        raise ValueError(f"Unsupported message type for the OpenClaw adapter: {type(message)}")

    def _deliver_results(self, message) -> None:
        runtime = self._require_runtime()
        results = [message] if isinstance(message, ToolMessage) else message.tool_messages
        delivered = 0
        for result in results:
            call_id = result.id
            if call_id in {call.call_id for call in runtime.pending}:
                runtime.relay.deliver(call_id, result.content or "", error=bool(result.error))
                delivered += 1
        if delivered != len(results):
            raise RuntimeError(
                f"tool results did not match pending calls: {len(results)} results, "
                f"{delivered} matched, pending={[c.call_id for c in runtime.pending]}"
            )
        runtime.pending = []

    def _start_invocation(self, state: OpenClawRetailState, user_text: str) -> None:
        runtime = self._require_runtime()
        if runtime.proc is not None and runtime.proc.poll() is None:
            raise RuntimeError("a previous OpenClaw invocation is still running")
        prompt_parts = []
        if state.turn_index == 0 and getattr(self, "_skill_names", None):
            prompt_parts.append(
                "Before acting, consult the store's reusable skills: "
                + " ".join(f"${name}" for name in self._skill_names)
            )
        if state.turn_index == 0 and state.first_context:
            prompt_parts.append(
                "Context already said in this conversation:\n" + state.first_context
            )
        prompt_parts.append("Customer message:\n" + user_text)
        prompt = "\n\n".join(prompt_parts) + "\n"
        prompt_path = runtime.session_dir / f"turn_{state.turn_index:03d}_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        if self._launcher is not None:
            runtime.proc = self._launcher(runtime, prompt_path, state.turn_index)
        else:
            runtime.proc = self._launch_subprocess(runtime, prompt_path, state.turn_index)

    def _launch_subprocess(self, runtime: SessionRuntime, prompt_path: Path, turn: int):
        # OpenClaw needs its workspace, prompt and logs on the Linux FS:
        # fs-safe atomic rename is unsupported on /mnt/d, and a child blocked
        # writing stdout to 9p hangs in p9_client_rpc. Copy the isolated
        # public workspace each launch (AGENTS.md + skills only) and keep all
        # child I/O native; logs are synced back after exit.
        shutil.copytree(runtime.workspace, runtime.native_workspace, dirs_exist_ok=True)
        native_logs = runtime.state_dir / "turn_logs"
        native_logs.mkdir(parents=True, exist_ok=True)
        native_prompt = native_logs / f"turn_{turn:03d}_prompt.txt"
        shutil.copyfile(prompt_path, native_prompt)
        env = os.environ.copy()
        env.update(
            OPENCLAW_STATE_DIR=str(runtime.state_dir),
            OPENCLAW_CONFIG_PATH=str(runtime.config_path),
            OPENCLAW_NO_RESPAWN="1",
            OPENCLAW_DISABLE_UPDATE_CHECK="1",
            NO_PROXY="127.0.0.1,localhost",
            PYTHONIOENCODING="utf-8",
            TMPDIR=str(runtime.state_dir / "tmp"),
        )
        native_stdout = native_logs / f"turn_{turn:03d}_stdout.json"
        native_stderr = native_logs / f"turn_{turn:03d}_stderr.txt"
        session_stdout = runtime.session_dir / f"turn_{turn:03d}_stdout.json"
        session_stderr = runtime.session_dir / f"turn_{turn:03d}_stderr.txt"
        command = [
            str(self.node_bin),
            str(self.openclaw_cli),
            "agent",
            "--local",
            "--session-id",
            runtime.session_id,
            "--model",
            f"experiment/{self.model_id}",
            "--message-file",
            str(native_prompt),
            "--json",
            "--timeout",
            str(self.agent_timeout_seconds),
        ]
        stdout_handle = native_stdout.open("w", encoding="utf-8")
        stderr_handle = native_stderr.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            command,
            cwd=str(runtime.native_workspace),
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
        return SubprocessInvocation(
            proc, native_stdout, native_stderr, session_stdout, session_stderr
        )

    def _wait_and_respond(
        self, state: OpenClawRetailState
    ) -> tuple[AssistantMessage, OpenClawRetailState]:
        runtime = self._require_runtime()
        if runtime.proc is None:
            raise RuntimeError("no OpenClaw invocation is active")
        deadline = time.time() + self.turn_timeout_seconds
        while True:
            code = runtime.proc.poll()
            if code is not None:
                sync = getattr(runtime.proc, "sync", None)
                if callable(sync):
                    sync()
                unfulfilled = runtime.relay.pending_unfulfilled()
                if unfulfilled:
                    for call in unfulfilled:
                        runtime.relay.fail(call.call_id, "OpenClaw exited before tool results")
                    raise RuntimeError(
                        f"OpenClaw exited (code {code}) with pending tool calls: "
                        f"{[c.name for c in unfulfilled]}"
                    )
                if code != 0:
                    raise RuntimeError(f"OpenClaw invocation failed with exit code {code}")
                text = runtime.proc.final_text()
                runtime.proc = None
                state.turn_index += 1
                if not text:
                    raise RuntimeError("OpenClaw returned an empty assistant message")
                return AssistantMessage(role="assistant", content=text), state
            remaining = deadline - time.time()
            if remaining <= 0:
                runtime.proc.terminate()
                sync = getattr(runtime.proc, "sync", None)
                if callable(sync):
                    sync()
                runtime.proc = None
                raise TimeoutError("OpenClaw invocation exceeded the turn timeout")
            batch = runtime.relay.take_batch(
                timeout=min(0.25, remaining), settle=self.settle_seconds
            )
            if batch:
                runtime.pending = batch
                calls = [
                    ToolCall(id=call.call_id, name=call.name, arguments=call.arguments)
                    for call in batch
                ]
                return (
                    AssistantMessage(role="assistant", tool_calls=calls),
                    state,
                )

    # ------------------------------------------------------------------ stop
    def stop(self, message=None, state=None) -> None:
        runtime = self._runtime
        if runtime is None:
            return
        if runtime.proc is not None:
            runtime.proc.terminate()
            sync = getattr(runtime.proc, "sync", None)
            if callable(sync):
                sync()
            runtime.proc = None
        runtime.bridge.stop()
        try:  # archive the native OpenClaw state next to the run for audits
            archive = runtime.session_dir / "openclaw_state_archive"
            if runtime.state_dir.exists() and not archive.exists():
                shutil.copytree(runtime.state_dir, archive, dirs_exist_ok=True)
        except OSError:
            pass

    def _require_runtime(self) -> SessionRuntime:
        if self._runtime is None:
            raise RuntimeError("agent used before get_init_state")
        return self._runtime


def create_openclaw_retail_agent(
    tools,
    domain_policy: str,
    llm: Optional[str] = None,
    llm_args: Optional[dict] = None,
    task=None,
    **kwargs,
):
    """Factory registered as 'openclaw_retail'. Run config via env:

    TAU2_RETAIL_RUN_ROOT   batch output root        (required)
    TAU2_RETAIL_GROUP      'no_skill'/'autoskill_library'
    TAU2_RETAIL_SKILLS_DIR frozen library (B1) or unset (B0)
    TAU2_RETAIL_RELAY_BASE relay base url for the consumer route
    """
    run_root = os.environ.get("TAU2_RETAIL_RUN_ROOT")
    if not run_root:
        raise RuntimeError("TAU2_RETAIL_RUN_ROOT is not set")
    group = os.environ.get("TAU2_RETAIL_GROUP", "no_skill")
    skills_dir = os.environ.get("TAU2_RETAIL_SKILLS_DIR")
    return OpenClawRetailAgent(
        tools=tools,
        domain_policy=domain_policy,
        llm=llm,
        llm_args=llm_args,
        task=task,
        run_root=Path(run_root),
        group=group,
        skills_dir=Path(skills_dir) if skills_dir else None,
        relay_base_url=os.environ.get(
            "TAU2_RETAIL_RELAY_BASE", "http://127.0.0.1:8141/tau2_retail/consumer/v1"
        ),
    )
