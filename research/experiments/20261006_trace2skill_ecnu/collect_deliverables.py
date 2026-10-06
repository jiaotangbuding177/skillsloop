"""Offline delivery copies, with content hashes equal to original model-generated candidates."""
import hashlib, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "private/run_v3"
OUT = HERE / "deliverables"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    state = json.loads((RUN / "run.json").read_text(encoding="utf-8"))
    if state["status"].startswith("RUNNING"):
        raise ValueError("Do not deliver a running experiment")
    if OUT.exists():
        raise ValueError("Existing deliverables preserved")
    OUT.mkdir()
    manifest = {"run": "run_v3", "status": state["status"], "candidates": {},
        "copies_only": True, "task_benefit": "NOT_EVALUATED", "not_registered": True}
    rows = []
    labels = {"A": "直接学习版", "B": "任务与轨迹恢复版"}
    for arm in ("A", "B"):
        entry = {"status": state["arms"].get(arm, {}).get("status"), "files": []}
        source = RUN / arm / "skills/spreadsheet-generation-audit"
        if source.is_dir():
            target = OUT / arm / "spreadsheet-generation-audit"
            shutil.copytree(source, target)
            for path in source.rglob("*"):
                if not path.is_file():
                    continue
                copy = target / path.relative_to(source)
                if digest(copy) != digest(path):
                    raise ValueError("Delivered content differs from frozen candidate")
                entry["files"].append({"path": str(copy.relative_to(OUT)), "sha256": digest(copy),
                    "origin": str(path.relative_to(HERE))})
            for package in (RUN / arm / "packages").glob("*.skill"):
                destination = OUT / arm / package.name
                shutil.copy2(package, destination)
                if digest(destination) != digest(package):
                    raise ValueError("Package copy differs")
                entry["files"].append({"path": str(destination.relative_to(OUT)),
                    "sha256": digest(destination), "origin": str(package.relative_to(HERE))})
            rows.append(f"| {labels[arm]} | [{arm}/SKILL.md]({arm}/spreadsheet-generation-audit/SKILL.md) | [{arm}/.skill包]({arm}/spreadsheet-generation-audit.skill) |")
        else:
            rows.append(f"| {labels[arm]} | 未生成 | 未生成 |")
        manifest["candidates"][arm] = entry
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = "# 本次实验生成的技能\n\n同一表格技能的实验版本，文件与正式生成物字节一致，未人工修正文案、注册或验证新任务收益。\n\n| 版本 | 技能正文 | 技能包 |\n|---|---|---|\n" + "\n".join(rows)
    generated = [a for a, e in manifest["candidates"].items() if e["files"]]
    if len(generated) == 2:
        text += "\n\n两个版本的技能名称相同，用于分开的实验条件；不要把它们当作两个不同功能技能同时注册。"
    else:
        text += "\n\n本轮实际只有直接学习版技能。恢复组没有完成生成，没有第二个技能包。"
    text += "具体生成质量和失败记录见[总实验报告](../../../reports/2026-10-06_trace2skill_ecnu_generation_pilot.md)。\n"
    (OUT / "README.md").write_text(text, encoding="utf-8")
    print(json.dumps({"status": state["status"], "deliverables": str(OUT),
        "generated_versions": [a for a, e in manifest["candidates"].items() if e["files"]],
        "byte_identical": True}, ensure_ascii=False))

if __name__ == "__main__":
    main()
