"use strict";
// ============================================================
// 知识库 API：博主/直播订阅、知识库管理
// 知识库在 biji.com 中称为"话题"（Topic）
// Base URL: https://get-notes.luojilab.com
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.KnowledgeAPI = void 0;
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
class KnowledgeAPI {
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
     * 将笔记添加到话题（知识库）
     * POST /voicenotes/web/topics/import/notes
     */
    async addNotesToTopic(topicId, noteIds) {
        const url = `${this.baseUrl}/voicenotes/web/topics/import/notes`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify({
                ids: noteIds,
                topic_id: topicId,
            }),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 从话题中删除笔记
     * DELETE /voicenotes/web/topics/{topicId}/notes/{noteId}
     */
    async removeNoteFromTopic(topicId, noteId) {
        const url = `${this.baseUrl}/voicenotes/web/topics/${topicId}/notes/${noteId}`;
        const res = await fetch(url, {
            method: "DELETE",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 在话题中创建笔记
     * POST /voicenotes/web/topics/notes
     */
    async createNoteInTopic(body) {
        const url = `${this.baseUrl}/voicenotes/web/topics/notes`;
        const res = await fetch(url, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify(body),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 获取博主列表
     * GET /v1/web/follow/list?topic_id=-1&topic_id_alias=
     */
    async getBloggerList(topicAlias = "") {
        const url = `${this.baseUrl}/v1/web/follow/list?topic_id=-1&topic_id_alias=${topicAlias}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 获取博主内容列表
     * GET /v1/web/follow/account/posts?follow_id=&page=&page_size=
     */
    async getBloggerPosts(followId, page = 1, pageSize = 20) {
        const params = new URLSearchParams();
        params.set("follow_id", followId);
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        const url = `${this.baseUrl}/v1/web/follow/account/posts?${params.toString()}`;
        const res = await fetch(url, {
            method: "GET",
            headers: this.headers,
        });
        return (0, utils_1.parseWebResponse)(res);
    }
    /**
     * 取消关注博主
     * DELETE /v1/web/follow/delete
     */
    async unfollowBlogger(followIds) {
        const url = `${this.baseUrl}/v1/web/follow/delete`;
        const res = await fetch(url, {
            method: "DELETE",
            headers: this.headers,
            body: JSON.stringify({ follow_ids: followIds }),
        });
        return (0, utils_1.parseWebResponse)(res);
    }
}
exports.KnowledgeAPI = KnowledgeAPI;
//# sourceMappingURL=knowledge.js.map