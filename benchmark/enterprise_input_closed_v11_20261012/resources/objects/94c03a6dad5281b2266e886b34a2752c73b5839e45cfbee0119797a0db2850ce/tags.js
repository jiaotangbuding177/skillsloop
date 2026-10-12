"use strict";
// ============================================================
// 标签 API：列表、添加、删除
// Base URL: https://get-notes.luojilab.com
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.TagsAPI = void 0;
const utils_1 = require("../utils");
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
class TagsAPI {
    constructor(baseUrl, token, csrfToken, deviceId) {
        this.baseUrl = baseUrl;
        this.token = token;
        this.csrfToken = csrfToken;
        this.deviceId = deviceId;
    }
    updateCredentials(token, csrfToken, deviceId) {
        this.token = token;
        this.csrfToken = csrfToken;
        this.deviceId = deviceId;
    }
    get headers() {
        return buildHeaders(this.token, this.csrfToken, this.deviceId);
    }
    /**
     * 获取标签列表
     * GET /voicenotes/web/tags?page_size=
     */
    async list(pageSize = 200) {
        const url = `${this.baseUrl}/voicenotes/web/tags?page_size=${pageSize}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res).then(r => r.data);
    }
    /**
     * 为笔记添加标签
     * POST /voicenotes/web/notes/{noteId}/tags
     */
    async add(noteId, tags) {
        const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}/tags`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify({ tags }),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 删除笔记标签
     * DELETE /voicenotes/web/notes/{noteId}/tags
     */
    async remove(noteId, tagIds) {
        const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}/tags`;
        const res = await fetch(url, {
            method: "DELETE",
            headers: this.headers,
            body: JSON.stringify({ tag_ids: tagIds }),
        });
        await (0, utils_1.parseWebResponse)(res);
    }
}
exports.TagsAPI = TagsAPI;
//# sourceMappingURL=tags.js.map