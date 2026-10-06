/**
 * 中科优势组织用户使用数据拉取（只读）
 * 输出 JSON 文件到当前目录：
 *   - members.json     成员列表（含活跃度）
 *   - sessions.json    组织成员全部会话（title/时间/消息数）
 *   - user_messages.json 用户原始消息（UUID 副本，去 trusted）
 *   - tool_usage.json  工具调用频次聚合
 */
import { execSync } from "node:child_process";

const PG_PATH = "C:/Users/MR/.agents/skills/iw-debug/scripts/node_modules/pg/lib/index.js";
const pgModule = await import(`file://${PG_PATH}`);
const Client = pgModule.default?.Client ?? pgModule.Client;

// 连接串取自 db-inspect 同源环境变量/默认值
const ENV_PROD =
  process.env.IW_DB_PROD ??
  "postgresql://[REDACTED_DATABASE_CREDENTIAL]@pgm-uf69u232ir6c2312po.pg.rds.aliyuncs.com:5432/insight_weaver_prod?schema=public";

const ORG_ID = "0d2b87b4-0be4-4ebe-89f3-87fcfc7798ef"; // 中科优势

const client = new Client({ connectionString: ENV_PROD });
await client.connect();
console.log("connected");

const ORG_MEMBERS = `SELECT "userId" FROM enterprise_memberships WHERE "enterpriseId" = '${ORG_ID}' AND "isDeleted" = false`;

// 1. 成员 + 活跃度
const members = await client.query(`
  SELECT ui."providerUserId" AS phone, em.role, em."userId",
    (SELECT COUNT(*) FROM zclaw_sessions s WHERE s."userId" = em."userId" AND s."isDeleted" = false) AS sessions,
    (SELECT COUNT(*) FROM zclaw_messages m JOIN zclaw_sessions s ON s.id = m."sessionId"
      WHERE s."userId" = em."userId" AND m."isDeleted" = false AND m.role = 'user' AND m.id NOT LIKE 'conv_%') AS user_msgs,
    (SELECT MAX(s."lastMessageAt") FROM zclaw_sessions s WHERE s."userId" = em."userId" AND s."isDeleted" = false) AS last_active
  FROM enterprise_memberships em
  LEFT JOIN user_identities ui ON ui."userId" = em."userId" AND ui.provider = 'phone' AND ui."isDeleted" = false
  WHERE em."enterpriseId" = '${ORG_ID}' AND em."isDeleted" = false
  ORDER BY 5 DESC NULLS LAST`);

// 2. 会话（组织成员的全部非删会话）
const sessions = await client.query(`
  SELECT s.id, s."userId" AS user_id, ui."providerUserId" AS phone, s.title, s.status,
    s."createdAt" AS created_at, s."lastMessageAt" AS last_message_at,
    (SELECT COUNT(*) FROM zclaw_messages m WHERE m."sessionId" = s.id AND m."isDeleted" = false AND m.role = 'user' AND m.id NOT LIKE 'conv_%') AS user_msgs
  FROM zclaw_sessions s
  JOIN user_identities ui ON ui."userId" = s."userId" AND ui.provider = 'phone' AND ui."isDeleted" = false
  WHERE s."userId" IN (${ORG_MEMBERS}) AND s."isDeleted" = false
  ORDER BY s."createdAt" ASC`);

// 3. 用户原始消息（UUID 副本 = 无系统前缀）
const messages = await client.query(`
  SELECT m.id, m."sessionId" AS session_id, s."userId" AS user_id, ui."providerUserId" AS phone,
    m.content, m."createdAt" AS created_at
  FROM zclaw_messages m
  JOIN zclaw_sessions s ON s.id = m."sessionId"
  LEFT JOIN user_identities ui ON ui."userId" = s."userId" AND ui.provider = 'phone' AND ui."isDeleted" = false
  WHERE s."userId" IN (${ORG_MEMBERS}) AND m."isDeleted" = false AND m.role = 'user' AND m.id NOT LIKE 'conv_%'
  ORDER BY m."createdAt" ASC`);

// 4. 工具调用频次（tool 消息 content 格式：[toolName]\n{JSON}）
const tools = await client.query(`
  SELECT LEFT(m.content, 60) AS head, COUNT(*) AS cnt
  FROM zclaw_messages m
  JOIN zclaw_sessions s ON s.id = m."sessionId"
  WHERE s."userId" IN (${ORG_MEMBERS}) AND m."isDeleted" = false AND m.role = 'tool' AND m.id NOT LIKE 'conv_%'
  GROUP BY 1 ORDER BY cnt DESC LIMIT 40`);

await client.end();

const { writeFileSync } = await import("node:fs");
const out = (name, data) => {
  writeFileSync(new URL(`./${name}`, import.meta.url), JSON.stringify(data, null, 1));
  console.log(`wrote ${name}`);
};
out("members.json", members.rows);
out("sessions.json", sessions.rows);
out("user_messages.json", messages.rows);
out("tool_usage.json", tools.rows);
console.log(`members=${members.rows.length} sessions=${sessions.rows.length} messages=${messages.rows.length}`);
