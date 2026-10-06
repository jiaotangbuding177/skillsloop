"""One bounded synthetic API calibration; no enterprise data, no credential persistence."""
import hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
out = ROOT / "private" / "calibration"
out.mkdir(parents=True, exist_ok=True)
target = out / "api_probe.json"
if target.exists():
    raise SystemExit("Probe already recorded; inspect it rather than silently retry.")
key = os.environ.get("ECNU_API_KEY")
if not key:
    raise SystemExit("Missing runtime ECNU_API_KEY.")
base = "https://chat.ecnu.edu.cn/open/api/v1"
payload = {
    "model": "ecnu-plus",
    "messages": [{"role":"user","content":"这是接口校准，不是任务实验。请仅回复 JSON：{\"ready\":true}"}],
    "temperature": 0,
    "max_tokens": 256,
    "stream": False,
}
req = urllib.request.Request(base + "/chat/completions",
    data=json.dumps(payload, ensure_ascii=False).encode(),
    headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
record = {"purpose":"synthetic API calibration", "requested_model":"ecnu-plus",
          "base_url":base, "request":payload, "max_requests":1}
start = time.monotonic()
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = resp.read()
        record["http_status"] = resp.status
    data = json.loads(body)
    record["response"] = data
    msg = data.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "") or ""
    try:
        parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        record["valid"] = parsed.get("ready") is True
    except (ValueError, AttributeError):
        record["valid"] = False
except Exception as exc:
    record["valid"] = False
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc).replace(key, "[REDACTED]")
    if isinstance(exc, urllib.error.HTTPError):
        record["http_status"] = exc.code
        record["error_body"] = exc.read().decode("utf-8", errors="replace").replace(key, "[REDACTED]")
finally:
    record["elapsed_seconds"] = round(time.monotonic()-start,3)
    text = json.dumps(record, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
    target.write_text(text, encoding="utf-8")
    print(json.dumps({k:record.get(k) for k in ["valid","http_status","error_type","elapsed_seconds"]}))
    if "response" in record:
        print(json.dumps({"served_model":record["response"].get("model"),
                         "usage":record["response"].get("usage")}))

