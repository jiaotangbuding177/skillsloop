"""Suspend-and-relay MCP tool bridge for the retail experiment.

The bridge exposes the official retail tool schemas over MCP (streamable
HTTP). A call arriving here is NOT executed: it is captured, handed to the
tau2-side adapter, and held open until the adapter delivers the result of
the single official execution performed by tau2's orchestrator. This keeps
exactly-once business writes and the native tau2 message record intact.

Threading model:
- The MCP server runs uvicorn on a background thread (its own event loop).
- Each call_tool handler awaits PendingCall.wait() on a worker thread.
- The adapter's main thread (tau2 orchestrator) takes captured calls from a
  queue, returns them to tau2, and later delivers results via PendingCall.
"""
from __future__ import annotations

import json
import queue
import socket
import threading
import time
import traceback
import uuid
from typing import Callable, Optional

import anyio
import mcp.types as types
import uvicorn
from mcp.server.lowlevel import Server

MAX_LEDGER_TEXT = 20000


class PendingCall:
    """One captured retail tool call awaiting the tau2-side execution result."""

    __slots__ = (
        "call_id",
        "name",
        "arguments",
        "created_at",
        "is_error",
        "_event",
        "_result",
        "_error",
    )

    def __init__(self, call_id: str, name: str, arguments: dict):
        self.call_id = call_id
        self.name = name
        self.arguments = arguments
        self.created_at = time.time()
        self.is_error = False
        self._event = threading.Event()
        self._result: Optional[str] = None
        self._error: Optional[str] = None

    def wait(self, timeout: float) -> str:
        """Blocks until the adapter delivers the result (MCP handler thread)."""
        if not self._event.wait(timeout):
            raise TimeoutError(
                f"retail tool call {self.name} ({self.call_id}) timed out awaiting "
                f"tau2 execution after {timeout}s"
            )
        if self._error is not None:
            raise RuntimeError(self._error)
        return self._result or ""

    def deliver(self, text: str, error: bool = False) -> None:
        """Deliver the official execution result.

        `error=True` marks an error ToolMessage from the tau2 environment; the
        text is still delivered to the model (native tau2 semantics: tool
        errors are part of the conversation, not bridge failures).
        """
        self._result = text
        self.is_error = error
        self._event.set()

    def fail(self, error: str) -> None:
        """Bridge-level failure (never masks a real official result)."""
        self._error = error
        self._event.set()

    def wait_seconds(self) -> float:
        return max(0.0, time.time() - self.created_at)


class RetailRelay:
    """Captures MCP tool calls and exposes them to the adapter as batches."""

    def __init__(
        self,
        schemas: list[dict],
        *,
        call_timeout: float = 900.0,
        record_sink: Optional[Callable[[dict], None]] = None,
    ):
        # schemas: [{"name": str, "description": str, "parameters": {json schema}}]
        self.schemas = {s["name"]: s for s in schemas}
        self.call_timeout = call_timeout
        self._record_sink = record_sink
        self._queue: "queue.Queue[PendingCall]" = queue.Queue()
        self._lock = threading.Lock()
        self._seq = 0
        self.calls: dict[str, PendingCall] = {}
        self.records: list[dict] = []

    # -- MCP handler side --------------------------------------------------
    def begin_call(self, name: str, arguments: dict) -> PendingCall:
        with self._lock:
            self._seq += 1
            call_id = f"retail_{self._seq:04d}_{uuid.uuid4().hex[:8]}"
            pending = PendingCall(call_id, name, arguments)
            self.calls[call_id] = pending
        self._queue.put(pending)
        return pending

    # -- adapter side -------------------------------------------------------
    def take_batch(self, timeout: float, settle: float) -> list[PendingCall]:
        """Block up to `timeout` for the first call, then `settle` for siblings."""
        try:
            first = self._queue.get(timeout=max(0.0, timeout))
        except queue.Empty:
            return []
        batch = [first]
        deadline = time.time() + max(0.0, settle)
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                batch.append(self._queue.get(timeout=remaining))
            except queue.Empty:
                break
        return batch

    def pending_unfulfilled(self) -> list[PendingCall]:
        with self._lock:
            return [c for c in self.calls.values() if not c._event.is_set()]

    def deliver(self, call_id: str, text: str, *, error: bool = False) -> None:
        pending = self.calls.get(call_id)
        if pending is None:
            raise KeyError(f"unknown tool call id {call_id}")
        pending.deliver(text, error=error)
        record = {
            "call_id": call_id,
            "name": pending.name,
            "arguments": pending.arguments,
            "delivered_result": text[:MAX_LEDGER_TEXT],
            "result_truncated": len(text) > MAX_LEDGER_TEXT,
            "result_error": error,
            "wait_seconds": round(pending.wait_seconds(), 3),
            "delivered_at": time.time(),
            "executor": "tau2_orchestrator",
        }
        self.records.append(record)
        if self._record_sink is not None:
            self._record_sink(record)

    def fail(self, call_id: str, error: str) -> None:
        pending = self.calls.get(call_id)
        if pending is None:
            return
        pending.fail(error)
        self.records.append({"call_id": call_id, "name": pending.name, "error": error})


def build_server(relay: RetailRelay) -> Server:
    """mcp>=2 handler-style server exposing the relayed retail tools."""

    async def on_list_tools(context, params):
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=s["name"],
                    description=s.get("description") or s["name"],
                    inputSchema=s.get("parameters")
                    or {"type": "object", "properties": {}},
                )
                for s in relay.schemas.values()
            ]
        )

    async def on_call_tool(context, params):
        name = params.name
        arguments = params.arguments or {}
        pending = relay.begin_call(name, arguments)
        try:
            text = await anyio.to_thread.run_sync(pending.wait, relay.call_timeout)
        except Exception as error:  # surfaced to the model as a tool error text
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Error: tool bridge could not obtain the official result ({error})",
                    )
                ],
                isError=True,
            )
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])

    return Server("tau2-retail-bridge", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


def pick_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


class McpBridgeServer:
    """Runs the MCP server for one simulation on a background thread."""

    def __init__(self, relay: RetailRelay, host: str = "127.0.0.1", port: int = 0):
        self.relay = relay
        self.host = host
        self.port = port or pick_free_port(host)
        self._thread: Optional[threading.Thread] = None
        self._uvicorn: Optional[uvicorn.Server] = None
        self._error: Optional[str] = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"

    def start(self) -> str:
        self._thread = threading.Thread(target=self._run, name="mcp-retail-bridge", daemon=True)
        self._thread.start()
        if not wait_for_port(self.port, self.host):
            raise RuntimeError(f"MCP bridge did not open port {self.port}: {self._error}")
        return self.url

    def _run(self) -> None:
        try:
            asyncio_loop = __import__("asyncio").new_event_loop()
            __import__("asyncio").set_event_loop(asyncio_loop)
            asyncio_loop.run_until_complete(self._serve())
        except Exception:
            self._error = traceback.format_exc()

    async def _serve(self) -> None:
        server = build_server(self.relay)
        app = server.streamable_http_app(
            streamable_http_path="/mcp", json_response=False, stateless_http=True
        )
        config = uvicorn.Config(
            app=app, host=self.host, port=self.port, log_level="warning", access_log=False
        )
        self._uvicorn = uvicorn.Server(config)
        await self._uvicorn.serve()

    def stop(self) -> None:
        if self._uvicorn is not None:
            self._uvicorn.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=10)


def main() -> None:
    """Standalone smoke test: serve schemas from a JSON file, print the URL."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas", required=True, help="JSON file: list of tool schemas")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    schemas = json.loads(open(args.schemas, encoding="utf-8").read())
    relay = RetailRelay(schemas)
    server = McpBridgeServer(relay, port=args.port)
    url = server.start()
    print(f"listening: {url}", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
