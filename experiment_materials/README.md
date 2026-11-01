# Eval250 实验原材料

本目录包含用于实验验证的原始材料和实测证据。

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
