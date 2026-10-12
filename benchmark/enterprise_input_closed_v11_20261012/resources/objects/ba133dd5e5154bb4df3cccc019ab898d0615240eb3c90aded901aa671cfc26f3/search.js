"use strict";
// ============================================================
// 搜索 API：笔记搜索
// Base URL: https://get-notes.luojilab.com
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.SearchAPI = void 0;
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
class SearchAPI {
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
}
exports.SearchAPI = SearchAPI;
//# sourceMappingURL=search.js.map