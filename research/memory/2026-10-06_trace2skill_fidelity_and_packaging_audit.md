# 2026-10-06｜Trace2Skill复用边界与技能封装核查

## 用户要求

用户选中交付技能里的泛三步，追问是否完全执行Trace2Skill、最终如何包装。本轮仅只读核查与解释；不启动新模型实验、代码修复、技能重写或消费。

## 核对结论

- 准确名称为企业历史UNKNOWN适配＋官方离线演化核心＋OpenClaw脚本封装。A实际3MAP/1MERGE/程序APPLY落盘，不是完整官方rollout/成功失败分析/验证选择/留出评测链路；B未进入技能更新。
- run_experiment.py:192自写经验分析，:172覆写MAP及合并提示，:210复制initial_skill.md，:217继承调用官方run。官方parallel_evolving_agent.py:3075读取已有skill，:3089MAP、:3131REDUCE、:3211程序APPLY、:3224落盘。官方CLI本来要求skill_dir/SKILL.md；本实验草稿由我们写，不能说全部内容/命名由模型从空白生成。
- 初始22行弱草稿固定name/description和主题，泛三步在initial_skill.md:11–14；交付原三步在SKILL.md:22–24，学习新增规则在:11–20及:30–31。单个技能数量是本批预设，不是自动发现技能数的实验证据。
- 本次input_mode=records，按2份记录一批，3补丁合并；没有语义轨迹聚类或我方跨会话工作流聚合，不能把MAP分批/补丁合并称聚类。
- 使用JSON路线skip_translation=True，max_verification_rounds=0，格式自修复/续写关闭；并非官方默认完整纠错配置。最终检查仍执行，不能把当前质量外推作者方法。
- 没有调用skill-creator agent或临时creator会话。run_experiment.py:225/:235调用OpenClaw两个Python脚本，quick_validate.py检查SKILL与YAML/name/description等；package_skill.py:77用zipfile封装目录。没有新LLM调用或正文润色。
- 包仅有SKILL.md，2732字节，正文和独立交付一致，没有scripts/references；尚未验证注册、导入或消费。先前“安装包/可导入”标签应改为技能归档包，不升级为验收过的安装能力。

## 新增源码因果发现

- 原始MERGE替换操作没有old_text（official_result.json:153附近raw_json）；序列化final_patch.json:6–11显示默认空串。
- 官方解析parallel_evolving_agent.py:1591缺键→空串；:275章节文本包含原标题；:282执行section_text.replace('', content,1)。实际插入新增内容，没有替换原标题/旧流程。
- content没有尾换行，新增末尾直接接原标题，产生最终SKILL.md:21标题连行及:22–24旧三步残留。applied_diffs.patch:19–22与此一致。
- 因果是缺有效替换锚点的补丁被程序接受后按空串语义执行；不是ZIP打包把正文损坏，也不能只说模型故意重复。格式检查只看元信息未拦截。
- 以上为新增源码/产物核对观察；无新模型实验证据，不改原生成物、不掩盖此前质量问题。修复或开启翻译是否改善仍未实验，不承诺开修复必解决语义。

## 记录与边界

- [总实验报告](../reports/2026-10-06_trace2skill_ecnu_total_experiment_report.md)已补实际复用表、封装过程与空锚点因果，并将归档包标签澄清；内容只涉及本实验。
- 承接[最终结果记忆](2026-10-06_trace2skill_ecnu_continuation_and_final_results.md)。请求数仍19、265639已报告tokens＋1超时用量未知；skill/包/冻源不变，未注册或执行。
- 两位代理独立只读核对官方链路与应用/封装；源定位交叉一致，无凭据读取、新API或文件修复。当前输出仍是待审候选。
