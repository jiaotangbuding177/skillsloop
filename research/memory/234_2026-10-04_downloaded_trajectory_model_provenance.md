# 第234轮：下载实样并核对轨迹模型、环境与增强阶段

## 用户已确认要求

实际下载轨迹、逐点查看、明确生成模型与agent环境，回答当前公开轨迹属于额外训练增强前还是之后。仅本项公开下载/分析授权，不扩展为批量实验或微调。

## 证据支持的观察

完整报告见[234](../reports/234_trajectory_download_and_provenance.md)，实际下载/审计文件位于`research/reports/233_trajectory_audit/`（下载时233编号，随后并发巡检已占用233，本报告采用234，不覆盖巡检）。

- RW HF固定revision完整93,739项文件清单扫描及官方网页公开数据未发现完整rollout下载。修正可能混淆：运行框架记录轨迹不等于发布了可下载的论文训练/评测轨迹。
- 新取得ProCUA样本0028完整20,127字节JSON及8张1920×1080截图，逐张核对8动作：滚动、点击、全选、替换activeEditorLong、Enter、滚动、done。采集教师Kimi-K2.5由官方卡说明，样本pipeline=kimi；Ubuntu VM、OSWorld初始化、PyAutoGUI。是学生SFT之前的教师数据，不是增强后的学生rollout；无checkpoint hash不能称裸base。
- 样本无独立评分，done是agent声明；goal改标题，继承setup/evaluator却是创建test.py，不能混用验证。初态已在设置页，未打开实际文件展示路径，观察仅支持设置改变。
- AgentNet既有样本人工演示+合成标注，7步、task_completed=false；非某模型增强前后。
- 本地RW基线205记录、91tool_use条目；Claude Code2.1.177/Playwright MCP/官方Web容器。claude-opus-4-8为兼容别名，账本012255实际请求/响应GLM-5.3-Flash，无本项目SFT/skills。原程序分0、VLMnull、score_passed=false保持，进程pass不当成功。
- 论文RW教师Qwen3.8-Max生成训练轨迹后35,000条SFT两学生；只文献证据，未取得原轨迹。

## 研究假设、建议与未知

外部教师GUI轨迹可作技能来源，但对RW复刻迁移未知；不属于RW官方训练/测试配对。精确教师checkpoint、采集harness版本、RW官方训练包入口未取得。一条实样不能代表全库质量。建议保持模型基线、独立训练来源、库冻结与held-out评分边界。

## 范围与现状

仅公开下载/只读分析和记忆；未改运行中的208/115、分集、提示词、库、评分，未调用暂缓Voyage/Tavily，未启动评测。当前运行状态沿用233巡检，不把本次数据分析当健康巡检。
