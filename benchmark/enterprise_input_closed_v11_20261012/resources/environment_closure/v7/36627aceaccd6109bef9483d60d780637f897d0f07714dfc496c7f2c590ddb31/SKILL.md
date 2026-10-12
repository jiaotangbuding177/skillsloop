---
name: human-resources-performance
description: Use this skill for HR performance evaluation, review periods, evaluation criteria, feedback, rating scales, action plans, and training recommendations.
---

# human_resources.evaluate_employee_performance.skill

## Purpose

Compiled agent skill for evaluate_employee_performance in domain human_resources.

## Invocation Contract

Inputs: user_request, evaluation_period, criteria, feedback, rating_scale, business_context, authorization_context

Outputs: action_plan, training_recommendations, evidence, next_action

## Business Action

- Action id: `BA-E69B148438`
- Action type: `record_transformation`
- Intent: evaluate employee performance based on defined criteria
- Trigger examples: Run conduct_performance_review for task evaluate_employee_performance.; Transform employee_training, performance_evaluation into employee_records.

Required input fields:

- `evaluation_period`
- `criteria`
- `feedback`
- `rating_scale`

## Business Rule Contract

Must do:

- feedback must be constructive and actionable
- Return evidence atom ids for key conclusions.
- Expose missing inputs and unsupported scope.

Must not:

- Do not invent business facts absent from evidence.
- Do not treat low-confidence synthesis as a deterministic rule.
- Do not expose restricted details when external output is not allowed.

Escalate when:

- `disputed_evaluations`
- `evidence_missing`
- `external_output_requested`
- `misaligned_or_missing_quote`
- `missing_feedback`
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

- `CM-1E8685E4` human_resources.evaluate_employee_performance.module: atoms=42, relations=42, coverage=1.0, security=confidential

## Knowledge Atoms

- `KA-0050` training_program: 培训考勤结果将存入员工人事档案，员工参与内部培训的情况作为年度绩效评估依据。
- `KA-0150` performance_evaluation: 试用期考核用于确认职位要求与员工能力的匹配度。
- `KA-0151` performance_evaluation: 用人部门对新员工进行试用期考核，并结合《试用期自我工作鉴定》内容进行评估。
- `KA-0152` performance_evaluation: 人力资源部要求新员工提交《试用期自我工作鉴定》，并组织部门负责人进行试用期评估。
- `KA-0153` performance_evaluation: 用人部门负责人填写转正意见，人力资源部面谈复核后提交总裁审批。
- `KA-0154` performance_evaluation: 员工提交“试用期转正评估”并附《试用期自我工作鉴定》后，总裁审批通过方可转正。
- `KA-0155` performance_evaluation: 直属上级及部门负责人监督新员工试用期内的绩效和日常表现，并及时沟通反馈。
- `KA-0209` policy_document: 由公司总裁牵头组织的公司绩效考核管理小组为公司的绩效管理决策机构，领导公司的绩效考核管理工作。
- `KA-0210` policy_document: 人力资源部是绩效考核管理的执行机构，主要职责包括绩效考核管理制度体系的草拟与修订。
- `KA-0211` policy_document: 人力资源部负责绩效考核管理制度的宣导、解释和培训。
- `KA-0212` policy_document: 人力资源部负责组织绩效考核相关管理流程的实施。
- `KA-0213` policy_document: 人力资源部负责协调处理绩效考核的投诉。
- `KA-0214` policy_document: 各中心、各部门负责人负责提供相关年度、半年度、月度绩效评估及改进计划。
- `KA-0215` policy_document: 各中心、各部门负责人负责本中心/部门绩效体系运作的整体组织及管理。
- `KA-0216` policy_document: 各中心、各部门负责人负责所属员工的绩效指导与评价。
- `KA-0217` performance_evaluation: 员工职责包括沟通确定年度、半年度、月度（如有）绩效目标和内容。
- `KA-0218` performance_evaluation: 员工需按时完成绩效述职报告和改进计划，与直属上级和部门负责人双向沟通。
- `KA-0219` performance_evaluation: 公司绩效考核管理体系包括目标与关键成果体系、员工绩效考核管理和阶段性评估、项目激励和年度综合考评。
- `KA-0220` performance_evaluation: 绩效管理过程由绩效目标与计划的拟订、绩效指导、绩效评估与绩效改进四部分组成。
- `KA-0221` performance_evaluation: 绩效考核管理强调部门负责人与员工的共同参与，强调沟通和绩效辅导。
