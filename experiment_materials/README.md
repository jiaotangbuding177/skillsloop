# Eval250 实验原材料

本目录包含用于实验验证的原始材料和实测证据。

## 更正记录（2026-11-02 第二版）

1. **WRD 最终输出**：新增 `WRD_web_tasks/T0*_WRD_output.*` 四份文件，SHA256 与 2026-10-23 实测归档记录一致（见 `WRD_web_tasks/WRD输出与实测对应说明.md`），并非输入的"原首页.html"或旧产物；并提取了各任务 trace2skill 臂的对应实测观测（`WRD_web_tasks/observations/`）。
2. **T0136 八人版 Word**：新增 `Trace2Skills_T0136/八人版_H801-H808/`（三份八人版 docx + 两份 xlsx + H805–H808 履历 + SHA256 校验表）。注意：第一版交付的三份 docx 为四人版（仅 H801–H804），请以八人版为准。
3. **T0232 边界校验**：新增 `WRD_web_tasks/T0232_boundary_evidence/`（校验提示文本 + 每步导出磁盘核查结果）。**已知缺口**：现有实测记录没有"日期改坏"边界组，详见该目录汇总文档。

## 目录结构

### WRD_web_tasks/
WRD 网页任务的完整归档和原始输入文件。

- **eval250_T0001_review_20261023.tar.xz** - T0001 完整浏览器会话观测（键盘焦点、菜单激活等）
- **eval250_T0081_review_20261023.tar.xz** - T0081 完整浏览器会话观测（submenu focus、SVG重查等）
- **eval250_T0082_review_20261023.tar.xz** - T0082 完整浏览器会话观测（状态检查、busy重试、下载验证等）
- **eval250_T0232_review_20261023.tar.xz** - T0232 完整浏览器会话观测（联系人、日期、空报价边界校验）
- **T0001_inputs/** - T0001 原始输入（原首页.html、logo.svg、交互约定.md、品牌与需求.md、样例数据.json）
- **T0081_inputs/** - T0081 原始输入
- **T0082_inputs/** - T0082 原始输入（lab_environment.json、syllabus.md）
- **T0232_inputs/** - T0232 原始输入（业务规则.md、产品目录.csv、字段契约.json、客户样例.json）

### Trace2Skills_T0136/
T0136《临床项目经理证据审查》任务的输入和输出。

**输入文件：**
- H801履历.pdf ~ H804履历.pdf（4份候选人履历）
- 岗位要求.md（岗位JD）

**输出文件（三个臂）：**
- T0136_autoskill_临床项目经理证据审查.docx - autoskill 臂输出
- T0136_noskill_临床项目经理证据审查.docx - no_skill 臂输出
- T0136_trace2skill_临床项目经理证据审查.docx - trace2skill 臂输出（来自 eval_r3b）

### web24_addendum/
网页实测补充证据包。

- **eval250_web24_addendum_login_scroll_dimensions_20261023.zip** - 登录页面滚动尺寸技术发现
  - A组：登录对话框观测（4步截图 + actions.jsonl）
  - B组：空表单提交观测（6步截图）
  - C组：滚动维度观测（多步滚动截图）
- **eval250_web24_reports_and_checksums_20261023.zip** - 报告和校验和

## 实测证据说明

每个 tar.xz 归档包含：
- `observations/` - 浏览器会话观测数据
  - `*.png` - 截图证据
  - `*.json` - 事件记录、DOM状态
  - `actions.jsonl` - 操作序列
- `final/` - 汇总报告
  - `summary.json` - 任务摘要
  - `T0XXX_observations_final.md` - 最终观测报告
  - `coverage_matrix.json` - 覆盖矩阵

## 来源

- 归档文件：`handoff/20261021_eval250_q_scoring/web24_delivery/`
- T0136 输入：`output/20261013_eval250_review/qa/final_episodes/T0136/workspace/inputs/`
- T0136 输出：`output/20261015_transport_recovery_round2/` 和 `output/20261016_eval_r3b/`
- 原始输入：`output/20261013_eval250_review/qa/final_episodes/T0001|T0081|T0082|T0232/workspace/inputs/`

## 创建日期

2026-11-01
