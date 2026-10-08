# RW 演化轨迹接续采集

**当前用户停止（2026-10-05第299轮）：** 监控任务及RW相关专用进程/参考容器已停止；本目录及旧285/288的private/STOP生效，不自动恢复或启动后续参考/采集。原始轨迹、评分、freeze、日志及参考构建产物保留。[停止记录](../../memory/299_2026-10-05_rw_user_stop_monitor_and_processes.md)。

日期：2026-10-05。本目录在恢复工作时准备，研究记忆编号为294。旧285/288产物和freeze保持。

用户要求继续生成轨迹，并明确允许将Squoosh自己的既有会话、候选代码和公开参考截图发送至原指定 `https://claudex.org/v1` / `deepseek-v4-flash-vision-exp`。本批仍是26独立应用pilot，不自动开始skills学习或250评测。

## 当前状态（第295轮核对）

Squoosh第2、3轮均已结束，功能1/6、SSIM0.8826、最终0.5246，与首轮相同；三轮预算耗尽，监督器及observer已退出，不再启动第四轮。[终态实核](reports/295_terminal_progress_audit.json)：新增两轮raw各5文件SHA/大小/JSONL通过，67/69冻结文件变化0，169/94独立API全完成，无新OOM。原始数据存储验收不等于完整canonical/原创性或学习输入已通过。

Vite docs v2已构建成功（327文件、rc0、model_calls0），GUI/重置/独立verifier及负对照准入仍待完成，runtime_accepted=false。仍2/26应用准入、两应用各3轮已结束、成功0；RW生成当前未运行，skills学习/250正式评测未启动。新增Squoosh两轮尚未并入下面的旧公开导出。[第295轮记忆](../../memory/295_2026-10-05_rw_terminal_progress_and_vite_reference.md)。

## 第294轮启动时的执行截面（历史）

- Squoosh第2轮已启动：`squoosh_recreation_eval_1791158578555081942`，首轮session `040fcf5e-ec60-4923-95cb-41e85236ebad`、自己的代码与真实失败反馈接续。
- 官方vendor与训练reference/verifier不变；新轮固定3GiB/2CPU，代理8793，经既有8193 relay独立 `/293/<attempt>/` 路由记账。
- supervisor仅允许第2轮、必要时最后第3轮。满足功能6/6与SSIM>=0.85时停止并待最终审计；终态失败/评分缺失不自动重跑。每轮首agent前另冻结，跨版本预算不重置。
- miniPaint已3/3耗尽，旧corravale保持STOP。其余24未准入，不能称全部26正在执行。
- Vite docs下一项参考构建要求可用内存>=6GiB；首准备版已在准入后因pnpm可执行shim缺失退出，日志/状态保留。新v2显式激活shim，当前再次等待资源。固定原来源commit，只构建研究者侧参考，不调用agent/模型/评分，构建成功后仍须GUI/独立verifier准入。

## 读取状态

- [当前实际健康](reports/current_health.json)：真实controller、容器、原生session增长、源码mtime和独立API回执；原生会话统计包含继承历史，不是全部新增事件。
- [当前actor](reports/active/squoosh.json)、[监督器身份](reports/supervisor_identity.json)：接续终态/等待另存于`reports/continuation_status.json`，仅在相应等待/终态时生成；运行中优先读当前actor与实际健康。
- [第2轮freeze](reports/freeze_squoosh_round2.json)、[检查点准入](reports/checkpoint_round2_admission.json)、[离线恢复验收](reports/checkpoint_offline_admission.json)。
- [Vite参考准备v2](admission/vite_docs_v2/preparation_status.json)、[首版失败](admission/vite_docs/preparation_status.json)。

最初监督器的已加载观察代码误用了图像计数字段，`health_state.json`内旧image_transport_blocks=0不可作无图像证据；新独立只读observer读取实际recovered_image_blocks并输出current_health.json，actor/freeze未改。累计请求图像块含历史重复，不当作独立图片数。

## 已有素材机械导出

[导出清单](reports/existing_public_exports.json)：miniPaint三轮去重后1236条公开消息事件、43唯一图片、505调用/505回执；Squoosh首轮851事件、48唯一图片、377调用/377回执。UUID冲突、未匹配调用/孤立回执均0。导出包括逐轮来源hash、图片hash、机械文本视图；没有LLM摘要、没有伪造success或将末轮裁判结果伪装为actor回执。

这是本地机械整理，不代表完整canonical因果/原创性审计已通过或AutoSkill完整读到输入；现有text-only学习器不会因图片路径存在而看到像素。新第2轮运行中不并入已完成导出。完整原始私有session、官方分数和设施失败继续保留。

接续研究入口：[第294轮记忆](../../memory/294_2026-10-05_rw_squoosh_continuation_authorized.md)。
