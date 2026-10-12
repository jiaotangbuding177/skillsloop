---
name: human-resources-compliance
description: Use this skill for HR policy compliance, policy audits, compliance status checks, violation review, and evidence-based policy reporting.
---

# human_resources.enforce_compliance_with_policies.skill

## Purpose

Compiled agent skill for enforce_compliance_with_policies in domain human_resources.

## Invocation Contract

Inputs: user_request, policy_name, policy_scope, effective_date, responsible_department, business_context, authorization_context

Outputs: compliance_status, violations, evidence, next_action

## Business Action

- Action id: `BA-A4D271884F`
- Action type: `policy_transformation`
- Intent: ensure compliance with company policies
- Trigger examples: Run audit_policy_adherence for task enforce_compliance_with_policies.; Transform policy_document into reports.

Required input fields:

- `policy_name`
- `policy_scope`
- `effective_date`
- `responsible_department`

## Business Rule Contract

Must do:

- audit must align with regulatory requirements
- Return evidence atom ids for key conclusions.
- Expose missing inputs and unsupported scope.

Must not:

- Do not invent business facts absent from evidence.
- Do not treat low-confidence synthesis as a deterministic rule.
- Do not expose restricted details when external output is not allowed.

Escalate when:

- `evidence_missing`
- `external_output_requested`
- `misaligned_or_missing_quote`
- `policy_violations`
- `sensitive_data_requested`
- `unapproved_revisions`
- `unsupported_scope`

## Execution Policy

1. Map the user request to the compiled task intent.
2. Select the dynamic cognitive module attached to this Skill.
3. Retrieve and inspect relevant knowledge atoms from the local `evidence_index.json` before answering.
4. Answer only with claims directly supported by approved evidence atoms, and return atom ids for key conclusions.
5. If evidence is missing or review_status is not approved, ask for human confirmation.
6. Follow the governance policy before exposing sensitive information.

## Knowledge Atom Usage Policy

This skill must rely heavily on grounded knowledge atoms from the local `evidence_index.json`.

Rules:

1. Retrieve and inspect all relevant knowledge atoms before producing HR workflow conclusions.
2. Key conclusions, policy judgments, process steps, and risk statements must cite supporting evidence atom ids.
3. Do not produce deterministic HR conclusions when no approved atom supports the claim.
4. Prefer atoms with `review_status: approved`, `quote_traceable: true`, and `claim_supported: true`.
5. If atoms are missing, conflicting, restricted, or not review-approved, expose the uncertainty and ask for human confirmation.
6. Do not use knowledge atoms as decoration; each cited atom must directly support the sentence or recommendation it is attached to.

## Governance

- Data level: `restricted`
- Human approval required: `True`
- External output allowed: `False`
- Evidence policy: `grounded_atoms_only`
- Compile readiness: `ready`
- Readiness blockers: `none`

## Dynamic Cognitive Modules

- `CM-59F1AE17` human_resources.enforce_compliance_with_policies.module: atoms=132, relations=132, coverage=1.0, security=restricted

## Knowledge Atoms

- `KA-0001` policy_document: 员工培训管理规定依据国家及人力资源管理相关法规、政策以及公司组织管理制度制定。
- `KA-0002` policy_document: 本规定适用于公司各部门及下属的全资子公司及关联公司、分支机构及下属所有员工。
- `KA-0033` policy_document: 人力资源部应与员工签订《培训服务期协议》以管控培训服务期。
- `KA-0034` policy_document: 人力资源部应与员工签订《培训服务期协议》以管控培训服务期，适用于培训费用超过3000元/次的培训。
- `KA-0035` policy_document: 人力资源部应与员工签订《培训服务期协议》以管控培训服务期，适用于公司资助的长期业余培训。
- `KA-0036` policy_document: 参加外派培训人员需根据参训费用或时间确定服务期，违反服务期约定主动离职的需承担违约金。
- `KA-0037` policy_document: 员工在合同期内因以下情况导致公司提前与其解除合同的，从劳动关系结束之日前两年中公司为员工投入的培训费用，员工应全额退还公司。
- `KA-0038` policy_document: 员工在合同期内主动离职的，返还的培训费用根据承诺服务协议的月数折算比例为：培训总费用/承诺服务期的月数×未服务约束 =员工返还公司的培训费用。
- `KA-0041` policy_document: 培训设施设备的采购、维护和管理依照“资源共享、充分利用”的原则，根据现有资源情况进行添置。
- `KA-0042` policy_document: 二、培训设施设备的调配权限归属人力资源部，系统运营部负责进行维护和保养
- `KA-0047` policy_document: 二、请假规定 1、特殊情况不能参加培训人员，必须事先得到部门负责人和人力资源部的批准
- `KA-0048` policy_document: 否则，均 作旷工处理
- `KA-0051` policy_document: 在岗培训中未通过考试的视为不能胜任本职工作，公司可以单方面解除劳动合同、安排再次培训或转岗。
- `KA-0052` policy_document: 员工无正当理由缺席公司指定培训的，给予书面警告一次。
- `KA-0053` policy_document: 两次以上拒不接受培训的，视同严重违反公司规章制度。
- `KA-0054` policy_document: 参加培训迟到、早退的，视同上班迟到、早退，按公司《考勤管理规定》执行。
- `KA-0055` policy_document: 未经核准擅自退训的，其培训所发生的费用由其个人承担，缺席时间按旷工处理。
- `KA-0056` policy_document: 公司人力资源部对本规定拥有解释权和修订权。
- `KA-0057` policy_document: 本规定经公司总裁批准后，于正式发文当日开始实施，公司原培训管理相关规定自行废止。
- `KA-0058` policy_document: 为规范员工离职管理，确保公司各部门及各分支机构人力资源的合理流动，优化人力资源配置，依据国家及人力资源管理相关法规、政策以及公司组织管理制度特制定本离职管理规定。
