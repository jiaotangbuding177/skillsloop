import { readFileSync, writeFileSync, readdirSync } from "node:fs";
const MASK_PATTERNS = [
  [/\+?861[3-9]\d{9}/g, (m) => "***" + m.slice(-4)],                    // +86 手机号
  [/(?<!\d)1[3-9]\d{9}(?!\d)/g, (m) => "***" + m.slice(-4)],            // 裸手机号
  [/(?<!\d)\d{17}[\dXx](?!\d)/g, "***ID***"],                           // 18 位身份证
  [/(?<!\d)\d{15}(?!\d)/g, "***ID***"],                                 // 15 位身份证
  [/(?<!\d)\d{13,19}(?!\d)/g, "***CARD***"],                            // 银行卡等长数字
  [/sk-[A-Za-z0-9_-]{8,}/g, "***KEY***"],
  [/Bearer\s+[A-Za-z0-9._-]{8,}/gi, "Bearer ***"],
  [/\b(api[_-]?key|apikey|password|passwd|secret|token|access[_-]?key)(["'\s:=]+)[^\s"'，。;；]{6,}/gi, "$1$2***"],
  [/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, "***@***"],       // 邮箱
  [/\b[A-Fa-f0-9]{32,}\b/g, "***HEX***"],                               // 长十六进制
];
function maskStr(s) { let r = s; for (const [re, rep] of MASK_PATTERNS) r = r.replace(re, rep); return r; }
function walk(v, key) {
  if (typeof v === "string") {
    if (key === "phone" || key === "providerUserId") return "***" + v.slice(-4);
    return maskStr(v);
  }
  if (Array.isArray(v)) return v.map((x) => walk(x));
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x, k)]));
  return v;
}
for (const f of readdirSync(".").filter((f) => f.endsWith(".json"))) {
  const data = JSON.parse(readFileSync(f, "utf-8"));
  writeFileSync(f, JSON.stringify(walk(data), null, 1));
  console.log("masked", f);
}
// 校验：不应再有明文手机号
const bad = [];
for (const f of readdirSync(".").filter((f) => f.endsWith(".json"))) {
  if (/[1][3-9]\d{9}/.test(readFileSync(f, "utf-8").replace(/\d{5,}/g, ""))) continue;
}
console.log("verify: no raw 11-digit CN mobile remains:", !readdirSync(".").some((f) => f.endsWith(".json") && /(?<!\d)1[3-9]\d{9}(?!\d)/.test(readFileSync(f, "utf-8"))));
