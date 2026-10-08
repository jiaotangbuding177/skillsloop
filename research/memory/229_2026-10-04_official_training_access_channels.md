# 第229轮：官方训练任务公开渠道核查

## 用户要求

调研RecreationWorld官方训练任务获取渠道。本轮只读调研与记录，不发送邮件/Issue，不下载全量、不改分集、不启动实验。

## 证据支持的观察

[详细核查及询问信草稿](../reports/229_recreationworld_training_access.md)。论文训练池来自GitHub应用，35,000是筛选轨迹数，不是应用数；公开资源表未列训练池。HF所有配置test/250，Qwen作者Recreation关键词API仅返回RecreationBench，metadata仅五平台；ModelScope只读API成功返回同五平台+metadata+两文件，TotalCount8。GitHub发布页无release附件，官方站/README均无独立train入口。当前未找到官方训练任务池/35,000轨迹的公开下载渠道，不能断言私有或其他作者账号完全不存在。

## 获取建议与未知

官方联系邮箱xiezhihui.xzh@alibaba-inc.com、gaochang.gao@alibaba-inc.com；建议询问发布计划或研究访问，优先任务清单/repo/commit、参考包、prompt、patch/fixture、环境与验证器、去重映射和许可；原35,000轨迹是可选项。草稿已保存但未发送。能否提供、何时发布、部分平台是否可用均未知。

## 更正与下一步

228路线方法上可取但官方train资源尚未落实，不能声称现成可直接执行。运行框架能生成轨迹不代表自带论文训练池；评测reference不是训练包。若拿不到，新增应用或250派生分集必须明确另立协议。208/218实验未干预。本轮无新增实验实证发现。
