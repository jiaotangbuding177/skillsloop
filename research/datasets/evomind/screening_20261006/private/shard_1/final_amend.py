import json,pathlib,collections
p=pathlib.Path(__file__).parent;ids=json.loads((p/'assigned_ids.json').read_text(encoding='utf-8'));f=p/'review_labels.json';rows=json.loads(f.read_text(encoding='utf-8'));by={r['session_id']:r for r in rows};cards={r['session_id']:r for r in json.loads((p.parent/'all_cards.json').read_text(encoding='utf-8'))}
expanded=[0,1,7,11,12,32,81,83,100,108,179,186,196,199,212,235,242,251,254,263,275,277,278,279,288,295,297,302,303,311,325,332,333,335,341,348,364,373,380,385,388,389,393,425,442,444,448,459,467]
new=[
 (7,'Wiki目录与索引一致性修复','Wiki归档后逐一比对文件名与index.md条目；修正简称与真实文件名不一致，新增页面必须有索引项，文件存在但读取失败与文件缺失分别核查',['wiki'],['a_324816dee58381cecf','a_3cf6ff0457c6feeb26'],'index.md中的条目名称与实际wiki文件名不一致'),
 (12,'开源技能仓库克隆排障','克隆长时间超时时改浅克隆减小历史对象传输，再检查目录和技能入口文件；不能将仅开始安装写成技能已可用',['安装','技能'],['a_aeb290f0a755beb85d'],'克隆超时了。让我尝试手动克隆，使用浅克隆来加快速度'),
 (32,'知识库过期内容分层治理','销售方法论、产品介绍等稳定参考资料标reference而不按新闻到期自动淘汰；时效新闻单独归档，按内容用途判断更新需求',['wiki','过期'],['a_8a3cc30d880ed67c48'],'内容不会过时'),
 (108,'输入法动态皮肤能力边界','ssf皮肤包不支持运行时代码，关键词触发自动换肤需外部监听程序；先Web演示验证交互再选Windows运行时集成，不能把静态皮肤交付称为动态能力',['皮肤','输入法'],['a_b4df457e501814f18a'],'不支持运行时代码'),
 (179,'企业增长阶段诊断修正','已卖出一千账号的产品应讨论一千到一万扩展，而非继续需求验证；用真实已发生收入与采用阶段调整行动计划，避免重复低阶段实验',['1000','一千','卖'],['a_35ee0a245461e50f3d','a_0dbc6dc7d72f799c36'],'1000'),
 (254,'开源课程组件许可证核实','许可证以官方GitHub仓库为准，第三方介绍将MIT误写AGPL时撤回商授权风险判断；分别核对项目本体和LGPL等可选依赖，不将依赖许可证泛化到整个项目',['openMAIC','License','OpenMAIC'],['a_1f8253f6a446a0e8c6','a_7240f69f5d3dd15ae1'],'MIT'),
 (263,'Markdown转PDF表格解析排障','表格在列表缩进中可能被pandoc当列表文本；先把表格移出缩进并检查HTML是否形成table，再同时复核PDF和Word渲染，不能只看生成退出码',['PDF','pdf'],['a_a9a06c4b323d86c449','a_4f9192dae267b70419'],'表格'),
 (275,'分步骤操作指引编号校验','各步骤内的操作要点应重新从1编号，不能跨步骤延续；自动编号不在文本提取结果时将Word转PDF核对实际显示，别把提取不到当成无编号',[0],['a_af7515f6a43f2d0547','a_4cb60c9533127a1a56'],'每个步骤应该从 1 重新编号'),
 (277,'同一文档并行修改竞态规避','多个并行edit写同一文件可能最后一次覆盖前几次；报告修改成功不等于字节实际改变，改串行或统一一次处理并逐处验证；招聘资料虚构需与真实简历分开',[0,4,8],['a_199d49b12ad62add9a','a_f0532b973ca5198c4a'],'之前 6 个并行 edit 存在写回竞态'),
 (278,'docx-js数组序列化修复','正文生成无效零元素且列表消失时定位children参数；不能将数组整体push为嵌套子项，使用展开运算符并解包校验XML，后验列表内容',[0,1],['a_c1110feb4e1a9a076a'],'把整个数组直接 push 进 children 导致 docx-js 序列化出错'),
 (279,'DCF现金流公式和重算交叉核验','公式无报错不能证明DCF正确；折旧摊销加回核对源行和手算，LibreOffice缓存不回写则真实导出验算，等号开头标签需防被当公式',[0],['a_522f0bad0f0c84ffc5','a_fbaddf816872d7a5c1','a_82273f9963d174074d'],'FCF 中 D&A 加回行引用了错误的源行'),
 (325,'行业数据图表与文内引用一致性','不同预测口径相差数量级时使用对数坐标并明确口径；多张图片引用写同一文件要串行，避免并行编辑丢引用，逐一核对图与文件',['图','报告'],['a_8cbaf57aad6a0139d4','a_2e59cab13e3105a898'],'同一批并行编辑同一文件时发生了写入竞争'),
 (332,'PDF依赖解释器对应核验','导出依赖安装后仍不可导入时核对pip与python版本，使用目标解释器自身的pip安装，再检验生成PDF内容；重试与下载显示故障分别处理',['PDF','pdf','报告'],['a_4e4af1598169f88384'],'pip 和 python 版本不匹配'),
 (333,'报告制作依赖隔离排障','依赖已装却import失败先核对pip和实际运行python，使用python3 -m pip避免另一个解释器环境，不按缺库表象重复装全局包',['报告','新闻'],['a_3741a7cf447296037c'],'pip 和 python3 版本不匹配'),
 (335,'公众号含图正文发布','公众号草稿不能直接引用本地img路径；先上传配图到微信素材库替换永久URL，再创建草稿，发布与本地文件完成分别验收',['公众号','发布'],['a_4c1ac1c18493884311'],'必须先把配图上传到微信素材库换成永久 URL'),
 (348,'外部技能包适配企业个人技能规范','导入技能先核对中文name、触发description和必填市场字段，删除定价营销杂项；校验脚本未同步时按正文清单逐项人工核对并保留无法运行校验的边界',['技能','skill'],['a_eabeab4179e48ef4e1','a_ce27f87c5e8038d456'],'frontmatter name 改为中文「健身教练」'),
 (364,'文档自动化中的引号转义排障','Shell嵌套内容生成遇ASCII引号语法错误先核对字符编码，再改独立脚本文件执行，避免继续多层转义；产物通过结构校验后记录运行清单',['审阅','合同','文件'],['a_af91b0562c65cb6c1b','a_e3538a0818e6dbef60'],'Shell 转义问题，改为脚本文件方式执行'),
 (373,'财务PPT正负值图表验收','图表负值坐标与标签展示分开处理，不能将年份标签嵌进存在负值分支；金额显示保留适当小数并对源报告，修复后正值图和负值图分别验收',['PPT','ppt'],['a_25cfd8da168ac5da38','a_430ef6b759c42f2c46'],'坐标轴标签被错误嵌进了"存在负值"分支'),
 (385,'技能产物与共享目录核对','文件迁移先比较来源和目标MD5，相同内容跳过替换；缺失、已一致、内容不同分列，不因目录存在声称齐全，不能自开网关权限',['成果','替换','技能'],['a_69885fa2cebd360a4f','a_5578da1d49f2849e09'],'与源文件完全一致'),
 (388,'图片PPT错字与OCR误报区分','视觉服务429时用OCR临时核查，小字识别异常用TSV定位裁切，再用标准字体同字对照确认OCR自身误读；提示词原文错与渲染错分别修复',['PPT','ppt','图片'],['a_b0e6a6f7351ef0ff81','a_f46e238b9ce18bb2e0'],'标准字体渲染的"式"字 OCR 也读成"却/并"'),
 (389,'发光标题图片文字复核','发光大字OCR不稳时先二值化，再用tesseract TSV定位标题精确裁切复核；模型质检不可用仍可做本地校验，但不能把所有视觉美观也宣称验证',['新闻','图','PPT'],['a_6f870b58ed229b6bdd','a_cb329e230a342c4b3f'],'主标题是发光大字，OCR 识别不稳定'),
 (425,'PPTX富文本列表对象修复','渲染出现object Object时核查pptxgenjs富文本run结构；run不能嵌套paragraph，扁平化连续对象并将段落属性放段首run，另查页面几何越界',['PPT','ppt'],['a_a92a2483ede46d34af','a_6974a3aa9da9d57514'],'富文本 run 不能嵌套在 paragraph 对象里'),
 (448,'专家邀请角色与拒绝反馈修订','邀请失败后拆开学术评审、创业指导和活动背书角色，不把多种责任压在一个主席头衔；明确拒绝后收尾回复零索取、不解释、不再推销下一次合作',[13,14,15,16,19,20],['a_0c55e358168435c071','a_2eb8cb34a0d5a3676a'],'零索取、不解释、不提"以后还有机会"')
]
for ix,task,lesson,us,ais,q in new:
 r=by[ids[ix]];c=cards[ids[ix]]
 if isinstance(us[0],int):uis=[c['users'][j]['id'] for j in us if j<len(c['users'])]
 else:uis=[u['id'] for u in c['users'] if any(k.lower() in u['text'].lower() for k in us)][:5] or [c['users'][0]['id']]
 r.update(decision='KEEP',reason_code='METHOD_CONSTRAINT',reason='扩读未展示AI发现任务内具体诊断、纠正或处理条件',review_basis='expanded',candidates=[dict(task=task,lesson=lesson,user_ids=uis,assistant_ids=ais,evidence_quote=q,limitations=['原始时序未独立核验','附件与产物字节未提供','方法适用性及任务结果未独立验收'])])
for ix in expanded:by[ids[ix]]['review_basis']='expanded'
links={67:'a_6a62dcf76a99d33650',128:'a_a78d1621914deede58',205:'a_a098b8537cd80951e5',222:'a_05177c20889f15cafb',248:'a_35c58271f34cfcbc3e',257:'a_0799b66ea67a454d08',261:'a_d76e752dbacc8c6b7d',318:'a_c2c27f7bb980c2740f',350:'a_d0469d4b2a64e392b1',412:'a_00ab4537f058a5cce2',419:'a_290943295674f3370b',430:'a_0acf3ca5180b4e0534',438:'a_3c33bccf85a9d08426',447:'a_ae5231d62fd15d5a95',456:'a_b2bd19a58656c86357',469:'a_92c9d4d9aa462bd3c1'}
for ix,a in links.items():
 r=by[ids[ix]];r['candidates'][0]['assistant_ids'].append(a);r['review_basis']='expanded'
by[ids[194]]['candidates'][0]['evidence_quote']='从「学生毕业查重」转向「教师论文数据校对」'
by[ids[194]]['candidates'][0]['assistant_ids'].append('a_a91f3fbc9ddfc34a94');by[ids[194]]['review_basis']='expanded'
f.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('amended',len(rows),dict(collections.Counter(r['decision'] for r in rows)))
