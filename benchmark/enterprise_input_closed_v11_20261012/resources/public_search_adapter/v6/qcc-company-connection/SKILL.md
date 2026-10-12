---
name: qcc-company-connection
description: 使用公开网络来源核查公司，真实检索并逐字段保留出处；本实验按用户要求不调用企查查付费接口。
---

# 公开公司资料核查

用户已指定本实验用公开网络搜索完成公司核查，无需企查查凭据。保留原技能名供任务发现，实际资源条件是public_search，不能将查不到的字段写成无风险或将旧AI业务答复复用为事实。

首先以用户公司全称实际检索：

```bash
python /workspace/skills/qcc-company-connection/scripts/public_company_search.py --company "用户给出的公司全称" --output /workspace/outputs/公司公开检索.json
```

该命令使用已配好的匿名公开Search MCP，保留搜索结果、真实查询时间及公司全称匹配候选。它不会认证结果事实；对候选继续用原生web_search、browser或HTTP读取工商登记机关、公司官网、法院、监管与交易所披露。逐项确认同一法律主体，记录URL和原文位置，再填写 company_check.py 所需证据JSON；公开模式用public_evidence。证据要支持公司全称及所填字段，避免把同名/近似名/集团资料混入。

注册资本、股权、法人、关联企业、处罚、诉讼、财务分别记录实际覆盖及未知项。搜索接口返回结果不等于已查到目标公司；exact_name_result_candidates为空时继续换关键词/核对名称，并如实说明未取得公司准确匹配公开证据，不编造数据、结论或把未知当零风险。形成报告时根据本次实际证据作答，不要求结论与历史AI一致。
