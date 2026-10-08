# 第235轮：35,000训练轨迹、250评测任务与本地单题区分

用户追问是否已下载35,000条、benchmark是否35,000题、本地GLM是否已完整跑完。

证据：先读README/CHARTER/STATE及234实样报告；再次枚举218/runs的metrics/trajectory文件并读取正式canary metrics。论文§3.1与结论公开250 applications说明沿用官方来源 https://arxiv.org/html/2609.22000v1 。

- 35,000是论文筛选用于SFT的训练轨迹，不是RecreationBench评测题数，也不能直接推为35,000个不同问题。评测250应用任务，五平台各50。
- 未下载官方35,000轨迹；234下载的是官方93,739项文件清单，不是93,739轨迹或所有资产。ProCUA实际单条完整JSON+8截图，AgentNet既有单条示例，均非RW35,000训练包。
- 218本地确有GLM-5.3-Flash完成运行的单题corravale.example轨迹，run recreation_eval_baseline_1791032747410611525，205条JSONL为一条任务轨迹内部记录，不是205题；root/recreation两份trajectory路径不当两题。
- metrics明确recreation/eval completed、result_complete=true，但program_score0、VLMnull、score_passed=false。属于过程结束，不是任务成功，也不是250题完整跑完；其他setup/eval尝试不混计完整任务轨迹。
- 旧Co-Gym的212采集与RW250独立，不混计。

本轮是概念及文件范围核验，无新增实验效果证据，未启动批量、未改分集/库/评分，运行健康沿用234巡检。建议后续讨论以“已下载轨迹数／已执行任务数／评分完成范围”分别表述。
