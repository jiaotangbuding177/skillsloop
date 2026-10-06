import { readFileSync, writeFileSync } from "node:fs";
const msgs = JSON.parse(readFileSync("./messages_clean.json", "utf-8"));

// 主题分桶：正则命中即归桶（一条消息可归多桶）
const BUCKETS = {
  "合同/协议审查": /(合同|协议|NDA|保密协议|条款).*(审|看|查|改|风险|起草)|(审|审阅|审查|审核).*(合同|协议|NDA|条款)|补充协议/,
  "会议纪要/录音整理": /会议纪要|会议记录|录音|转写|谈话.*(总结|整理)|开会|例会|腾讯会议|会议室/,
  "翻译": /翻译|译成|翻译成|translate/i,
  "简历/招聘/职级": /简历|岗位|招聘|职级|薪酬序列|面试/,
  "招投标/售前": /招标|投标|标书|评分规则|客户画像|销售机会|售前|需求表|响应/,
  "投资/尽调/基金": /尽调|投资|基金|股权|BVI|合伙|交割|融资|领投|跟投|私募|信托|估值|增资|出资/,
  "PPT/路演材料": /PPT|ppt|幻灯|路演|汇报材料|演示文稿/,
  "报告/简报/公文": /简报|晨报|周报|日报|报告|公文|红头|请示|申请表|申报|汇报/,
  "表格/数据整理": /表格|Excel|excel|BOM|库存|对账|台账|清单|名册|花名册/,
  "企业/人物调研": /查一下|调研|检索|背景调查|工商|企查|公司介绍|个人介绍|办学|产线/,
  "写作/文案起草": /帮我写|写一份|起草|仿照|润色|改写|公众号|文案|推荐信|邮件/,
  "法务/合规咨询": /股东会|公司法|劳动法|工会法|法规|合规|法律风险|多数决|工商变更|注册/,
  "图片/文档处理": /图片|照片|截图|合并到一|扫描|OCR|提取.*文字/,
  "日程/提醒": /预定|预约|提醒|日程|日历|calendar/i,
  "技能/平台操作": /skill|技能|插件|安装|智能体|agent/i,
  "编程/开发": /代码|bug|报错|部署|python|python|脚本|程序|开发|接口|API/,
};
const REPEATABLE = /(按|照|仿|参照|参考).*(以前|之前|上次|模板|格式|样)|模板|上次一样|同样的|老样子/;

const stats = Object.fromEntries(Object.keys(BUCKETS).map(k => [k, { n: 0, users: new Set(), sessions: new Set(), samples: [] }]));
let repeatable = [];
for (const m of msgs) {
  for (const [k, re] of Object.entries(BUCKETS)) {
    if (re.test(m.content)) {
      const s = stats[k]; s.n++; s.users.add(m.phone); s.sessions.add(m.session_id);
      if (s.samples.length < 400) s.samples.push({ p: m.phone, t: m.created_at.slice(5, 16), c: m.content.slice(0, 160) });
    }
  }
  if (REPEATABLE.test(m.content)) repeatable.push({ p: m.phone, t: m.created_at.slice(5, 16), c: m.content.slice(0, 120) });
}
const rows = Object.entries(stats).sort((a, b) => b[1].n - a[1].n);
console.log(`总消息: ${msgs.length}  可复用信号(按以前/模板): ${repeatable.length}`);
console.log("\n=== 主题分桶（消息数 | 用户数 | 会话数）===");
for (const [k, s] of rows) console.log(`${k.padEnd(10)} ${String(s.n).padStart(5)} | ${String(s.users.size).padStart(3)} | ${String(s.sessions.size).padStart(4)}`);
writeFileSync("./bucket_samples.json", JSON.stringify(Object.fromEntries(rows.map(([k, s]) => [k, { n: s.n, users: [...s.users], samples: s.samples }])), null, 1));
writeFileSync("./repeatable_signals.json", JSON.stringify(repeatable, null, 1));
console.log("\nwrote bucket_samples.json, repeatable_signals.json");
