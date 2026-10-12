"use strict";
// ============================================================
// 笔记 API：列表、详情、创建、更新、删除、搜索
// Base URL: https://get-notes.luojilab.com
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotesAPI = void 0;
const utils_1 = require("../utils");
/**
 * 将多行文本构建为 ProseMirror doc JSON 字符串
 * 每行一个 paragraph，空行渲染为空段落，确保换行正确显示
 * 注意：得到笔记使用 camelCase 节点名，paragraph 需要 textAlign attrs
 */
function buildProseMirrorDoc(text) {
    const lines = text.split("\n");
    const content = lines.map((line) => ({
        type: "paragraph",
        attrs: { textAlign: null },
        content: line ? [{ type: "text", text: line }] : [],
    }));
    return JSON.stringify({ type: "doc", content });
}
/** 构建 paragraph 节点 */
function p(text) {
    return { type: "paragraph", attrs: { textAlign: null }, content: text ? [{ type: "text", text }] : [] };
}
/** 构建 tableCell 节点 */
function cell(text) {
    return { type: "tableCell", attrs: { colspan: 1, rowspan: 1, colwidth: null }, content: [p(text)] };
}
/** 构建 tableRow 节点 */
function row(...cells) {
    return { type: "tableRow", content: cells.map(cell) };
}
/**
 * 构建 ProseMirror 表格 doc JSON 字符串
 * headers: 表头列名数组，data: 二维数据数组（每行是一个数组）
 * 节点名使用 camelCase（tableRow/tableCell），匹配得到笔记的 ProseMirror schema
 *
 * 使用示例：
 *   buildProseMirrorTable(["名称", "做法"], [
 *     ["米饭", "米水比1:1.2"],
 *     ["馒头", "中筋面粉500g..."],
 *   ])
 * 生成包含两个 block 的数组：[标题段落, 表格]，可直接拼接或插入到 doc.content 中
 */
function buildTableBlocks(headers, data) {
    const headerRow = row(...headers);
    const dataRows = data.map((r) => row(...r));
    return [{ type: "table", content: [headerRow, ...dataRows] }];
}
/** 构建请求头 */
function buildHeaders(token, csrfToken, deviceId) {
    return {
        "Authorization": `Bearer ${token}`,
        "Xi-Csrf-Token": csrfToken,
        "x-d": deviceId,
        "Xi-App-Client-Source": "getnote",
        "Content-Type": "application/json",
        "Origin": "https://www.biji.com",
    };
}
class NotesAPI {
    constructor(baseUrl, token, csrfToken, deviceId) {
        this.baseUrl = baseUrl;
        this.token = token;
        this.csrfToken = csrfToken;
        this.deviceId = deviceId;
    }
    /** 更新凭证 */
    updateCredentials(token, csrfToken, deviceId) {
        this.token = token;
        this.csrfToken = csrfToken;
        this.deviceId = deviceId;
    }
    get headers() {
        return buildHeaders(this.token, this.csrfToken, this.deviceId);
    }
    // ==================== 笔记列表 ====================
    /**
     * 获取笔记列表
     * GET /voicenotes/web/notes?limit=&since_id=&sort=
     */
    async list(options = {}) {
        const params = new URLSearchParams();
        if (options.limit)
            params.set("limit", String(options.limit));
        if (options.since_id)
            params.set("since_id", options.since_id);
        if (options.sort)
            params.set("sort", options.sort);
        const url = `${this.baseUrl}/voicenotes/web/notes?${params.toString()}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 笔记详情 ====================
    /**
     * 获取笔记详情
     * GET /voicenotes/web/notes/{noteId}
     */
    async detail(noteId) {
        const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 创建笔记 ====================
    /**
     * 创建笔记
     * POST /voicenotes/web/notes
     */
    async create(body) {
        const url = `${this.baseUrl}/voicenotes/web/notes`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify(body),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 创建文本笔记（便捷方法）
     * 自动将换行符拆分为独立段落，确保 ProseMirror 正确渲染
     */
    async createText(title, text, tags) {
        const jsonContent = buildProseMirrorDoc(text);
        return this.create({
            note_type: "plain_text",
            title,
            json_content: jsonContent,
            tags,
            source: "web",
            entry_type: "manual",
        });
    }
    // ==================== 更新笔记 ====================
    /**
     * 更新笔记
     * PUT /voicenotes/web/notes/{noteId}
     * 使用 prime_id 或 note_id 定位笔记
     */
    async update(noteId, body) {
        const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}`;
        const res = await fetch(url, {
            method: "PUT",
            headers: this.headers,
            body: JSON.stringify(body),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 更新笔记标题和内容（便捷方法）
     */
    async updateContent(noteId, title, text, version, tags) {
        const jsonContent = buildProseMirrorDoc(text);
        const body = {
            note_id: noteId,
            title,
            json_content: jsonContent,
            source: "web",
            entry_type: "manual",
        };
        if (version !== undefined)
            body.version = version;
        if (tags !== undefined)
            body.tags = tags;
        return this.update(noteId, body);
    }
    // ==================== 删除笔记 ====================
    /**
     * 删除笔记（移入回收站）
     * DELETE /voicenotes/web/notes/{noteId}
     */
    async delete(noteId) {
        const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}`;
        const res = await fetch(url, {
            method: "DELETE",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 搜索笔记 ====================
    /**
     * 搜索笔记
     * GET /voicenotes/web/notes/search?page=&page_size=&query=
     */
    async search(query, page = 1, pageSize = 10) {
        const params = new URLSearchParams();
        params.set("query", query);
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        const url = `${this.baseUrl}/voicenotes/web/notes/search?${params.toString()}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 回收站 ====================
    /**
     * 获取回收站列表
     * GET /voicenotes/web/notes/recycle/
     */
    async recycleBin(page = 1, pageSize = 20) {
        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        const url = `${this.baseUrl}/voicenotes/web/notes/recycle/?${params.toString()}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 回收站搜索
     * GET /voicenotes/web/notes/recycle/search?query=
     */
    async searchRecycleBin(query, page = 1, pageSize = 20) {
        const params = new URLSearchParams();
        params.set("query", query);
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        const url = `${this.baseUrl}/voicenotes/web/notes/recycle/search?${params.toString()}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 回收站批量操作（恢复/彻底删除）
     * POST /voicenotes/web/notes/recycle/op/batch
     */
    async recycleBinBatchOp(noteIds, action) {
        const url = `${this.baseUrl}/voicenotes/web/notes/recycle/op/batch`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify({ note_ids: noteIds, action }),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 清空回收站
     * POST /voicenotes/web/notes/recycle/op/clear
     */
    async clearRecycleBin() {
        const url = `${this.baseUrl}/voicenotes/web/notes/recycle/op/clear`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify({}),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 笔记数量 ====================
    /**
     * 获取笔记总数
     * GET /voicenotes/web/notes/count
     */
    async count() {
        const url = `${this.baseUrl}/voicenotes/web/notes/count`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    // ==================== 获取所有笔记（自动翻页）====================
    /**
     * 获取所有笔记（自动翻页直到没有更多数据）
     */
    async listAll(pageSize = 50) {
        let allItems = [];
        let sinceId = "";
        while (true) {
            const result = await this.list({
                limit: pageSize,
                since_id: sinceId || undefined,
                sort: "create_desc",
            });
            allItems = allItems.concat(result.list);
            if (result.list.length < pageSize) {
                break;
            }
            // 使用最后一条的 id 作为下一页的 since_id
            sinceId = result.list[result.list.length - 1].id;
        }
        return {
            total_items: allItems.length,
            list: allItems,
        };
    }
}
exports.NotesAPI = NotesAPI;
//# sourceMappingURL=notes.js.map