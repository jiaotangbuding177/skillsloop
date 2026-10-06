import { readFileSync, writeFileSync } from "node:fs";
const msgs = JSON.parse(readFileSync("./user_messages.json", "utf-8"));

const STRIP = [
  /^【个人助手设定】[\s\S]*?设定。\s*/,                    // persona 注入块
  /^\[[A-Z][a-z]{2} \d{4}-\d{2}-\d{2} \d{2}:\d{2} GMT\+8\]\s*/, // 时间戳包装
  /^请使用技能「[^」]+」协助当前任务。\s*/,                 // 技能调用包装
  /^请使用中文回复，除非用户明确使用其他语言。\s*/,
  /^以下内容来自用户当前选中的知识库文件[\s\S]*?不要编造。\s*/, // 知识库注入块
  /^以下内容来自用户当前选择的知识图谱节点[\s\S]*?召回实现。\s*/,
  /^\[PromptGuard\][\s\S]*$/,                            // 平台安全告警，整条丢弃
  /^\[OpenClaw runtime context\][\s\S]*$/,
];
function clean(c) { for (const re of STRIP) c = c.replace(re, "").trim(); return c; }

const SKILL_INVOKE = /请使用技能「([^」]+)」/;
const SKILL_INSTALL = /(?:安装技能|skills add|npx skills)[，,\s]*([^\n。;；]+)/;

const out = [], skillInvokes = {}, skillInstalls = [];
for (const m of msgs) {
  const raw = m.content;
  const inv = raw.match(SKILL_INVOKE);
  if (inv) skillInvokes[inv[1]] = (skillInvokes[inv[1]] ?? 0) + 1;
  const ins = raw.match(SKILL_INSTALL);
  if (ins) skillInstalls.push({ p: m.phone.slice(-4), t: m.created_at.slice(5, 16), what: ins[1].slice(0, 90) });
  const c = clean(raw);
  if (!c) continue; // 清洗后为空 = 纯平台注入，丢弃
  if (c.length < 4 && !/[a-zA-Z0-9]/.test(c)) continue;
  out.push({ ...m, content: c, had_skill_invoke: !!inv });
}
out.sort((a, b) => a.created_at.localeCompare(b.created_at));
writeFileSync("./messages_clean.json", JSON.stringify(out, null, 1));
const si = Object.entries(skillInvokes).sort((a, b) => b[1] - a[1]);
console.log(`清洗后: ${out.length} / ${msgs.length}`);
console.log(`\n=== 已有技能调用频次（请使用技能「X」）===`);
for (const [k, v] of si) console.log(String(v).padStart(4), k);
console.log(`\n=== 技能安装行为（最近 25 条）===`);
for (const x of skillInstalls.slice(-25)) console.log(`[${x.p} ${x.t}]`, x.what);
writeFileSync("./skill_invokes.json", JSON.stringify(si, null, 1));
writeFileSync("./skill_installs.json", JSON.stringify(skillInstalls, null, 1));
