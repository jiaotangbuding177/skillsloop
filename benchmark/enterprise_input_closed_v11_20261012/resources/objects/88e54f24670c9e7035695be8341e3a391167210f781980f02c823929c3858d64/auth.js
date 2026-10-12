"use strict";
// ============================================================
// 认证 API：Token 刷新
// Base URL: https://ddll-api.trytalks.com
// 通过 refresh_token 换取新的 JWT access_token
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuthAPI = void 0;
const utils_1 = require("../utils");
class AuthAPI {
    constructor(authBaseUrl = "https://ddll-api.trytalks.com", tokenInfo, onTokenRefreshed) {
        this.tokenInfo = null;
        this.refreshPromise = null;
        this.authBaseUrl = authBaseUrl;
        this.tokenInfo = tokenInfo || null;
        this.onTokenRefreshed = onTokenRefreshed;
    }
    /** 更新本地 token 信息 */
    setTokenInfo(info) {
        this.tokenInfo = info;
    }
    /** 获取当前 token 信息 */
    getTokenInfo() {
        return this.tokenInfo;
    }
    /**
     * 判断是否需要刷新 token
     * 当 token 过期时间距离现在不足 5 分钟时，返回 true
     */
    needsRefresh() {
        if (!this.tokenInfo)
            return false;
        const now = Math.floor(Date.now() / 1000);
        // 提前 5 分钟（300秒）刷新
        return now + 300 >= this.tokenInfo.token_expire_at;
    }
    /**
     * 判断 refresh_token 是否已过期
     */
    isRefreshTokenExpired() {
        if (!this.tokenInfo)
            return true;
        const now = Math.floor(Date.now() / 1000);
        return now >= this.tokenInfo.refresh_token_expire_at;
    }
    /**
     * 刷新 token
     * POST /account/v2/web/user/auth/refresh
     * Body: { refresh_token: "..." }
     * 返回: { h: { c: 0 }, c: { success: true, token: { ... } } }
     *
     * 注意：并发调用时只发一次请求
     */
    async refreshToken() {
        if (!this.tokenInfo?.refresh_token) {
            throw new Error("RefreshTokenNotFound: 没有 refresh_token，无法刷新");
        }
        if (this.isRefreshTokenExpired()) {
            throw new Error("RefreshTokenExpired: refresh_token 已过期，请重新登录");
        }
        // 防止并发重复刷新
        if (this.refreshPromise) {
            return this.refreshPromise;
        }
        this.refreshPromise = this._doRefresh();
        try {
            const result = await this.refreshPromise;
            return result;
        }
        finally {
            this.refreshPromise = null;
        }
    }
    async _doRefresh() {
        const url = `${this.authBaseUrl}/account/v2/web/user/auth/refresh`;
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: this.tokenInfo.refresh_token }),
        });
        const data = await (0, utils_1.parseWebResponse)(res);
        if (!data.success || !data.token) {
            throw new Error("RefreshTokenInvalid: 刷新返回无效数据");
        }
        const newInfo = {
            token: data.token.token,
            token_expire_at: data.token.token_expire_at,
            refresh_token: data.token.refresh_token,
            refresh_token_expire_at: data.token.refresh_token_expire_at,
        };
        this.tokenInfo = newInfo;
        this.onTokenRefreshed?.(newInfo);
        return newInfo;
    }
}
exports.AuthAPI = AuthAPI;
//# sourceMappingURL=auth.js.map