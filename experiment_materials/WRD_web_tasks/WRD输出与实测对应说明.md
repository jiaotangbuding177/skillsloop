# WRD 最终输出与实测对应说明（更正版）

## 对应关系核验

以下 WRD（trace2skill 臂）最终输出已与 2026-10-23 浏览器实测归档中的 `final/candidate_index.json` 记录的 `html_sha256` 逐一比对，**字节级一致**（非"原首页.html"，非旧三组产物）：

| 任务 | 本目录文件 | 实测归档记录的 SHA256 | 核验 |
| --- | --- | --- | --- |
| T0001 | T0001_WRD_output.html | `5bcc16ee60bb4732cd9de7abb2e164cbac7d0fe11e8cc2263a589537b336a121` | ✅ 一致 |
| T0081 | T0081_WRD_output.html | `ec35dedd8d0e43d0b755d63a253db4d7b48118df41798338436473669f19b789` | ✅ 一致 |
| T0082 | T0082_WRD_output.html | `9c0c91798df5c2536574415e8955b7899588fe3ef22cf147008fc904b94561c3` | ✅ 一致 |
| T0232 | T0232_WRD_output.html | `3641409a2302db25f93c5b6f229db49ecf4e25d256054283cb8a265a45c588fc` | ✅ 一致 |

实测来源归档：`eval250_T0001/T0081/T0082/T0232_review_20261023.tar.xz`（本目录各 tar.xz，含同批 autoskill / no_skill / trace2skill 三臂完整观测）。

## 目录内新增的对应实测

`observations/` 下为各任务 **trace2skill（WRD）臂的实测观测**（从总归档提取）：

- `T0001__trace2skill_verified/` — 桌面/平板视图、键盘菜单焦点与激活、登录入口等截图与事件
- `T0081__trace2skill_verified/` — 桌面/平板、键盘焦点等
- `T0082__trace2skill_run/` — 状态页、busy 重试、下载结果等
- `T0232__trace2skill_run/` — 从有效样例开始的边界校验全序列（详见 `T0232_boundary_evidence/边界校验证据汇总.md`）

每个目录含 `*.png`（截图）、`*.json`（DOM/事件状态）、`actions.jsonl`（操作序列）、`events.json`。

## 溯源说明

- WRD 输出源路径：`output/20261015_eval250_three_baselines_v2/attempts/T0001__trace2skill/workspace/outputs/`、`output/20261015_transport_recovery_round2/.../T0081|T0082__trace2skill.../outputs/`、`output/20261016_eval_r3b/execution/attempts/T0232_TS_f1/workspace/outputs/`
- 归档内另存有实测字节副本 `original_copies/artifacts/<candidate>/outputs/`，与上述源文件一致。
- `*_页面说明.md` / `使用说明.md` 为各臂随附说明文档，不属于浏览器实测对象（归档 observation 已注明）。
