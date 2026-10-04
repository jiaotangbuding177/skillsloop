# 阻塞项（集中询问）

截至 2026-10-02：模型资源与 embeddings 均已配好并探测通过；仍待确认 **预算硬上限 / dev 联调许可**。

## 1. 模型资源（已更新，2026-10-02）

用户已提供本实验专用资源：**GLM-4-Flash** @ `https://open.bigmodel.cn/api/paas/v4`（账号标注：吴天辰）。
凭据存于仓库外受控文件 `C:/Users/22142/.skillsloop148/upstream_connection.json`（不入库、不入账本、不打印）。
探测（1 次成功请求）确认**原生工具调用可用**（`finish_reason=tool_calls`）。

| 角色 | 现状 |
| --- | --- |
| Consumer / Collector | ✅ glm-4-flash（经实验中继；B0/B1 完全相同） |
| User Simulator | ✅ glm-4-flash（记录为适配；官方推荐 gpt-4o，报告单列） |
| AutoSkill LLM（提取/维护） | ✅ glm-4-flash |
| NL 断言判分（judge） | ✅ glm-4-flash（诊断用途，报告单列） |
| AutoSkill Embeddings | ✅ `ecnu-embedding-small` @ `https://chat.ecnu.edu.cn/open/api/v1`（dim 1024；凭据仓库外；探测通过） |

注意：GLM-4-Flash 比本项目既往 GLM-5.3-Flash 弱，成绩不与其它配置跨比（协议已记录）。

## 2. 预算与硬上限

- 规模：70 条演化采集 + 320 次配对评测（40 题 × 2 组 × 4 trials）+ AutoSkill 提取/维护与 embedding + NL 判分。
- 粗估：约 1.3 万–1.6 万次模型请求（每场模拟 ≈ 25–35 次请求；样本小、模型多轮，波动大）。
- 请求上限不改 token/费用口径；若需要费用上限，请给口径（每请求均费或总金额）。
- 建议：`请求硬上限 20,000`、无墙钟截止、分阶段推进（阶段上限：dev ≤ 300；采集 ≤ 4,000；评测 ≤ 14,000；AutoSkill/判分 ≤ 2,000）；触顶保留断点，费用未知不填 0。
- **dev 真实联调是否现在即可跑？**（4 题、预计 ≤ 300 请求，用已批准 GLM 端点）

## 3. 数据/版本决策（已按你的要求固定，如要变更请明说）

- 固定 τ²-bench **v1.0.1**（τ³ 时代、含 Task Quality 修订；零售文本数据与 main 一致）。若你要 τ² 论文时代的旧数据（v0.2.0，无 train/test split 文件），请在开工前提出——切换会影响与旧论文的可比性、以及 74/40 划分的可用性。
- 模拟器/判分用 GLM 属适配；成绩不与不同配置直接排名。

## 非阻塞（我方继续）

- 单测通过后继续：skills 接线、canonicalize（A/B/C 隔离）、预算中继账本、进度页与巡检。
