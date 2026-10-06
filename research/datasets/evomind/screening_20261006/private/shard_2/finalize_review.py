import json
from pathlib import Path

B = Path(__file__).parent
ids = json.loads((B / 'assigned_ids.json').read_text(encoding='utf-8'))
labels = {x['session_id']: x for x in json.loads((B / 'review_labels.json').read_text(encoding='utf-8'))}
source = json.loads((B.parents[2] / 'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))

# Narrow quotations were reread against selected source messages. They are evidence
# excerpts, not a claim that the assistant's professional conclusions are correct.
quotes = {
 0:'我提供的数字**可能不准确**，具体标准请以PDF原文为准',
 16:'匿名机制说明（同事/下级评价匿名）',
 19:'你说得对，是我疏忽了，应该先问你打什么字',
 25:'比如老板/法定代表人邮件确认、公司审批流程、授权书、合同审批截图等',
 27:'文件中所有的财务数字都是 **孤立的、无来源的估算**',
 28:'建立严格的"洁净室"机制隔离接触英特尔信息的人员',
 37:'delivery` 被系统落成了 `none`，这会导致它只跑、不主动推送',
 44:'先提炼JD的核心硬性门槛（**一票否决项**）和加分项',
 45:'如着色器实现、WebSocket断线重连方案',
 48:'五人中唯一有生产级 Agent 落地经验',
 53:'暂时未能确认精确到日的比赛日期',
 57:'空谈方案没用，要听具体案例',
 70:'小明直接改 **TOOLS.md** 加个硬规则',
 72:'同一只猴="配对数据"，不能用非配对检验',
 74:'先看必须项——乳酸菌、枯草、大肠杆菌的基因编辑或工程化能力',
 78:'没有实际的拍摄场景，而是全部通过数字生成',
 81:'"起初我以为…可真正上手才发现…"有转折',
 86:'建议直接核对作者SDM处理脚本',
 98:'5个近三年同类项目（合同复印件需另行准备）',
 99:'BMDM和RAW264.7两组独立实验数据一模一样',
 103:'按流程在行程确认后应该主动把每天的行程图生成好，再合并成一个合集PDF',
 121:'先自动搜一下，搜不到再问',
 130:'我是这个AI专家，帮我整个创业思路',
 131:'数据审查周期不计入项目工期',
 136:'LibreOffice 可用，直接转 PPTX → PDF，确保每页全幅显示',
 138:'技能目录是只读挂载的，我先复制到可写位置再安装',
 139:'用于邮件客户端（或我）登录你的邮箱，而不是用你的登录密码',
 140:'这款盲盒的产品logo**（放在盒面上的系列标志），不是公司品牌',
 144:'个人知识库/` 存在但为空，wiki 实际在 workspace 根目录',
 169:'必须全部替换为 **"EvoMind"**',
 189:'学生端独立用户具体数字** — 您说几万，方便给个准数吗',
 191:'LangGraph+LangChain+RAG+Agent+Dify | 少量提及 | Docker',
 194:'没有你的语气、表情、铺垫——他只会觉得"又来了一篇罪状"',
 197:'去掉 emoji 图标** — 不再使用 📊📌🌍 等符号',
 212:'分配在银行日记账中尚未体现',
 215:'她必须自己先做一轮判断（20→5）',
 216:'你方有限合伙当初投钱给有限公司，现在有限公司把钱退回来',
 228:'这份PDF是近畿全区域的大图，和用户发的不是同一份',
 233:'底部原理末句 | `双缩试剂` | `双缩脲试剂`',
 239:'Device Flow 登录（OAuth，不需要手动输 Token）',
 251:'加 (2)(3)…后缀区分，避免数据混淆',
 265:'6张图全部从零重新生成，无Logo、无涂抹痕迹、无任何填充色块',
 268:'等于钱没到手先交权。建议改为与出资同步生效',
 282:'三个商品全部未选中（圆圈都是空的），但底部却显示"已选 5 件 / 合计 ¥1602"',
 284:'校验通过，只是输出目录只读。换个可写目录打包',
 285:'图片模型后端持续不可用。改用内容级质检兜底',
 296:'拿走公司约 80%+ 表决权和全部经营管理权',
 302:'市场地位表述为**初步沟通口径，待正式行业报告确认',
 303:'另外"产值"≠"收入"，必须以审计报告为准',
 304:'图2 左触角末端被画成了卡通眼球、图3 翅膀画成了多片',
 305:'把上市公司"机器人（300024）"的高管张进、刘子军套到了国巡头上',
 310:'客户版的账户应该写**信托的募集账户**，而不是基金账户',
 316:'给法定代表人戴上"事前审批"和"事后追偿"两道枷锁',
 324:'连接箭头方向反了（旋转 180° 后指向左边）',
 325:'切成 16 块分别处理，大幅降低内存峰值',
 327:'页面框架拿到了，但文件数据需要调 API',
 333:'这不是让你降帧率，和 60fps 不冲突',
 335:'在缺口后的下一块木板重生',
 336:'我把它说得比原文更硬了',
 340:'发现问题→明确需求→针对性修改→说明理由',
 341:'页面是JS渲染的，我找一下它内部调用的下载API',
 344:'我之前"生产现场深度待确认"的表述不够准确',
 346:'增值税买入价按IPO发行价算',
 348:'关节机器人本体设计、工业机器人机械手设计、RV/行星/谐波减速机设计',
 349:'纯市场化、能领投1000-3000万、**无落地/返投要求',
 354:'把三年目标中的生态建设指标（论坛路演、投资机构联动）补回',
 355:'序言写了"有意投资"，但全文没排除投资义务',
 358:'公开渠道查不到任何记录**，无法验证',
 364:'但"真期刊"≠"真合作"',
 365:'巡检数据与 DCS 系统对接**（"对接不了我们没法用"',
 368:'箭头全部改成规整的折线（不再斜穿）、标签挪到空白区域',
 369:'先打一场官司证明机构有过错，再打第二场追偿官司',
 371:'来源冲突**（C1 续航6h/8h/10h、C2 预算300万/600万/980万',
 374:'重点把精力放在"申请函盖章 + 公证"这条路上',
 376:'对方有没有开过写"定金"的收据或发票',
 380:'不能按"品类"一刀切',
 382:'两笔明细相加为 **39.44万元**（23.44+16）',
 383:'研发 V2.2 计划（草稿）、MCU 备选报价（待确认）未纳入正文',
 384:'曾误读为"COWIN"，高清后确认 JOY',
 388:'有中文 OCR 可用，对关键页面做文字抽检',
 392:'没有要求甲方在投资终止后返还或销毁资料',
 396:'上一版我按早期周会记录写错了，已纠正',
 401:'第三方镜像站（llmbase/mcpservers）也只有安装说明、没有内容',
 402:'"虚拟内存不足"** → 系统内存/页面文件问题',
 406:'绩效 1500 若人人固定月月足额',
 408:'"基金免税"的通道关闭了，整套算账逻辑要重来',
 410:'【IDC项目】只是内部叫法，没有对应的官方主体含义',
 411:'文字在组合图形内，需要递归遍历。修正脚本并重跑',
 421:'可能他后来跳槽了，也可能存在同名混淆',
 425:'附件6（初始业务计划）在原件中倒置，我旋转后重新识别',
 447:'IND-enabling（专利布局）**，从未进临床',
 448:'基因编辑做的是酿酒酵母**，大肠杆菌敲入敲除无证据',
}
extra_ids = {
 16:['a_11ddb92d0807dcf09a'],
 53:['a_012d4570df3b6796c5'],
 72:['a_c7d31328bf6941d52c'],
 233:['a_b0ca74ca9f24c5f4bb'],
 239:['a_8cee59e8d6acf6223b'],
 304:['a_814b72a088f3100f9c'],
 341:['a_f22bb75bfd7b872df9'],
 346:['a_617aeb7f827ddc1f6e'],
 406:['a_6ad15c9ccd8eff8f3c'],
 411:['a_beb241d26accdc267b'],
}
for index, more in extra_ids.items():
    x = labels[ids[index]]
    if x['candidates']:
        old = x['candidates'][0]['assistant_ids']
        x['candidates'][0]['assistant_ids'] = list(dict.fromkeys(old + more))
        x['review_basis'] = 'expanded'
for index, quote in quotes.items():
    x = labels[ids[index]]
    if not x['candidates']:
        continue
    c = x['candidates'][0]
    chosen = [a for a in source[ids[index]]['assistant_contents'] if a['group_id'] in c['assistant_ids']]
    chosen += [u for u in source[ids[index]]['user_requests'] if u['group_id'] in c['user_ids']]
    if any(quote in a['content'] for a in chosen):
        c['evidence_quote'] = quote
    else:
        print('QUOTE_NOT_APPLIED', index, repr(quote))

# Final semantic read found these two are conventional outputs or only prior
# organization instructions, with no concrete task correction or local method.
for index, reason in {
 90:'知识库整理按现有模式做检查，结果主要为通过声明；未发现当前任务特有修订或实际新整理方法',
 115:'图片按参考风格生成，描述基本为外观变化和内容保留，未见具体修订或失败规避方法',
}.items():
    x = labels[ids[index]]
    x.update(decision='HOLD', reason_code='INSUFFICIENT_METHOD', reason=reason, candidates=[])

for x in labels.values():
    for c in x['candidates']:
        reminder = '学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验'
        if reminder not in c['limitations']:
            c['limitations'].append(reminder)

for filename in ['root_batch19_labels.json','root_tail_labels.json']:
    f = B / filename
    if f.exists():
        extra = json.loads(f.read_text(encoding='utf-8'))
        labels.update({x['session_id']:x for x in extra})
    else:
        print('NOT_YET', filename)

ordered = [labels[s] for s in ids if s in labels]
(B / 'review_labels.json').write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding='utf-8')
print('coverage',len(ordered))
