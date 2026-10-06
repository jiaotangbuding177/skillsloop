/**
 * Get笔记 Web SDK 使用示例
 * 
 * 运行前设置环境变量：
 *   export GETNOTE_TOKEN="eyJ..."
 *   export GETNOTE_CSRF="jtrG..."
 *   export GETNOTE_DEVICE_ID="e152..."
 * 
 * 运行：
 *   npx tsx examples/basic.ts
 */

import { GetNoteClient } from "../src/index";

const token = process.env.GETNOTE_TOKEN || "";
const csrfToken = process.env.GETNOTE_CSRF || "";
const deviceId = process.env.GETNOTE_DEVICE_ID || "";

if (!token || !csrfToken || !deviceId) {
  console.error("请设置环境变量: GETNOTE_TOKEN, GETNOTE_CSRF, GETNOTE_DEVICE_ID");
  process.exit(1);
}

const client = new GetNoteClient({ token, csrfToken, deviceId });

async function main() {
  // 1. 获取笔记列表
  console.log("=== 笔记列表 ===");
  const list = await client.notes.list({ limit: 5, sort: "create_desc" });
  console.log(`共 ${list.total_items} 条笔记`);
  for (const note of list.list.slice(0, 3)) {
    console.log(`  - [${note.note_id}] ${note.title} (${note.date_str})`);
  }

  // 2. 获取笔记详情
  if (list.list.length > 0) {
    const noteId = list.list[0].note_id;
    console.log(`\n=== 笔记详情: ${noteId} ===");
    const detail = await client.notes.detail(noteId);
    console.log(`  标题: ${detail.title}`);
    console.log(`  类型: ${detail.note_type}`);
    console.log(`  标签: ${detail.tags.join(", ") || "无"}`);
    console.log(`  创建时间: ${detail.created_at}`);
  }

  // 3. 搜索笔记
  console.log("\n=== 搜索笔记 ===");
  const searchResult = await client.notes.search("学习", 1, 5);
  console.log(`搜索结果: ${searchResult.total} 条`);
  for (const note of searchResult.list.slice(0, 3)) {
    console.log(`  - ${note.title}`);
  }

  // 4. 获取标签列表
  console.log("\n=== 标签列表 ===");
  const tags = await client.tags.list(20);
  console.log(`共 ${tags.total} 个标签`);
  for (const tag of tags.items.slice(0, 5)) {
    console.log(`  - ${tag.name} (${tag.note_count}条笔记)`);
  }

  // 5. 获取笔记总数
  const count = await client.notes.count();
  console.log(`\n=== 笔记总数: ${count.total} ===");

  // 6. 创建文本笔记（注释掉以免误操作）
  // const newNote = await client.notes.createText("测试标题", "测试内容");
  // console.log(`创建笔记: ${newNote.note_id}`);

  // 7. 更新笔记（注释掉以免误操作）
  // const updated = await client.notes.updateContent(
  //   "1912355455074697832",
  //   "更新后的标题",
  //   "更新后的内容"
  // );
  // console.log(`更新成功: ${updated.note_id}`);
}

main().catch(console.error);
