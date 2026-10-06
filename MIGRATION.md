# 新环境接续实验

本次数据迁移位于 **`codex/direct-trace-skill-pipeline` 分支**，默认 `main` 还包含另一条实验线。请明确选择这个分支，避免拉到旧数据版本。

## 拉取及数据完整性核验

先在新环境安装 Git 和 Git LFS，再执行：

```bash
git lfs install
git clone --recurse-submodules --branch codex/direct-trace-skill-pipeline https://github.com/jiaotangbuding177/skillsloop.git
cd skillsloop
git lfs pull
git submodule update --init --recursive
python3 research/transfer/20261006_git_data_migration/prepare_author_checkout.py
python3 research/transfer/20261006_git_data_migration/verify_clone.py
```

核验脚本逐文件检查数据大小及SHA，检查作者独立仓库的提交与550项原源码哈希；遇到LFS占位指针、漏文件或不同源码即报错。它不调用模型。不要跳过这个步骤。

## 数据在哪里

| 材料 | 仓库内位置 |
|---|---|
| 全部研究记忆、研究状态及报告 | `research/memory/`、`research/STATE.md`、`research/reports/` |
| 两份原始导出（仅遮蔽凭据） | `research/datasets/evomind/raw_sources_20261006/zkys-raw-export-20260925/`、同目录下 `zkys-skill-mining-20260925/` |
| 三份原始人工标注备份 | `research/datasets/evomind/raw_sources_20261006/human_annotations/` |
| 全部历史整理版本 | `research/datasets/evomind/`，从预览、清理、匹配、人工确认到主题划分，保留各版原目录 |
| 当前企业学习主数据 | `research/datasets/evomind/task_topics_20261006/`：1224会话、719候选；完整原文在 `private/`，不是只有索引 |
| 用户最初的系统报告及原始规范 | `research/sources/user_supplied_20261006/` |
| 作者原始算法、原技能及公开校准数据 | `research/baselines/Trace2Skill/`：固定版本子模块 |
| 本轮原生实验源码、输入、模型响应、失败证据、生成物 | `research/experiments/20261006_trace2skill_native_baseline/` |
| 实验生成的完整技能 | 上述目录 `deliverables/enterprise_monthly_salary/xlsx/` |
| 迁移复制记录与逐文件核验清单 | `research/transfer/20261006_git_data_migration/` |

`private` 是历史目录名称，本次按用户明确要求纳入上传。原始会话文件没有补造附件、工具全量日志、缺失产物或业务结果。Windows程序安装文件、依赖包目录、缓存和凭据不上传；实际模型请求／响应及失败报告保留。旧会话中的GitHub令牌及导出脚本中的数据库凭据只在上传副本中遮蔽，本地原件保留；逐文件原始／上传SHA见迁移目录中的 `credential_redaction_manifest.json`。新环境按上传SHA核验，历史来源SHA保留为原件依据，不假称遮蔽前后字节一致。

## 新环境从哪里继续

1. 先读 `AGENTS.md`、`research/README.md`、`research/CHARTER.md` 和 `research/STATE.md`。本项目持续采用科研路线，上传不是新的效果实验。
2. 核对[当前原生实验报告](research/reports/2026-10-06_trace2skill_native_baseline_execution.md)。已有技能深化生成及保存响应回放通过；公开校准、真实消费和真实失败修复尚未执行。
3. Linux依赖及容器准备见[环境文档](research/experiments/20261006_trace2skill_native_baseline/linux_runtime/README.md)。Dockerfile尚未构建验收；新环境必须记录实际镜像、Python、模型SDK、LibreOffice及包版本。
4. 实际封装检查器已经随实验保存于 `private/runtime_preflight/runtime/skills/skill-creator/scripts/quick_validate.py`；另有同字节的稀疏原路径副本供既有回放脚本定位，无需上传整个OpenClaw运行时。原生入口工作目录必须是 `private/runtime_preflight/runtime/`，输入和输出参数用绝对路径。
5. 先免费验证原LibreOffice重算脚本：正常公式必须得到真实缓存，除零错误必须被拒绝；同时核原评分正反例、目标技能非空注入和Bash依赖。通过后在本机生成新的Linux环境证明，再启动付费原生校准／消费；不要把Windows失败记录改成通过。

## 旧路径和版本边界

原始证据中的 `D:\skillsgen-industry_track\...`、`C:\Users\39835\Downloads\...` 是来源说明，不改写它们。部分历史整理脚本仍从Downloads绝对路径读取原始导出；重做数据整理时应在新的外层入口映射到上述 `raw_sources_20261006`，保留旧脚本和旧数据的SHA，另开运行记录。

`real_call_replay.py` 仍直接读取旧清单里的Windows日志绝对路径。Linux回放须通过只读路径映射，限定原项目根到新克隆根并核原文件SHA；这次上传未静默重写旧清单或旧付费请求。不要因此将路径失败算成算法负结果。

作者子模块必须保持提交 `3d0b52a140f002a512930252b613c49048f7d5ac`，不把它替换成父仓库文件后关闭版本校验。本次数据上传也不补齐Creation未公开初稿、论文模型权重或未认证的版本对应关系。

历史付费清单有225项文件使用Windows CRLF表示，作者HEAD原blob为LF；另外325项及初始xlsx三资源与原blob字节相同。`prepare_author_checkout.py` 先全量验证独立仓库、固定commit和干净状态，只在原blob做LF→CRLF后SHA精确等于历史清单时恢复该表示，保留双哈希记录。它不修改作者算法或旧清单，随后仍须550项历史SHA全部通过；不能靠关闭源码校验绕过差异。

模型密钥在新环境自行通过进程环境提供，不随Git分发。继续实验前先完成环境控制，不运行Windows专用诊断脚本，也不自动重跑已完成的付费生成。
