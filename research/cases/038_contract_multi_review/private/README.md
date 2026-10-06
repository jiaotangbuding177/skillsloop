# 本地原文证据

本目录由 `../prepare_case.py` 从两份用户提供的导出中抽取。`eligible_contract_user_messages.jsonl` 是P0-1关键词桶剔除技能请求整会话后的227条原始用户消息；它们尚未逐条确认为独立任务。`raw_messages.jsonl` 保留所选三个会话的旧包原始导出行；`user_messages_with_dates.jsonl` 保留对应用户消息与日期；`demo_generation_import.jsonl` 是针对 demo 接口的转换视图。`demo_generation_import_compat.jsonl` 为诊断当前规则识别问题，在委托方任务的首句前额外加一个“请”；它**不是原文**，只能用于接口预检，不能充当原始数据或算法结果。上述文件含企业会话正文，限本地研究使用，不加入公开论文附件或向外部模型批量发送。原DOCX附件与历史输出文件不在导出包中。
