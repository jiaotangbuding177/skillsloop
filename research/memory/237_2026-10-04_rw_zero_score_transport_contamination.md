# 第237轮：更正RW canary完成表述，末请求传输失败污染

用户质疑程序0/VLMnull是否基础设施错误。先读README/CHARTER/STATE，实际核验218 run controller.log、score_report/test_details、src/App.tsx、output/index.html、agent_dom/homepage、JSONL后40记录和共享账本012259。

## 证据与更正

- controller.log22/41/120-121明确VLM judge disabled/enabled=false，vlm_score=null为配置未运行，不是VLM失败。此前“未完成”应精确改为“未启用”；SSIM替代路径执行，不能称官方VLM完整评分。
- 功能229项全部失败，输出DOM为Ready to build/default Arena Web Dev App，src/App.tsx同默认模板；agent只更新CSS/main入口、下载素材，末JSONL205 native result subtype success/is_error=false文本却说现在开始写应用，未真实交付复刻。
- 同run账本012259明确13:39:59.592开始，elapsed240.011、Absolute upstream response deadline reached、upstream_transport_error、response_complete=false。末agent结束13:43:59、native controller13:44:00收尾，时间一致支持请求中断与过早结束相关，但本轮未完整审计代理错误转换代码，不能断言其具体机制。
- 这是明确的基础设施传输故障，native正常exit/结果文件不证明全链路完整。此前234/235“完整结束单题”仅进程收尾，不应当作无故障完整任务轨迹/有效能力基线。本轮显式更正保留历史。
- 根metrics的program_score0也是提取的final_score；原始评分final=功能50%+视觉SSIM50%，不可将该别名混为纯程序评分或论文双通道分。功能单独确为0/229，评分服务status success、eval_error null、build成功，0反映被测默认交付，但生成阶段被基础设施截断，不能归因模型能力。

## 行动、建议与未知

原run/0分/失败/库不改不覆盖，当前将此run标为传输故障污染、完整任务完成验收不通过。下一步独立版本修复错误传递/完成验收及请求截止配置（不可热改旧run），验收后新的canary保留归属；尚未实施或重跑，本轮没有完成恢复主张。用户本问诊断，不擅自开启250批量。

本轮本地WSL读取普通权限E_ACCESSDENIED未视为模型故障；改以Windows结构化只读JSON解析完成证据核验。没有输出模型reasoning或凭据。208健康仍沿用234，未干预另一实验。
