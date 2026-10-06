"""Offline unit tests for the OpenClaw retail adapter and MCP relay.

No model calls, no OpenClaw process: a FakeOpenClaw simulates the consumer's
side of the suspend-and-relay protocol (it calls the relay exactly like the
real MCP client would, and blocks until tau2's result is delivered).

Run:  runtime_py/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mcp_retail_bridge import PendingCall, RetailRelay  # noqa: E402
from tau2_openclaw_agent import (  # noqa: E402
    InvocationHandle,
    OpenClawRetailAgent,
    extract_payload_text,
)
from tau2.data_model.message import ToolMessage, UserMessage  # noqa: E402


class FakeTool:
    """Minimal stand-in with the tau2 Tool surface the adapter uses."""

    def __init__(self, name: str):
        self.name = name

    @property
    def openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"official {self.name}",
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                },
            },
        }


class FakeOpenClaw(InvocationHandle):
    """Scripted consumer side of one invocation.

    Script items: ("tool", name, args) blocks until the result arrives;
    a final string ends the turn with that text.
    """

    def __init__(self, relay: RetailRelay, script: list):
        self.relay = relay
        self.script = list(script)
        self.tool_results: list[tuple[str, str]] = []
        self._rc: int | None = None
        self._text: str | None = None
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            for step in self.script:
                if isinstance(step, tuple) and step[0] == "tool":
                    pending = self.relay.begin_call(step[1], step[2])
                    text = pending.wait(30)
                    self.tool_results.append((pending.name, text))
                else:
                    self._text = str(step)
                    self._rc = 0
                    self._done.set()
                    return
            # Script without a final text: stay alive (turn still in progress).
        except Exception as error:  # pragma: no cover - failure path
            self._text = f"fake failure: {error}"
            self._rc = 1
            self._done.set()

    def poll(self) -> int | None:
        return self._rc if self._done.is_set() else None

    def terminate(self) -> None:
        self._rc = self._rc if self._rc is not None else 1
        self._done.set()

    def final_text(self) -> str:
        if self._rc != 0:
            raise RuntimeError(self._text or "failed")
        return self._text or ""


def make_agent(tmp: Path, scripts: list[list], skills_dir: Path | None = None) -> tuple[OpenClawRetailAgent, list]:
    """Agent whose launcher serves `scripts[turn]` for each invocation."""
    launchers: list[FakeOpenClaw] = []

    def launcher(runtime, prompt_path, turn):
        fake = FakeOpenClaw(runtime.relay, scripts[turn])
        launchers.append(fake)
        return fake

    agent = OpenClawRetailAgent(
        tools=[FakeTool("get_order_details"), FakeTool("cancel_pending_order")],
        domain_policy="POLICY TEXT",
        task=type("T", (), {"id": "0"})(),
        run_root=tmp,
        group="no_skill",
        skills_dir=skills_dir,
        launcher=launcher,
        settle_seconds=0.05,
        turn_timeout_seconds=20,
    )
    return agent, launchers


def user(text: str) -> UserMessage:
    return UserMessage(role="user", content=text)


def tool_result(call_id: str, content: str, error: bool = False) -> ToolMessage:
    return ToolMessage(id=call_id, role="tool", content=content, requestor="assistant", error=error)


class AdapterTests(unittest.TestCase):
    def test_01_schemas_exposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent, _ = make_agent(Path(tmp), [["done"]])
            schemas = agent.schemas()
            self.assertEqual([s["name"] for s in schemas], ["get_order_details", "cancel_pending_order"])
            self.assertEqual(schemas[0]["parameters"]["required"], ["order_id"])

    def test_02_single_tool_roundtrip_then_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = [[("tool", "get_order_details", {"order_id": "#W1"}), "Your order is delivered."]]
            agent, fakes = make_agent(Path(tmp), scripts)
            state = agent.get_init_state()
            message, state = agent.generate_next_message(user("Where is my order?"), state)
            self.assertEqual(len(message.tool_calls), 1)
            call = message.tool_calls[0]
            self.assertEqual(call.name, "get_order_details")
            self.assertEqual(call.arguments, {"order_id": "#W1"})
            self.assertEqual(call.requestor, "assistant")
            message, state = agent.generate_next_message(tool_result(call.id, '{"status": "delivered"}'), state)
            self.assertEqual(message.tool_calls, None)
            self.assertEqual(message.content, "Your order is delivered.")
            self.assertEqual(fakes[0].tool_results, [("get_order_details", '{"status": "delivered"}')])
            ledger = list((state.session_dir / "bridge_calls.jsonl").read_text().strip().splitlines())
            record = json.loads(ledger[0])
            self.assertEqual(record["call_id"], call.id)
            self.assertEqual(record["executor"], "tau2_orchestrator")
            self.assertFalse(record["result_error"])

    def test_03_two_sequential_calls_in_one_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = [
                [
                    ("tool", "get_order_details", {"order_id": "#W1"}),
                    ("tool", "cancel_pending_order", {"order_id": "#W1"}),
                    "Cancelled.",
                ]
            ]
            agent, fakes = make_agent(Path(tmp), scripts)
            state = agent.get_init_state()
            message, state = agent.generate_next_message(user("cancel it"), state)
            first = message.tool_calls[0]
            message, state = agent.generate_next_message(tool_result(first.id, "ok1"), state)
            self.assertIsNotNone(message.tool_calls)
            second = message.tool_calls[0]
            self.assertEqual(second.name, "cancel_pending_order")
            self.assertNotEqual(second.id, first.id)
            message, state = agent.generate_next_message(tool_result(second.id, "ok2"), state)
            self.assertEqual(message.content, "Cancelled.")
            self.assertEqual([r[1] for r in fakes[0].tool_results], ["ok1", "ok2"])

    def test_04_two_turns_session_continuity(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = [
                [("tool", "get_order_details", {"order_id": "#W1"}), "Delivered on Monday."],
                ["Anything else?", ],
            ]
            agent, fakes = make_agent(Path(tmp), scripts)
            state = agent.get_init_state()
            message, state = agent.generate_next_message(user("q1"), state)
            call = message.tool_calls[0]
            message, state = agent.generate_next_message(tool_result(call.id, "ok"), state)
            self.assertEqual(message.content, "Delivered on Monday.")
            message, state = agent.generate_next_message(user("thanks"), state)
            self.assertEqual(message.content, "Anything else?")
            self.assertEqual(len(fakes), 2)
            self.assertEqual(state.turn_index, 2)

    def test_05_error_tool_result_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = [[("tool", "get_order_details", {"order_id": "#bad"}), "Sorry, I could not find it."]]
            agent, _ = make_agent(Path(tmp), scripts)
            state = agent.get_init_state()
            message, state = agent.generate_next_message(user("lookup"), state)
            call = message.tool_calls[0]
            message, state = agent.generate_next_message(
                tool_result(call.id, "Error: order not found", error=True), state
            )
            self.assertEqual(message.content, "Sorry, I could not find it.")
            record = json.loads((state.session_dir / "bridge_calls.jsonl").read_text().strip())
            self.assertTrue(record["result_error"])

    def test_06_unknown_result_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = [[("tool", "get_order_details", {"order_id": "#W1"}), "end"]]
            agent, _ = make_agent(Path(tmp), scripts)
            state = agent.get_init_state()
            message, state = agent.generate_next_message(user("q"), state)
            with self.assertRaises(RuntimeError):
                agent.generate_next_message(tool_result("not_a_real_call", "x"), state)

    def test_07_skills_dir_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = Path(tmp) / "frozen_skills"
            (frozen / "policy_helper").mkdir(parents=True)
            (frozen / "policy_helper" / "SKILL.md").write_text("# helper\n", encoding="utf-8")
            agent_b1, _ = make_agent(Path(tmp) / "b1", [["end"]], skills_dir=frozen)
            state = agent_b1.get_init_state()
            self.assertTrue((state.session_dir / "workspace" / "skills" / "policy_helper" / "SKILL.md").exists())
            agent_b0, _ = make_agent(Path(tmp) / "b0", [["end"]])
            state0 = agent_b0.get_init_state()
            self.assertEqual(list((state0.session_dir / "workspace" / "skills").iterdir()), [])

    def test_08_relay_timeout_marks_error(self):
        relay = RetailRelay([{"name": "t", "description": "", "parameters": {}}], call_timeout=0.2)
        pending = relay.begin_call("t", {})
        with self.assertRaises(TimeoutError):
            pending.wait(0.2)

    def test_09_extract_payload_text(self):
        self.assertEqual(extract_payload_text({"payloads": [{"text": "a"}, {"text": "b"}]}), "a\nb")
        self.assertEqual(extract_payload_text({"result": {"payloads": [{"text": "x"}]}}), "x")

    def test_10_config_contains_native_mcp_and_tool_policy(self):
        from openclaw_config import build_config

        config = build_config(
            workspace=Path("/tmp/ws"),
            model_id="GLM-5.3-Flash",
            relay_base_url="http://127.0.0.1:8129/tau2_retail/consumer/v1",
            mcp_url="http://127.0.0.1:9999/mcp",
        )
        self.assertIn("read", config["tools"]["allow"])
        self.assertIn("retail__*", config["tools"]["allow"])
        self.assertEqual(config["mcp"]["servers"]["retail"]["transport"], "streamable-http")
        self.assertEqual(config["skills"]["allowBundled"], ["__experiment_no_bundled_skills__"])
        self.assertNotIn("exec", config["tools"]["allow"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
