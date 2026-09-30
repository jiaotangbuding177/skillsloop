# 项目级科研工作约定

本项目默认且持续处于**科研模式**。用户在 2026-09-18 明确：目标是基于已有系统，研究企业会话驱动的 skills 发现、生成、入库、复用与持续演化闭环，对标 The Web Conference（WWW）Industry Track 论文。

## 必须先读

每次开始或接续本项目工作，先读取 `research/README.md`、`research/CHARTER.md`、`research/STATE.md`，再按记忆索引读取相关轮次记录。不得只凭聊天上下文或旧摘要判断现状。

## 科研模式与范围

- 除非用户显式要求进行开发，否则禁用开发相关 skills 链路和开发规则，包括开发路由、feature/bugfix/refactor/TDD、Trellis 开发工作流，以及自动触发的开发审查、测试、提交等流程。
- 用户明确授权某项开发时，授权仅适用于该项工作，不默认永久切换模式；研究主线和记忆规范持续有效。
- 按实际研究任务采用科研相关 skills。通用技能中的旧项目目标、SOTA 要求或单一生成侧范围，不得覆盖本项目章程。
- 默认可以开展用户请求范围内的科研讨论、资料分析和 Markdown 记录；本次立项不授权实验执行、系统代码修改、部署或数据接入。
- 研究完整企业闭环。检索、选用、组织共享和使用后演化均可构成研究对象，但每项工作必须说明其与主线和可验证研究问题的关系。
- 不把系统功能完整等同于论文贡献，不预设创新成立、效果提升或达到投稿要求。

## 每轮记忆

- 每一轮有实质研究内容的对话或工作，结束前都必须在 `research/memory/` 保存 Markdown 记录，并更新 `research/README.md` 的索引和 `research/STATE.md` 的当前状态。
- 洞察、发现、用户约束、决策、被否定的路线、负结果与未解决问题都必须记录；没有新发现时明确写“本轮无新增实证发现”。
- 分开标注用户已确认要求、证据支持的观察、研究假设、工作建议与未知项。讨论或直觉不能升级为实证结论。
- 记录结论的来源或产物路径、适用范围及下一步。无证据时明确标注；不编造实验、引用或系统现状。
- 历史记录保留。修正结论时新增更正并链接旧记录，同时更新当前状态，不能静默抹去负结果或旧决策。
- 不把敏感企业会话或凭据直接复制进研究记忆；使用必要的去标识摘要和受控来源引用。

## Local file inspection

Prefer FastCtx `inspect_local_file`, `grep`, and `glob` for reading, searching, and finding local files. Use plain absolute filesystem paths, including for URI-shaped references. Read only what the task needs; batch related text reads using `files`. Follow exact continuation parameters only when a result is Partial.

Use FastCtx `replace` for mechanical find-and-replace. Use `apply_patch` for generated content, semantic rewrites, or small local edits.
