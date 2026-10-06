# 2026-10-05：算法上传GitHub与原链路复用清单

## 用户确认

用户明确要求将算法更新上传GitHub，并列出用到的原链路文件。授权本次限定提交和推送；没有要求合并main、创建PR、运行新模型或benchmark。

## 已完成与来源

- 仓库：`https://github.com/jiaotangbuding177/skillsloop`。
- 分支：`codex/direct-trace-skill-pipeline`。
- 提交：`6286e0fd3f3c5e0ea602bc8705991bb046d6eacd`。
- `git push -u origin codex/direct-trace-skill-pipeline`成功，后续`git ls-remote`返回与本地HEAD完全相同的完整提交号。
- 本次80文件，包含新算法、此前未跟踪的必要skilldemo包、测试、两个安装脚本、构造E/C/V样例、直接管道文档及实现报告／记忆。不打包企业生产源码、私有原会话、模型请求产物、密钥或第三方运行时。提交前对暂存文本做凭据模式检查，没有命中；`git diff --cached --check`通过。
- 原工作区其他未提交研究／工程成果保留，不通过整仓add或覆盖提交混入本轮。README／STATE等已有多轮未提交汇总继续本地保留。
- 早期HTTPS／代理TLS握手失败和直连超时；最终标准HTTPS push成功，未关闭证书验证。凭据helper产生警告但推送及远端核验成功。

## 原链路文件说明

[完整源码与依赖清单](../../enginering/demo/DIRECT_PIPELINE_SOURCE_MAP.md)已经同提交上传。原链路指此前独立Demo，不是InsightWeaver服务。

- 原输入／请求：`pipeline.py`、`intake.py`、`evidence.py`。
- 原关系恢复：`relational.py`、`pair_detection.py`、`recovery.py`及辅助`detection.py`。
- 模型及配置：`runtime.py`、`live.py`；runtime本轮扩展两个用途。
- 官方封装：`bootstrap.py`、`creator.py`与本机OpenClaw官方skill-creator脚本；第三方脚本通过固定版安装器获取，不进Git。
- 原聚合模块`workflow.py`／`relational_workflow.py`／`workflow_index.py`作为包依赖和legacy保留，新默认聚合执行器为`workflow_induction.py`。

## 研究证据与边界

本轮无新增实证发现，仅上传和源码依赖核对；算法源码未修改，沿用上一轮416检查及有限真实生成验收，不重复运行付费模型。不将Git上传当成新的语义、下游得分或成本证据。
