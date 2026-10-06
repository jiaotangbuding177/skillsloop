from pathlib import Path
root=Path(__file__).resolve().parents[3]
reports=root/'research/reports'
source=reports/'022_论文概念文档.md'
text=source.read_text(encoding='utf-8')
anchor='### 8.7 复杂度、资源与实现边界\n'
record='''
构造数据的真实模型验收已完成：3条独立来源轨迹归纳为1个NEW，2条实际使用反馈合并为1个UPDATE；官方封装、个人采纳、组织审核和另一成员消费均通过。新输入的净额170/325及新增字段由宿主检查；35项软件测试通过。成功批次共5次派发、24次内部请求发起、306,250报告tokens；另有网络拒绝的1次派发/8次请求尝试，usage未知。没有同预算基线，不能由此推断成本下降或企业收益。[验收证据](../../enginering/demo/MULTITRACE_ACCEPTANCE.md)

'''
if record not in text:text=text.replace(anchor,anchor+record)
source.write_text(text,encoding='utf-8')
supp=reports/'025_technical_supplement.md'
supp.write_text('# 技术正文：多轨迹聚类与证据约束技能归纳\n\n'+text[text.index('## 八、'):text.index('## 十、')],encoding='utf-8')
assessment=text[text.index('## 十、'):text.index('## 附录A')].rstrip('-\n ')
(reports/'025_industry_technical_assessment.md').write_text('# WWW Industry技术评估与当前实现\n\n'+assessment+'\n',encoding='utf-8')
print('Canonical methods, assessment and evidence synchronized.')
