# 148固定零售工具边界核对

日期：2026-10-04。只读来源核对，无模型调用、服务操作或实验修改。

本轮已成功读取官方固定提交 `fc0055dc4e0a316c3f83133267fbd6faaa770992` 的[Retail工具源码](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/domains/retail/tools.py)，核对带`@is_tool`的方法；与本地准备期[source_audit.md](../../experiments/148_tau2_retail_autoskill/source_audit.md:20)清单一致。

| 工具类别 | 固定官方注册方法 |
|---|---|
| 查询，7项 | find_user_id_by_name_zip、find_user_id_by_email、get_order_details、get_product_details、get_item_details、get_user_details、list_all_product_types |
| 修改，7项 | cancel_pending_order、exchange_delivered_order_items、return_delivered_order_items、modify_pending_order_items、modify_pending_order_address、modify_user_address、modify_pending_order_payment |
| 通用，2项 | calculate、transfer_to_human_agents |

没有创建新订单、撤销取消或`update_order_address`方法。源码中的取消只允许pending，修改地址区分订单地址与用户默认地址；不能互相当成同一对象的fallback。固定源码第363—372行也确认`list_all_product_types`返回品类名→product_id映射，**不是品类数量统计**，不能把技能中使用该映射判为错误。

从v4结果保存的政策抽出的[本地政策副本](recorded_retail_policy.md:3)列明取消／修改pending订单、退换delivered订单、改用户默认地址和查询；其第14行同时限定每会话只能服务同一用户但允许多个请求。

资格：当前v4结果的`environment_info.tool_defs`未保存完整注册表，原运行vendor／session副本缺失。本轮核验的是固定上游工具表、准备期清单和保存政策的一致性；未独立证明历史服务实际暴露的schema字节。该限制不影响“来源没有对应成功写入”的消息证据，但应在正式复现时补运行时工具表hash。
