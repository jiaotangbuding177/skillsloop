---
name: human-resources-departures
description: Use this skill for HR employee departure workflows, resignations, exits, termination procedures, exit documentation, and severance evidence checks.
---

# human_resources.handle_employee_departures.skill

## Purpose

Compiled agent skill for handle_employee_departures in domain human_resources.

## Invocation Contract

Inputs: user_request, exit_type, reason, effective_date, documentation, business_context, authorization_context

Outputs: exit_interview_notes, severance_details, evidence, next_action

## Business Action

- Action id: `BA-9B45B365E9`
- Action type: `process_transformation`
- Intent: standardize employee exit procedures
- Trigger examples: Run process_employee_exit for task handle_employee_departures.; Transform employee_exit_management into employee_records.

Required input fields:

- `exit_type`
- `reason`
- `effective_date`
- `documentation`

## Business Rule Contract

Must do:

- documentation must comply with regulatory standards
- Return evidence atom ids for key conclusions.
- Expose missing inputs and unsupported scope.

Must not:

- Do not invent business facts absent from evidence.
- Do not treat low-confidence synthesis as a deterministic rule.
- Do not expose restricted details when external output is not allowed.

Escalate when:

- `disputed_exit_reasons`
- `evidence_missing`
- `external_output_requested`
- `misaligned_or_missing_quote`
- `missing_documentation`
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

- Data level: `restricted`
- Human approval required: `True`
- External output allowed: `False`
- Evidence policy: `grounded_atoms_only`
- Compile readiness: `ready`
- Readiness blockers: `none`

## Dynamic Cognitive Modules

- `CM-7BD1ABD8` human_resources.handle_employee_departures.module: atoms=59, relations=59, coverage=1.0, security=restricted

## Knowledge Atoms

- `KA-0060` employee_exit: 员工离职的类别包括终止试用、辞退、开除、辞职（劳动合同解除）、裁减、合同期满、退休等。
- `KA-0061` employee_exit: 终止试用是因员工在试用期间被证明不符合录用条件的，公司单方面与员工解除劳动合同。
- `KA-0062` employee_exit: 辞职是由员工本人主动提出申请离职的方式。
- `KA-0063` employee_exit: 辞退和开除是员工因特定原因，公司单方面与员工解除劳动合同的方式。
- `KA-0064` employee_exit: 裁减是公司因经营状况不佳等须缩减人员编制，由公司提出的员工离职方式。
- `KA-0065` employee_exit: 员工达到法定退休年龄而离职的方式
- `KA-0066` employee_exit: 在试用期间被证明不符合录用条件，包括以下情形之一的，公司有权终止试用期
- `KA-0067` employee_exit: 试用期内有严重违反公司规章制度，符合辞退或解除情形的
- `KA-0068` employee_exit: 试用期内请各类假期超过 15 天的
- `KA-0069` employee_exit: 试用期内未完成规定工作项目或者业绩目标的
- `KA-0070` employee_exit: 试用期内违反公司规章制度受到处分的
- `KA-0071` employee_exit: 试用期内受到两次书面警告处分的
- `KA-0072` employee_exit: 二、员工发生下列情形，公司将依法辞退员工，解除劳动关系
- `KA-0073` employee_exit: 1、员工患病或非因工负伤，医疗期满后，不能从事原工作也不能从事由公司另行安排的工作的
- `KA-0074` employee_exit: 2、员工不能胜任工作，经过培训或者调整工作岗位，仍不能胜任工作的
- `KA-0075` employee_exit: 包括以下情形： 1）不能按要求完成工作任务安排的
- `KA-0076` employee_exit: 2）不能再同样的时间完成公司同类工种、同类岗位人员的工作量的
- `KA-0077` employee_exit: 3）业绩不达标或绩效考核不合格的
- `KA-0078` employee_exit: 4）公司规定的任职资格（包括但不仅限于从业资质）丧失的
- `KA-0079` employee_exit: 身体状况不符合工作岗位要求的
