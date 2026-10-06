import json,pathlib,collections
p=pathlib.Path(__file__).parent;ids=json.loads((p/'assigned_ids.json').read_text(encoding='utf-8'));f=p/'tail17_19_review_labels.json';rows=json.loads(f.read_text(encoding='utf-8'));by={r['session_id']:r for r in rows}
changes={
 404:('a_3ea6929e09072443f6','原稿约 800 词，按 145 词/分钟要讲 5 分 30 秒'),
 406:('a_04820a40cf1fefd738','之前把横剖面和纵向的轴系/螺旋桨硬塞进一张图，几何上自相矛盾'),
 409:('a_9064e9e6f7dd49cec2','公司方陈述，未经审计验证'),
 410:('a_ff7d1560b996254c55','每个优势固定三段式：**我们怎么做的 → 别人怎么做的 → 凭据**'),
 412:('a_cd501d0784856aa792','图片块类型是 **27**（不是 28），且 image 必须为空 `{}`'),
 415:('a_cb9d7c005f11b32dda','飞书文档 API 不支持直接创建「分隔线」块'),
 416:('a_739ddaf678a1763c5a','发现 1 个缺字：正文中“張豈明”的繁体“豈”不在 GB2312 字库'),
 418:('a_508411e5a998372339','最……""最对口""之最"这类隐含横向比较的措辞'),
 419:('a_aca5969e1b869e0884','因为每次编辑都会轻微重渲染全图'),
 424:('a_07f29511dd44329c4a','控股股东变更与募投项目可行性没有因果'),
 426:('a_376499d86d80f6bbf9','不可直接比对'),
 434:('a_8bd1c5991d49e478e4','我前面说的是最坏情况下的推演，不是决定'),
 440:('a_7ed0a4b16ed37575d4','编号后必须有个空格'),
 447:('a_6180432b9459bf0d41','所有人体数据与 IIT 均来自天然菌，工程菌尚无人体数据'),
 450:('a_c0c1fb7e522bc4694d','诉讼 + 仲裁并存，且 7.2 **连仲裁机构名称都没有**'),
 452:('a_ebe2f3ca6ae6e68d2f','先留证再卸载**，切断下载与外联'),
 460:('a_88c1d88b1f5e2260b6','换成大肠杆菌（EcN 底盘），你的 Cpf1 编辑策略/载体/转化要改哪些'),
 469:('a_7814e5d33102525e1d','源文件里的组名是**合并单元格**，读取时只有第一格有值'),
 472:('a_0edf29ff210e305079','平台没有图生视频接口（zzz4ai 只支持图片）'),
 474:('a_896cda69bcdaf0d4b6','回程 5 天，都很松')
}
for ix,(a,q) in changes.items():
 r=by[ids[ix]];c=r['candidates'][0];c['assistant_ids']=[a];c['evidence_quote']=q;r['review_basis']='expanded'
for ix in [401,422,468]:by[ids[ix]]['review_basis']='expanded'
by[ids[426]]['candidates'][0]['evidence_quote']='凡"报告期内"金额/人数（关联交易、期间费用、员工社保人数）**不可直接比对**'
by[ids[440]]['candidates'][0]['evidence_quote']='markdown 里**编号后必须有个空格**才算列表项'
f.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('frozen tail',len(rows),dict(collections.Counter(r['decision'] for r in rows)))
