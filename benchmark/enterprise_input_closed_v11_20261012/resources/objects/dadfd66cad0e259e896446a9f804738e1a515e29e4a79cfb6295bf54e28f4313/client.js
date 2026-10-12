"use strict";
// ============================================================
// Get笔记 Web SDK 主客户端
// 通过 JWT Bearer Token 认证（浏览器 Cookie 登录后获取）
// Base URL: https://get-notes.luojilab.com
// 支持 refresh_token 自动刷新
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.GetNoteClient = void 0;
const notes_1 = require("./api/notes");
const search_1 = require("./api/search");
const tags_1 = require("./api/tags");
const knowledge_1 = require("./api/knowledge");
const auth_1 = require("./api/auth");
class GetNoteClient {
    constructor(config) {
        this.auth = null;
        this.baseUrl = config.baseUrl || "https://get-notes.luojilab.com";
        this.token = config.token;
        this.csrfToken = config.csrfToken;
        this.deviceId = config.deviceId;
        // 初始化认证模块（如果提供了 refresh_token）
        if (config.refreshToken) {
            const tokenInfo = {
                token: config.token,
                token_expire_at: config.tokenExpireAt || 0,
                refresh_token: config.refreshToken,
                refresh_token_expire_at: config.refreshTokenExpireAt || 0,
            };
            this.auth = new auth_1.AuthAPI(config.authBaseUrl, tokenInfo, (newInfo) => this._onTokenRefreshed(newInfo));
        }
        this.notes = new notes_1.NotesAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
        this.search = new search_1.SearchAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
        this.tags = new tags_1.TagsAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
        this.knowledge = new knowledge_1.KnowledgeAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
    }
    /** token 刷新后同步所有子 API */
    _onTokenRefreshed(info) {
        this.token = info.token;
        this.notes.updateCredentials(info.token, this.csrfToken, this.deviceId);
        this.search.updateCredentials(info.token, this.csrfToken, this.deviceId);
        this.tags.updateCredentials(info.token, this.csrfToken, this.deviceId);
        this.knowledge.updateCredentials(info.token, this.csrfToken, this.deviceId);
    }
    /** 更新凭证（热切换） */
    setCredentials(token, csrfToken, deviceId, refreshToken, tokenExpireAt, refreshTokenExpireAt) {
        this.token = token;
        this.csrfToken = csrfToken;
        this.deviceId = deviceId;
        if (refreshToken) {
            const tokenInfo = {
                token,
                token_expire_at: tokenExpireAt || 0,
                refresh_token: refreshToken,
                refresh_token_expire_at: refreshTokenExpireAt || 0,
            };
            if (this.auth) {
                this.auth.setTokenInfo(tokenInfo);
            }
            else {
                this.auth = new auth_1.AuthAPI(undefined, tokenInfo, (newInfo) => this._onTokenRefreshed(newInfo));
            }
        }
        this.notes.updateCredentials(token, csrfToken, deviceId);
        this.search.updateCredentials(token, csrfToken, deviceId);
        this.tags.updateCredentials(token, csrfToken, deviceId);
        this.knowledge.updateCredentials(token, csrfToken, deviceId);
    }
    /**
     * 确保 token 有效（如已过期或即将过期则自动刷新）
     * 在每次 API 调用前调用此方法
     */
    async ensureToken() {
        if (!this.auth)
            return;
        if (this.auth.needsRefresh()) {
            const info = await this.auth.refreshToken();
            // _onTokenRefreshed 回调已更新子 API
        }
    }
    /** 检查 refresh_token 是否已过期 */
    isLoginValid() {
        if (!this.auth)
            return true; // 没有 auth 模块时不判断
        return !this.auth.isRefreshTokenExpired();
    }
    /** 获取当前 token 信息 */
    getTokenInfo() {
        return this.auth?.getTokenInfo() || null;
    }
    /** 主动刷新 token */
    async refreshToken() {
        if (!this.auth)
            throw new Error("未配置 refresh_token");
        return this.auth.refreshToken();
    }
}
exports.GetNoteClient = GetNoteClient;
//# sourceMappingURL=client.js.map