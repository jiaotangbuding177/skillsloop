const PG_PATH = "C:/Users/MR/.agents/skills/iw-debug/scripts/node_modules/pg/lib/index.js";
const pgModule = await import(`file://${PG_PATH}`);
const Client = pgModule.default?.Client ?? pgModule.Client;
const ENV_PROD = process.env.IW_DB_PROD ?? "postgresql://[REDACTED_DATABASE_CREDENTIAL]@pgm-uf69u232ir6c2312po.pg.rds.aliyuncs.com:5432/insight_weaver_prod?schema=public";
const ORG_ID = "0d2b87b4-0be4-4ebe-89f3-87fcfc7798ef";
const client = new Client({ connectionString: ENV_PROD });
await client.connect();
const rows = await client.query(`
  SELECT m.id, m."sessionId" AS session_id, ui."providerUserId" AS phone,
    m.content, m."createdAt" AS created_at
  FROM zclaw_messages m
  JOIN zclaw_sessions s ON s.id = m."sessionId"
  LEFT JOIN user_identities ui ON ui."userId" = s."userId" AND ui.provider = 'phone' AND ui."isDeleted" = false
  WHERE s."userId" IN (SELECT "userId" FROM enterprise_memberships WHERE "enterpriseId" = '${ORG_ID}' AND "isDeleted" = false)
    AND m."isDeleted" = false AND m.role = 'user' AND m.id LIKE 'conv_%'
  ORDER BY m."createdAt" ASC`);
await client.end();
const PREFIX_RE = /^请使用中文回复，除非用户明确使用其他语言。\s*/;
const msgs = rows.rows.map(r => ({ ...r, content: r.content.replace(PREFIX_RE, "").trim() }));
const { writeFileSync } = await import("node:fs");
writeFileSync(new URL("./user_messages.json", import.meta.url), JSON.stringify(msgs, null, 1));
console.log(`trusted user messages: ${msgs.length}`);
const lens = msgs.map(m => m.content.length).sort((a,b)=>a-b);
console.log(`len p50=${lens[Math.floor(lens.length*0.5)]} p90=${lens[Math.floor(lens.length*0.9)]} max=${lens[lens.length-1]}`);
