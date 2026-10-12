---
name: human-resources-training
description: Use this skill for HR training programs, training schedules, training objectives, target audiences, delivery methods, and evaluation criteria.
---

# human_resources.manage_training_programs.skill

## Purpose

Compiled agent skill for manage_training_programs in domain human_resources.

## Invocation Contract

Inputs: user_request, program_name, objectives, target_audience, delivery_method, business_context, authorization_context

Outputs: schedule, evaluation_criteria, evidence, next_action

## Business Action

- Action id: `BA-D932680A06`
- Action type: `resource_transformation`
- Intent: create structured training schedules for employees
- Trigger examples: Run design_training_schedule for task manage_training_programs.; Transform employee_training into training_schedules.

Required input fields:

- `program_name`
- `objectives`
- `target_audience`
- `delivery_method`

## Business Rule Contract

Must do:

- schedule must align with company strategy
- Return evidence atom ids for key conclusions.
- Expose missing inputs and unsupported scope.

Must not:

- Do not invent business facts absent from evidence.
- Do not treat low-confidence synthesis as a deterministic rule.
- Do not expose restricted details when external output is not allowed.

Escalate when:

- `conflicting_objectives`
- `evidence_missing`
- `external_output_requested`
- `misaligned_or_missing_quote`
- `missing_schedule_details`
- `sensitive_data_requested`
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

- Data level: `confidential`
- Human approval required: `True`
- External output allowed: `False`
- Evidence policy: `grounded_atoms_only`
- Compile readiness: `ready`
- Readiness blockers: `none`

## Dynamic Cognitive Modules

- `CM-99308FF7` human_resources.manage_training_programs.module: atoms=40, relations=40, coverage=1.0, security=confidential

## Knowledge Atoms

- `KA-0003` training_program: 人力资源部负责培训需求调查、培训计划制定和培训的组织实施。
- `KA-0004` training_program: 培训项目组织包括需求、培训通知、课件收集、现场管理和评估。
- `KA-0005` training_program: 内部培训师管理与监督包括评估和激励。
- `KA-0006` training_program: 各部门负责人根据公司整体培训需求和人力资源部的培训计划推进，兼任内部培训师。
- `KA-0007` training_program: 部门负责人需具备一定的培训或演讲技巧、具备教材、教案编写能力。
- `KA-0008` training_program: 结合公司实际情况编撰教材、策划培训的开展。
- `KA-0009` training_program: 原则上每年年初人力资源部对各部门和各关联公司的培训需求进行调查， 各部门和各关联公司根据公司的战略及年度工作计划提交培训需求
- `KA-0010` training_program: 人力资源部根据公司战略目标对培训需求汇总、分析后，制定本年度培训计划
- `KA-0011` training_program: 对于计划外的内部培训或外派培训，各部门或各关联公司负责人须另行以书面形式提出培训需求申请，经总裁核准、抄送人力资源部后，由人力资源部协调相关时间和资源统一安排实施
- `KA-0012` training_program: 如遇到公司重大经营方针或内部组织架构调整、关键岗位员工不能胜任本职责工作等情形，经总裁核准，人力资源部可适时组织培训
- `KA-0013` training_program: 公司内部培训包括新员工入职培训、内部分享会以及由人力资源部编制年度培训计划后，统一安排时间并协调内部培训师实施的培训
- `KA-0014` training_program: 新员工入职培训由人力资源部组织并实施
- `KA-0015` training_program: 内部分享会由人力资源部组织，各部门人员须配合实施
- `KA-0016` training_program: 公司各中心/部门最高负责人皆担负有培养员工的责任，是内部培训师的主要承担者
- `KA-0017` training_program: 业务骨干或项目 PM 是员工业务开展和项目培训的主要承担者
- `KA-0018` training_program: 公司内任何一名具备培训或演讲能力、愿意承担内部培训师职责的人员均可向人力资源部提出申请，经人力资源部审核、总裁核准后可成为内部培训师
- `KA-0019` training_program: 本专业领域技能方法或本部门相关职能体系的培训
- `KA-0020` training_program: 负责培训资料的收集、编写、内容优化、主题培训教案的制订等（每年必须更新一次）
- `KA-0021` training_program: 学习、消化外部知识体系或培训课程，转化为内部培训课程，引入公司内部实施
- `KA-0022` training_program: 根据人力资源部设计的培训计划实施培训，如有调整须先征得人力资源部认可
