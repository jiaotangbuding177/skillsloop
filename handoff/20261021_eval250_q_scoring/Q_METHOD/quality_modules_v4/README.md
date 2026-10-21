# 新多轮产物的质量适配器

本目录是独立第四版fork。原`quality_modules/`、`quality_modules_v2/`、`quality_modules_v3/`及其6个质量POST/73728预约、另计基本TSR组件费用、原raw/分数/失败保持原字节。v4只修同一defect跨主责重复扣分导致整包报错的接口：外借缺陷从该条的defect_ids移至原owner交叉引用；非主责条目没有自己独立有效defect却被扣分时，只有该条为null，不自动抬成1，不改原owner原分，不放开重复扣分。若owner证据无效仍按v2为null，外借方也不能因清掉悬挂边而报整题错误。原raw条目、原图、清理前状态和每条清理理由保留审计。

**接口技术通过不等于语义可靠。** 本次真实CHECK重放只修复协议收口，仍保留裁判对利息/备用金的错误主责0；DRAFT87.5含额外要求也原样保留。没有为了得到某个期望分迭代提示词，没有新模型POST、没有擅自更换ecnu-max。人审为空、探索性未校准，正式750不由本目录放行。

v2的无证缺陷owner置null、清理悬挂引用和产物/观测级动态引用规则保持，不自动补缺陷引用或编造分数。v3的显式图片SHA一致性保持：引用唯一真图ID仍不强求SHA，但若裁判主动给SHA就不能与实际投递像素矛盾。judge_v5.py（含system提示词、原聚合规则）与v3逐字节相同。

全部原图保存在`native_archive_path`，Judge的`evidence_path`只投原模态适用的全部真图。未要求打印的XLSX保留全部sheet-wide页，默认打印诊断仅归档，相关导航ID清理且不可引用。原题明确要求打印则仍投全部原打印图。PDF、DOCX、PPTX和真实HTML状态不删页、不挑好图。T0003中性阅读事实动态读取当前原件和SHA绑定原流水，完整提供识别的220格原坐标、列头/月度、值、公式、主体/抵销组件与独立原流水重算；没有PASS/评分，不向Actor、用户或基本TSR提供。

fresh producer在实际render_pdf/_render_office/_render_html/_source_pages调用记录输入路径/SHA及像素SHA，结合确切role/record/相对文件名绑定；直接原图须字节相同。PDF/HTML/原图和source-only缓存均补确切native SHA。sheet-wide保留其派生SHA及原数据/样式/列宽不变性证明，不把派生SHA覆写成原件。私有调用日志留在`producer_invocations.private.json`。

本适配器复用旧v5的ecnu-max DRAFT/CHECK、完整证据投影、单位目录、逐条引文及图片核验、五维独立Q汇总。原250题2677项rubric、三档锚点、30/20/20/20/10权重和单缺陷主责保持，未新增标准。人员审核仍为空，分数只能标探索性、未校准。

不调用旧evidence_v4/v5的prepare入口：其中存在绑定旧任务的HTML/Office图复用分支。这里只复制16份原生解析/浏览器/投影/裁判源码，在每次全新Python子进程中导入，不共享调用者sys.modules。新产物每轮fresh inventory、实际解析和渲染；只允许原输入的同SHA、同环境实际图缓存。不会读取旧输出证据或旧评分cache。

## prepare：不调用模型

```python
import sys
sys.path.insert(0, r'D:\skillloop\output\20261019_eval250_multiturn_v2\quality_modules_v4')
import adapter
prepared = adapter.prepare(
    final_run_dir, case_dict_or_case_json_path, fresh_out_dir,
    environment_path=r'D:\skillloop\output\20261019_eval250_multiturn_v2\runtime\environment.json',
    turn_dir=explicit_turn_dir,  # 可省略；有则只读该轮交付，绝不读之后对话
    messages_path=explicit_turn_dir / 'actor_messages.json',  # 当前真实handoff消息
    extra_observations=[explicit_turn_dir / 'evidence/evidence.json'],
)
evidence = json.loads(Path(prepared['evidence_path']).read_text(encoding='utf-8'))
```

`final_run_dir`支持run、workspace、snapshot、inspection_workspace或turn目录。指定turn时优先该轮inspection_workspace，再snapshot；不从后续终态工作区回填前轮。每个out_dir必须全新，异常保留；不存在的必需文件与解析/渲染失败分别记录。

返回`multiturn-modality-applicable-quality-prepared-v3`字典，重要字段：

|字段|含义|
|---|---|
|`evidence_path` / `evidence_sha256`|全部原生内容、实际状态与全部适用真图索引|
|`native_archive_path` / `native_archive_sha256`|未减少任何原图的完整原生归档|
|`rubric_path` / `rubric_sha256`|与原任务整对象相同的冻结标准|
|`inventory_path` / `inventory_sha256`|本轮全部outputs/output及根目录实际交付文件，不择优|
|`images`|真实图片记录列表：`path,sha256,evidence_id,artifact,role,locator,page,...`；role为input/output|
|`visual_pages`|实际图片数量；完整记录也在evidence.visual_pages|
|`item_availability`|缺件/缺证/可评状态，AVAILABLE不是业务通过|
|`model_api_calls`|prepare恒为0|

具体内容在`evidence.artifacts[].extraction`，实际功能在`functional_observations`，原生图在`visual_pages`。Q用的`MTQUALITY:*`、`MTREADING:*`及所有quality_only/evaluation_scope=QUALITY_ONLY观测都不进入基本TSR/用户/Actor。真实文件、适用图及允许的实际业务功能观测按角色给出。

`represent(prepared, case, fresh_out_dir)`只从封签的完整实际证据构造新的模态适用呈现和动态阅读事实，0重跑Actor/0渲染/0API；适用于明确标注的旧技术实物重检，不能冒称新业务交付。

自动识别该轮v4 evidence.json的QUALITY_ONLY检查；每个测量对象filename/SHA都要与本次fresh inventory一致。表格错位可进入原D5、ICS实际consumer导入进入原D4，失败观测不等于新扣分规则，仍由原锚点和单缺陷主责评。没有要求多家解析库全通过、Outlook/云端兼容或实际到点响铃。

过程证据只取本轮`actor_messages.json`；终态无turn可取`messages_final.json`。原技能正文读取、runtime_links和skill_application计划写入等方法资料调用及反馈不投递Q；混合业务/技能调用不编造删节后的动作，只保留原工具身份与实际结构反馈，并明确正文被盲态省略。实际原始轨迹和私有删节审计保留，业务产物仍完整可见。

## 两阶段接口与冻结合同

`build_phase_request(prepared, phase='DRAFT', out_dir=fresh_path)`只构造盲态请求和完整真图、不POST。CHECK需要同一盲号的draft_result。Q计算、引文归一和伪引文置null沿原v5，不用TSR乘Q归零。

`score_phase(...)`与`score_two_phase(...)`默认无法发送请求。必须明确传`frozen_contract_path`，且其JSON包含：

```json
{
  "allow_model_post": true,
  "model": "ecnu-max",
  "frozen_before_first_post": true,
  "quality_adapter_sha256": "adapter.py当前SHA256",
  "quality_worker_sha256": "worker.py当前SHA256",
  "legacy_source_receipt_sha256": "legacy_source_receipt.json当前SHA256",
  "transport_source_pins": {
    "D:/skillloop/research/pipelines/skillsloop_ewi_v2/teacher_client.py": "实际transport源码SHA",
    "D:/skillloop/research/pipelines/skillsloop_graph/core.py": "其直接项目依赖SHA"
  },
  "absolute_deadline_epoch": 0
}
```

实际deadline应由root统一新冻结合同提供，示例0不能运行。调用方式：

```python
draft = adapter.score_phase(prepared, phase='DRAFT', out_dir=fresh_draft_dir,
    config_path=ecnu_config_path, frozen_contract_path=frozen_contract_path)
check = adapter.score_phase(prepared, phase='CHECK', draft_result=draft['result'],
    out_dir=fresh_check_dir, config_path=ecnu_config_path,
    frozen_contract_path=frozen_contract_path)
```

每phase最多1次物理POST，无自动重试；参数沿原max_tokens=12288、600秒、temperature=0、thinking=false。全局POST/输出预约、每题预算、并发、429退避和重试队列由外部统一协调器执行，本适配器**不拥有独立后台队列**。父合同还必须冻结实际transport服务/源码、模型配置、环境及本适配器source pins，不能只凭上面最小字段就宣称全局预算准入已实现。所有失败、费用、raw响应和阶段分均保留；最终使用CHECK，不择高分。

## 真实取证范围与边界

- PDF所有页Poppler真图；Office用固定LibreOffice派生PDF并实际渲染。XLSX原默认打印仅诊断，同时提供保留原值/样式/列宽的sheet-wide派生视图，不把未要求的打印分页当失败。
- HTML每次实际Chromium加载、两视口和通用交互状态。T0082/T0179/T0232另外fresh执行旧已声明专项场景，不使用旧捕获；未测试的交互保持未知。
- ICS导入采用root v4对本产物真SHA的本地consumer收据；不以纯文本解析冒称实际导入。根目录额外交付、额外sheet都保留，不给丰富文件数量加分，也不忽略额外内容的独立错误。
- 当前T0052专用搜索replay和T0144专用CalDAV旧helper绑定旧盲号，未迁移为通用新运行模块；这些专用观测缺失时必须保持UNSCORED，不能拿旧结果填补。
- 源/环境/图片/当前产物SHA在构造前检查，子进程返回后再核适配器/worker/环境。缺图/设施失败按原UNSCORED，不猜0或1。
- AI自查与有限技术控制不能替代人员可靠性校准，也不证明250题所有业务均成功。

`quality_validation/`中的历史T3/T148重检是旧技术实物的fresh解析/渲染，仅检验缺口是否进入原Q证据；不是新Actor运行或正式三组结果。模型POST仍为0，实际两阶段验证须由root在新冻结技术预算中启动。
