import json
from pathlib import Path

p = Path(__file__).parent
ids = json.loads((p / 'assigned_ids.json').read_text(encoding='utf-8'))
rows = json.loads((p / 'review_labels.json').read_text(encoding='utf-8'))
labels = {r['session_id']: r for r in rows}
quotes = {
    7: 'index.md 中的条目名称与实际 wiki 文件名不一致',
    32: '属于稳定参考资料，内容本身不会过时',
    108: '搜狗 ssf 皮肤格式**不支持运行时代码**',
    179: '已经卖了1000个账号，说明**需求验证已经过了**',
    254: '那是第三方转载站（openmaic.io）的错误信息',
    263: '表格在列表项里做了缩进，pandoc 把它当成了列表内容而不是表格',
    385: '我逐文件做了 MD5 校验——**与源文件完全一致**',
}
for ix, quote in quotes.items():
    labels[ids[ix]]['candidates'][0]['evidence_quote'] = quote
(p / 'review_labels.json').write_text(json.dumps([labels[i] for i in ids], ensure_ascii=False, indent=2), encoding='utf-8')
print('Fixed seven evidence quotes.')
