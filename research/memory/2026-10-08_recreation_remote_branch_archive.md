# Recreation相关实验、进度与记忆独立远端归档

## 用户已确认要求

2026-10-08用户要求把Recreation相关实验和进度上传远端新分支，独立上传相关记忆和内容。本项授权建立并推送归档分支，不恢复2026-10-05已停止的模型、采集、参考准备或监控任务，不更改其他研究实验。

## 归档方案与适用范围

先读取研究README/CHARTER/STATE及299停止记录。当前主工作区在main且存在其他研究未提交内容，采用独立临时Git仓库与无父提交的Recreation专用分支`codex/recreation-research-20261008`，目标原origin `https://github.com/jiaotangbuding177/skillsloop.git`，不切换或提交主工作区其他内容。

仅归档Recreation相关memory、reports、protocols、实验目录及停止的monitoring/recreationbench；早期尝试、失败/负结果、固定来源注册、输入合同、脚本、评分、自有交付与轨迹保持。共享README/STATE/CHARTER仅生成Recreation专用摘要，原混合项目文档不整份上传。

凭据/private资源配置不上传；安全STOP与canonical预算显式保留。运行依赖、缓存、公开源码大镜像及不透明压缩工作区/冻结ZIP不上传，保留URL/commit/原SHA、清单与省略项。上传副本的凭据匹配脱敏，源文件不改，PUBLICATION_MANIFEST分别保存source/published SHA与脱敏数量；脱敏导出不能冒称原freeze字节一致或正式AutoSkill学习输入已验收。

## 当前进度与限制

截至准备阶段仍为用户停止：26应用pilot仅2/26准入、两应用各3轮共6执行结束、成功0；miniPaint末分0.4228、Squoosh0.5246，Vite参考构建成功但GUI/verifier未准入。RW skills学习/250评测未开始，旧corravale STOP及暴露保留。

本轮无新增效果实证发现。远端创建/推送与SHA验证结果将在完成后追加；在验证前不宣称归档已上传。打包入口位于本地tmp/recreation-publish-20261008，不属于实验执行或业务代码改动。

## 完成结果与证据（追加，保留前述准备阶段）

远端新分支已实际创建并首次推送成功：[codex/recreation-research-20261008](https://github.com/jiaotangbuding177/skillsloop/tree/codex/recreation-research-20261008)。首次归档提交`52049afed438432e74300ef0223ca79931129c8f`与`git ls-remote --heads`一致；根提交无父历史，仅Recreation归档，不携带完整业务仓库或其他研究提交。完成回执随后另作小提交同步本段结果。

归档26个实验目录、36份相关记忆，初始manifest 19,050文件、4,978,378,430字节（包含重复来源路径，Git内容去重压缩包约1.02GiB）；另有8个专用入口/元数据文件。14文件的保守凭据模式匹配项在导出副本中脱敏，122个运行/不透明归档文件省略，公共大源码镜像与运行依赖目录另列省略规则。原始本地实验文件未改；未提交main上的其他研究改动。

独立验收：全部19,050导出文件SHA/大小匹配、残留凭据匹配0、脱敏引入JSON/JSONL错误0、意外文件0；Git暂存19,058文件，逐一核验manifest文件的实际Git blob字节与导出副本相同。首次Windows长路径限制已在隔离归档仓库开启core.longpaths解决；嵌套原gitignore忽略了部分已审计文件，在归档仓库范围显式补暂存后完整通过。WSL导出I/O过慢的本轮工具已精确停止并改Windows原生工具，不是实验重启。

远端[PUBLICATION_MANIFEST.json](https://github.com/jiaotangbuding177/skillsloop/blob/codex/recreation-research-20261008/PUBLICATION_MANIFEST.json)明确source/published SHA、脱敏和省略项；[PUBLICATION_VERIFICATION.json](https://github.com/jiaotangbuding177/skillsloop/blob/codex/recreation-research-20261008/PUBLICATION_VERIFICATION.json)保存检查结果。回执保存在[本地报告](../reports/2026-10-08_recreation_remote_archive_receipt.json)。凭据/private provider配置未上传，安全STOP和canonical预算保留。

上传授权只用于归档，监控/进程与实验仍保持用户停止；无新增模型、采集、学习或评分。归档不等于26应用采集完成、AutoSkill输入验收或技能收益成立。完整论文训练数据仍未取得，旧失败/暴露/预算约束保留。
