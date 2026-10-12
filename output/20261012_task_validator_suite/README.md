# 每任务终态基本交付校验脚本

本包对应最新 v10 的 **226 条完整评测会话、12 类任务**，按完整会话的最终状态评分。`scripts/` 每条会话有一个独立 Python 入口，`contracts/` 是该入口固定的验收条件；`manifest.json` 给出具体任务名、概要、入口、哈希和检查数量。`打开这里.html` 逐任务直接展示“检查对象、通过条件、取证方法、用户要求依据、校验参数”，无需展开隐藏字段。

审核依据为用户提供的《EvoMind 实验评测 pipeline 设计 图文版》：必需基本交付点做 AND；产物确实缺失、数量不符或明确字段不符才给 0；取证不足、解析器不可用或指代无法确定给 `UNSCORED`；质量留给另一条评测链。审核通过表示这些基本条件可执行，不表示 226 条业务任务已执行成功，也不表示所有运行环境已重新认证。本轮没有运行业务任务或调用模型。

## 运行

Python 3.10+；实际图片/PDF解析需要 Pillow 和 pypdf，旧 DOC/XLS 沿用原评分器的 LibreOffice/Docker 转读路径，没有该工具返回 `UNSCORED`。正式评分不依赖 pytest/reportlab，二者仅供离线控制测试。每个脚本只读取本次工作区和独立证据，不调用业务 API。

最终已测环境为 Python 3.12.14、Pillow 12.3.0、pypdf 6.10.0、pytest 8.3.5、reportlab 4.4.9；`requirements.txt` 固定这些库版本。测试依赖在本机现有两个 Python 环境中，`verification/verify_controls.py` 只在缺 pytest 时复用现有纯 Python 测试库；无需修改业务容器。

```powershell
# 一个任务：manifest.json 中找到其具体中文脚本路径
python "scripts/任务类别/具体任务名_conv_xxxxxxxxxxxx.py" --describe
python "scripts/任务类别/具体任务名_conv_xxxxxxxxxxxx.py" request.json response.json

# 通用 command 插件；按 source_session_id 路由到同一冻结任务
python score.py request.json response.json

# 同一模型同一次 attempt：一个任务一个 response.json
python summarize_scores.py "responses/" "summary.json"
```

命令执行成功的退出码 0 表示评分器已输出结果，**不代表任务通过**。必须读 `response.json` 中 `valid`、`score`、`task_success_status`：`PASS`/1、`FAIL`/0、`UNSCORED`/null。所有必需点通过才 PASS；观测点不进入 AND。不同 attempt/实验臂独立汇总，固定分母 226 和每类任务数；有缺测时正式 Micro/Macro 不生成，只报告 coverage 和已测条件下的比例，不能偷偷缩小分母。

## 请求和证据

沿用现有 `task-group-plugin-v1` 的请求/响应协议：

```json
{
  "task_id": "heldout_conv_xxxxxxxxxxxx",
  "source_session_id": "conv_xxxxxxxxxxxx",
  "workspace": "D:/本次独立工作区",
  "result": {"turn_answers": ["本次逐轮实际回复"]},
  "evidence_path": "D:/本次独立取证目录/final_state_evidence.json"
}
```

独立控制器在会话结束后生成 `final-state-evidence-v1`，也可放 `result.final_state_evidence_path` 或请求内 `evidence`。简化结构如下（以下路径、哈希、文字均为协议示意，不能作为真实任务证据）：

```json
{
  "schema": "final-state-evidence-v1",
  "source_session_id": "conv_xxxxxxxxxxxx",
  "workspace": "D:/本次独立工作区",
  "conversation_complete": true,
  "measurement": {"namespace": "final_state_measurement", "status": "collected", "initial_snapshot_complete": true},
  "initial_sha256": {},
  "declared_input_sha256": {},
  "deliveries": {
    "delivery_01": {"text": "这一独立交付的最终正文"},
    "delivery_02": {"files": ["outputs/report.docx"]},
    "delivery_03": {"directory": "skills/my-skill"}
  },
  "service_readbacks": [],
  "resolved_parameters": {}
}
```

`initial_sha256` 必须是本次工作区运行前的完整文件 SHA-256 库存，`declared_input_sha256` 是实际用户输入附件库存。禁止把未知库存伪装成空字典，明确不完整或非法哈希会缺测。产物重命名复制旧文件仍不是新交付；实际新增/修改的技能资源也算包的变更，不强制只改 SKILL.md。用户仅要求获取/展示既有照片或引用既有文件的任务有显式例外。按工作区边界解析，容器 `/workspace` 路径映射到本次 host 工作区，不读取另一个会话的产物。

每个独立交付必须有自己的最终文字、文件或状态绑定，不把总答复广播给全部交付。文件存在和可原生读取是基础；任务涉及页数、格式、图像尺寸、指定文本、附件对应、多个独立文件时再核冻结参数。文字型任务这里只证明正文交付，不能据非空声称事实正确或合同分析正确。历史 AI 不提供给 actor，不作为评分金标准；过程中恢复成功的工具错误也不扣分。

服务读回必须由独立控制器取得，记录服务、delivery_id、`observation: final_readback`、`authoritative: true`、`complete: true` 和真实 records。收件人、主题、附件、草稿/发送状态，会议时间/参与者，定时登记字段等同一对象上的全部参数必须同时满足，不能拼接几个不同对象。定时任务只核真实登记，不等待触发。固定参数不能拿已观察到的错误结果反填成期望值；账户、相对日期、本次选择的目标等动态参数必须来自本次独立上下文解析。

## 需要额外取证的检查

这些检查器已实现，但测量层必须提供对应真实证据；没有时返回 `UNSCORED`。不得用原轨迹中的 AI 声明、终态自选子集或虚构证据补齐。

| 条件 | 独立证据 |
|---|---|
| 本次提示词对应的图像集合 | `manifest_snapshots[delivery_id].pages` 在生图前冻结条目、原实际提示词 delivery_id 和正文 SHA；最终 `deliveries[delivery_id].manifests.pages` 条目绑定实际可解码图片。用户直接列出的分镜使用合同冻结条目。 |
| 检索后下载集合 | `manifest_snapshots[delivery_id].download_results` 在下载前冻结本次已选定可下载 item_ids；终态 `manifests.download_results.items` 给实际 path/SHA，全部覆盖。不是穷尽全球文献。 |
| PDF 的原输入对应和新增明确文字 | 合同固定输入附件路径/原 SHA/用户轮次；`manifests.pdf_source_outputs.items` 提供 input_path/input_sha256/input_user_turn/output_path。原输入需仍可读，避免覆盖原件后丢失比较依据。不能用正文同名字符冒称视觉水印。 |
| 原表格照片保留与高度 | `manifests.source_photos` 给本次实际源表 path/SHA/照片数；原生关系、图片字节和可解析几何参与检查，不据图片文件名认证。 |
| 最后 PDF 的本次来源图像顺序 | 本次工作区实际命名图像或独立别名绑定，与 PDF 实际绘制图像逐页解码比较；有损/复合结构不能证明时缺测。 |
| “重新生成，不用本次前期图像” | `image_baseline_snapshots[delivery_id]` 在指定用户轮之前冻结本次旧图路径/SHA；比较实际解码像素，不评分是否调用了某工具。 |
| 修改同一条定时任务的 timeout | `timeout_initial_dispatch_0001.json` 的本次真实 job_id/来源 job_id/初值及哈希绑定的末态 transition；同一 job 的最终值增加，无精确值时不编造数值。 |
| “这个 skill” 的当前指代 | 在安装请求派发前独立记录 `resolved_parameters[delivery_id].selection_binding`，绑定本次此前回复 SHA、轮序、选中名字和实际目录。不能把必要安装降为观测以获得通过。 |
| 文件应在指定目录 | 当前工作区内独立解参后的实际目录与实际文件路径，不允许凭 actor 口头创建。 |

详细字段以 `artifact_extensions_normalization.json`、`text_extensions_normalization.json`、实际 contract 和离线测试为准。已有证据收集器位于 `research/pipelines/task_group_pipeline/final_state_evidence.py`，本包没有修改它；本轮新加集合/基线字段必须由控制器按上述时机补采，不能认为旧收集器已经全部自动提供。视觉水印、语义报价条款、函件事实配对，以及允许跨章修改但边界不确定的章节比较留为观测，不能据此认证。

## 接入和版本

在**新建的评测配置副本**中把 scorer command 设为 `['<实际Python解释器>', '<本包绝对路径>/score.py', '{request}', '{response}']`。生成的 `scorer.config.fragment.json` 是可直接合并的具体配置块，并列出全部合同和实现固定文件。现有冻结配置、v10 数据和原评分器没有改写。不能把新检查器运行结果与旧评分规则的运行结果当作同版本直接合并。

验收合同、共享实现和每任务入口有 SHA 固定，篡改合同/实现会缺测；`--describe` 显示的五字段与执行合同相同，调用方传入另一份 final_contract 无法覆盖。正式运行之前先确认控制器额外证据采集完整并新建代码快照。

`verification/` 保存历史 RED、修复后 GREEN、独立复核和全任务入口核验；`audit/` 保存三组逐点审查、原 462 点的处理决定和追加点。本包的离线构造控制不等于真实会话的业务成功率。
