import { TokenInfo } from "../types";
export declare class AuthAPI {
    private authBaseUrl;
    private tokenInfo;
    private refreshPromise;
    private onTokenRefreshed?;
    constructor(authBaseUrl?: string, tokenInfo?: TokenInfo, onTokenRefreshed?: (info: TokenInfo) => void);
    /** 更新本地 token 信息 */
    setTokenInfo(info: TokenInfo): void;
    /** 获取当前 token 信息 */
    getTokenInfo(): TokenInfo | null;
    /**
     * 判断是否需要刷新 token
     * 当 token 过期时间距离现在不足 5 分钟时，返回 true
     */
    needsRefresh(): boolean;
    /**
     * 判断 refresh_token 是否已过期
     */
    isRefreshTokenExpired(): boolean;
    /**
     * 刷新 token
     * POST /account/v2/web/user/auth/refresh
     * Body: { refresh_token: "..." }
     * 返回: { h: { c: 0 }, c: { success: true, token: { ... } } }
     *
     * 注意：并发调用时只发一次请求
     */
    refreshToken(): Promise<TokenInfo>;
    private _doRefresh;
}
//# sourceMappingURL=auth.d.ts.map