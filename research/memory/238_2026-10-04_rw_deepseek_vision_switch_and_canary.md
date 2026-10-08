# 第238轮：用户切换RW模型，独立新版本实际启动

## 用户确认

用户指定claudex.org/v1及deepseek-v4-flash-vision-exp，提供密钥，要求模型切换并询问240秒是否太短。仅RW模型/传输切换，不替换Co-Gym/AutoSkill学习中的GLM。凭据只写238/private/provider.json，Windows ACL限制执行账户与SYSTEM，git全局private忽略；内容不写记忆/报告。

## 证据与判断

- 旧请求012259已证实240秒absolute截止触发，与正常结束同时间；不能仅提高时间而忽略响应错误传播。旧218源码/freeze、GLM失败轨迹及0分保持。
- 新238/model_resource.json与reports/phase_manifest.json冻结独立rw_web_deepseek_vision_v1。provider总截止取消，socket idle及官方协议代理等待1800秒；保持原官方agent/harness/数据/评分逻辑，不声称所有层完全无限等待。
- 直接API两张随机六字符图片均识别正确，tool_choice report_status参数正确。第一次标准JSON读取失败因服务{data,success}包装，失败验收文件全部保留，明确解包后通过，不伪造成功。请求模型是指定别名，provider自报deepseek/deepseek-v4.1-flash；实际checkpoint/内部视觉路由不可验证。
- 独立Windows8158 relay使用受控凭据；完整非流式上游结果验证后转标准SSE，错误/空choices/finish缺失/length拒绝502，4个确定性异常案例验收，真实SSE/DONE测试通过。不更改模型文本或原生agent算法，不保留完整模型payload。
- 仍可能有SDK内部等待限制，1800秒idle不是已经证实能处理任意时长；buffer完整响应保证不先泄露半条成功流，token usage原样进独立账本。078共享旧账本不改/不重置，新供应商费用独立登记，不混入旧GLM曲线。
- 真正运行：238/runs/recreation_eval_baseline_1791051558705758062，corravale.example基线canary（从正式结果排除），controller Linux PID1490、relay Windows PID15416、pipeline_status running。复用官方镜像skillloop-rw-web:218-v2、同官方固定数据与源码；原218.check先通过，新脚本锁和STOP门禁。官方ClaudeCode2.1.177/Playwright进入；账本1791051576468852600及1791051579328858400同route完整tool_calls，2.439/7.890秒。
- VLM judge仍禁用，单题生成与评分canary会后续收尾；不把当前运行称成功交付，不声称原生CLI视觉已完全验收或250完成。根pipeline状态只在所有API完整时标native_finished，formal_baseline_accepted仍false待产物验收，存在不完整请求标transport_failure。

## 范围、验收与下一步

本轮实际配置、API验收、单题启动，不只提出建议。当前尚在运行，无分数/交付完成结论。保留服务与安全账本，后续检查官方交付与所有API完成，不能把旧失败覆盖成新模型结果。没有250批量、没有借用Co-Gym库、没有Voyage/Tavily调用或变更旧208/115/196配置。当前208健康沿用234巡检，非本轮实测。

原canary最后响应完整性问题与模型是否“不会写”分开：长请求超过240是具体故障；任务复杂使其超时是解释假设，不由日志证明。新模型变更会改变实验处理，必须单列，不能称同模型公平补测。
