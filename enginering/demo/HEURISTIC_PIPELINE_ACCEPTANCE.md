# 启发式全管道验收

本轮从2026-10-04开始，跨日于10-05继续。验收对象为独立Demo的heuristic分支。旧legacy路径、旧实验和旧库保留；其他运行服务未修改。以下输入为明确披露的合成材料，不是企业效果或benchmark结果。

## 回归及十二阶段夹具

最终冻结后运行 `python -m unittest discover -s tests -q`：**281项通过，44.875秒**。改动前基线为92项；271/256/224项为此前版本实跑结果。新增检查覆盖来源保留、交错任务、要求继承、多值要求、调用与评价归属、方法支持、整个簇相容性、来源台账、无损索引、逐步骤范围封装、历史文件交接、精确版本和权限边界，以及单次直接更新选择路由/配置/失败处理。

[最终独立fixture](artifacts/heuristic-acceptance/runs/fixture-20261004T192259637816Z-30c0e72e/acceptance.json)通过。来源整理→任务线索→关系轨迹→工作流聚合→官方封装→个人采纳→选版读取与非空交付→反馈→同技能v2→组织审核→Bob复用→再次反馈恢复均执行。13个宿主派发为人工模型夹具，真实模型请求0；本地读取、文件交付、哈希检查和官方打包实际执行。组织审核为测试决策，反馈回流后没有自动发布组织更新。

[复现记录](artifacts/heuristic-acceptance/runs/fixture-20261004T192259637816Z-30c0e72e/reproducibility.json)保存输入、声明范围内的31份源码快照、前后哈希、公开配置及产物清单。夹具不能证明模型语义准确率或真实企业效果。

## 真实模型验收与失败保留

| 运行 | 实际完成范围 | 宿主派发 / 真实模型开始 | 保留的失败及修正 |
| --- | --- | --- | --- |
| [第一次](artifacts/heuristic-acceptance/runs/live-20261004T143246915143Z-95fd9e4e/acceptance.json) | 来源已整理，关系输出被拒 | 1 / 1 | 模型数组、分片结构错误；补完整JSON模板，没有手填语义或放松校验 |
| [第二次](artifacts/heuristic-acceptance/runs/live-20261004T144118855654Z-5cf30761/acceptance.json) | 阶段1—8，已有v1及真实交付 | 7 / 17 | 同维度两条可并存ADD被误拒；改为并存，只有明确替换覆盖 |
| [第三次](artifacts/heuristic-acceptance/runs/live-20261004T153848122242Z-332ccbbe/acceptance.json) | 阶段1—8和反馈恢复 | 7 / 15 | 145105字符超聚合预算；无损索引后92222字符，原110000预算保持 |
| [第四次](artifacts/heuristic-acceptance/runs/live-20261004T161518468674Z-9ab23862/acceptance.json) | 阶段1—4 | 4 / 6 | 实际Get-Content读取未被识别；新增严格单一命令及返回内容核验 |
| [第五次](artifacts/heuristic-acceptance/runs/live-20261004T164427858281Z-c9ab0513/acceptance.json) | 阶段1—4 | 4 / 6 | 实际读取相同官方安装源但旧审计只认副本；新增固定路径、初始化SHA和两文件SHA核验 |
| [第六次](artifacts/heuristic-acceptance/runs/live-20261004T170427883275Z-feb3ae06/acceptance.json) | 阶段1—6，v1采纳；消费审计被拒 | 5 / 9 | 绝对路径技能完整读取被参数顺序和missing-workdir检查误拒；按精确目标和严格allowlist修正 |
| [第七次](artifacts/heuristic-acceptance/runs/live-20261004T172148621668Z-a6baae0c/acceptance.json) | 阶段1—8，两回合实际读取及交付 | 10 / 20 | 更新器将只支持m2的引用绑定m1+m2，证据范围检查正确拒绝；不放松校验 |
| [第八次](artifacts/heuristic-acceptance/runs/live-20261004T1825-final-prebound-a3c07162/acceptance.json) | 阶段1—8，两份真实交付1296/2817字节 | 10 / 19 | 模型返回说明＋唯一JSON代码块，纯JSON解析在编译前拒绝；实际选择7获准/3延期可编译，但原run没有v2 |

以上每次均保存失败、输入、模型响应、源码快照和已产生的技能。宿主不在运行中改代码或自动阶段重发。必要修正结束旧run后另开冻结run。

第四、第五回执的[独立免费复核](artifacts/heuristic-acceptance/creator-read-preflight-20261004T170330-2e744239.json)确认完整官方读取；实际路径不同，收据保留来源。原失败状态及数据库不改写。原生草稿及宿主组装的免费预演只验证封装，不算真实消费或UPDATE成功。

前五次23个宿主派发、45次记录的真实模型开始；记录runtime tokens448105、运行墙钟约31.02分钟。两类token记录含缓存字段，不能直接推费用；供应商传输重试未测。

第六次官方读取为FULL_FILE，宿主封装及官方打包通过。v1包、个人采纳和消费入口的文本身份一致，消费文件1586字节；没有反馈回合和v2，不能计全链成功。原run的31份源码前后哈希、输入和产物清单均匹配。六次累计28派发/54真实模型开始、记录runtime tokens533174、墙钟约35.30分钟；费用与传输重试仍未知。

读取修正后的[免费预演](artifacts/heuristic-acceptance/all-native-read-preflight-20261004T172019-242aa385.json)复核历史10个已存会话、28个工具，5官方+5选定v1均完整，正文与版本一致；原失败和数据库不变。第七次真实1—8通过；两份实际文件1610/2338字节、两轮v1完整读取及正文身份均匹配，反馈文件交接成功。阶段9方法证据检查正确拒绝模型错误绑定，v2未产生，不计真实完整闭环。

第七31份代码前后/其同版本fixture相同，159份产物清单全部匹配，当前密钥字面检查通过。七次累计38宿主派发/74记录模型开始、900015记录runtime tokens、46.77分钟；免费回放不计真实通过，费用及传输重试未知。

最终修正已冻结：宿主预绑定方法自己的来源、完整引文、作用范围和插入正文，模型只选单元及唯一旧锚；没有自由content或analyses。不完整的多范围绑定延期，同维同值的正常副本保留；原动作等字段转义，不能遮住范围说明。[第七静态材料免费预演](artifacts/heuristic-acceptance/preflights/seventh-run-prebound-update-final-d0620aa6/preflight.json)为1个当前任务单元可编译、2个范围增量延期；人工位置选择、provider0，不是新真实UPDATE。新增29项矩阵及独立同构检查通过。原生learn配置已更正为实际提示变体/8192/agent timeout/未指定温度，旧run配置不追改。

[唯一调用返回免费重放](artifacts/heuristic-acceptance/relational-call-result-preflight-20261004T180547-0555349d.json)把2个已绑定write的真实返回补到attempt及W目录；仍6个工具来源未决、业务UNKNOWN、原DB哈希不变。

第八FAILED已保留，163项产物清单匹配，31份源码前后与其对应fixture相同。实际learn确为公开冻结投影，7获准单元/3宿主延期；有效analysis.json与final中的唯一JSON代码块同对象。阶段5官方creator完整读取通过；阶段9另一次错用根路径的read真实失败，不因解析修正追认为成功。271最终版本只对新学习分支接收严格对象或唯一明确完整json代码块，原文及解析范围/hash保留，原compiler/legacy/R/W不变。

八次完整尝试累计48派发/93真实模型开始、1174598记录runtime usage.total、约61.37分钟；费用/传输重试未知。最后采用独立副本继承第八真实1—8，阶段9另验，不叫同一新版的全量冷启动成功。[固定原回复免费回放](artifacts/heuristic-acceptance/runs/stage9-captured-20261004T190116866877Z-e7cb1128/acceptance.json)实际官方打包、v2采纳、v1文件/hash保留通过；1宿主派发/0真实请求，包内容逐字等于采纳正文，源目录不改。

[阶段9原生续验](artifacts/heuristic-acceptance/runs/stage9-live-20261004T190145188788Z-4ef5824d/acceptance.json)最终FAILED：1新派发/7真实开始、114240记录runtime usage.total，OpenClaw内层约300秒超时，final为空，宿主正确保留失败，没有采纳v2。实际已写outputs/analysis.json不能代替未完成的权威回复。7工具调用未报失败、7请求收到HTTP200，但这不证明完整答案；memory-reindex报错存在，未证明它是超时原因。原源码32项前后相同、继承状态不改。后续修正只把精确新契约的纯选择改为一次结构化LLM请求，原creator/chat/legacy不变；该新版本另行冻结验收，不追认本次成功。

## 复现及研究边界

最终[单请求结构化续验](artifacts/heuristic-acceptance/runs/stage9-live-20261004T192338068556Z-7ace1613/acceptance.json)已FAILED：180秒read响应超时，1派发/1请求开始，无完整响应、无usage、没有patch/v2。实际配置为qwen3.7-plus、anthropic-messages、8192、temperature0、direct网络及完整公开投影；未发送工具定义。源代码/继承状态不改，旧v1保留。全体十次实际尝试50派发/101开始、已知usage.total1288838＋最后1次UNKNOWN；没有自动重发，也不能从native中途文件或缺失usage拼出成功/零成本。实时更新尚未通过，不启动新训练或benchmark。

运行目录拒绝复用。复现清单只覆盖声明的必要源码、官方creator和公开配置，没有复制.env或整个vendor。模型回答不保证逐字重现。实时run检查当前密钥字面值是否落盘，不等于全面凭据审计。

阶段2—3冷启动共一次语义派发；有界搜索、来源检查和整个簇约束不能单独证明语义正确。无损索引保证已有材料完整传输，不补缺失语义。逐步骤封装控制结构及范围；阶段9新增内容与范围已冻结，但NO_CONFLICT仍模型判断，基准最低保留不等同于阶段5完整逐步骤范围覆盖。

本次不证明无效技能减少、整体模型费用下降、技能复用或更新质量改善，更不证明benchmark显著增益。微调、强化学习及新benchmark没有执行。
