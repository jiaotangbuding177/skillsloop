---
name: human-resources-recruitment
description: Use this skill for HR recruitment workflows, candidate verification, interview scheduling, offer approval, and onboarding evidence checks.
---

# human_resources.conduct_recruitment_processes.skill

## Purpose

Compiled agent skill for conduct_recruitment_processes in domain human_resources.

## Invocation Contract

Inputs: user_request, job_title, required_skills, application_process, interview_schedule, business_context, authorization_context

Outputs: candidate_verification, final_approval, evidence, next_action

## Business Action

- Action id: `BA-121EC09ADD`
- Action type: `process_transformation`
- Intent: implement recruitment workflows for new hires
- Trigger examples: Run execute_recruitment_plan for task conduct_recruitment_processes.; Transform employee_recruitment into structured_forms.

Required input fields:

- `job_title`
- `required_skills`
- `application_process`
- `interview_schedule`

## Business Rule Contract

Must do:

- interview schedule must accommodate all stakeholders
- Return evidence atom ids for key conclusions.
- Expose missing inputs and unsupported scope.

Must not:

- Do not invent business facts absent from evidence.
- Do not treat low-confidence synthesis as a deterministic rule.
- Do not expose restricted details when external output is not allowed.

Escalate when:

- `candidate_disputes`
- `evidence_missing`
- `external_output_requested`
- `policy_non_compliance`
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

- `CM-F3D7979F` human_resources.conduct_recruitment_processes.module: atoms=39, relations=39, coverage=1.0, security=confidential

## Knowledge Atoms

- `KA-0121` policy_document: 第三条 管理权限和职能 一、人力资源部是员工招聘录用实施的管理部门，各部门负责人是招聘录用的实施和采纳人
- `KA-0122` policy_document: 二、人力资源部可根据本规定对员工进行招聘、录用管理
- `KA-0123` recruitment_process: 公司聘用员工以契合公司业务发展需要为原则，以职位所需专业知识技能、学历背景、工作经验及个人品德为招聘基准，通过“公平” 、 “平等” 、 “竞争” 、 “择优”的原则，进行多种渠道招聘
- `KA-0124` recruitment_process: 职位申请者必须如实填写《职位申请表》 （见附表） ，并按职位级别需要由直属领导、人力资源部、总裁进行面试
- `KA-0125` recruitment_process: P2/M2 以上或特殊要求的面试人须经公司总裁进行最终面试
- `KA-0130` policy_document: 人力资源部有权要求候选人提交学历、资质等证书进行验证以核实其面试资料之真实准确性
- `KA-0131` policy_document: 入职人员在面试时提交的《职位申请表》所填写的内容须真实有效，如经核实有虚假信息的，公司可视情节轻重做出书面警告或严重违纪处分
- `KA-0132` policy_document: 员工入职前及任职期间获得的执业资格及专业资格须向人力资源部进行报备
- `KA-0134` recruitment_process: 人力资源部负责《录用通知书》的发放工作
- `KA-0135` recruitment_process: 人力资源部招聘负责人须在钉钉上提交《人员聘用申请》并通过审批后，方可通过电子邮件的方式进行《录用通知书》的发放
- `KA-0136` recruitment_process: 所有《录用通知书》一律以人力资源部招聘负责人的邮箱对外发放，同时抄送给人力资源部部门负责人和总裁
- `KA-0137` recruitment_process: 录用员工须在《录用通知书》指定日办理入职手续并提供以下有效资料，不得提供任何虚假内容和借用、伪造的证件
- `KA-0138` recruitment_process: 入职员工应在入职当日提供完整的入职资料，如有特殊情况无法及时提供的应向公司人力资源部说明情况，经人力资源部批准后方可延迟提交
- `KA-0140` recruitment_process: 公司认为有必要进行入职前背调的相关职位的人员应提供有关曾受雇公司之真实资料并配合背调委托方完成背调，否则公司有权撤回和取消其录用资格
- `KA-0289` recruitment_process: 2、具有扎实的会计基础知识和2年以上工作经验
- `KA-0290` recruitment_process: 3、熟悉现金管理和银行结算，熟悉ERP或其他财务软件的操作
- `KA-0291` recruitment_process: 4、具有较强的独立学习和工作的能力，工作踏实，认真细心，积极主动
- `KA-0293` policy_document: 招聘面试流程说明
- `KA-0294` policy_document: 全面招聘计划
- `KA-0295` policy_document: 责任部门：人力资源部
