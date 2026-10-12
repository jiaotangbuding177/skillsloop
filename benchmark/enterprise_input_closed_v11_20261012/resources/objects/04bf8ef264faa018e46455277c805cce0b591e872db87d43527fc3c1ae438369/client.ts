// ============================================================
// Get笔记 Web SDK 主客户端
// 通过 JWT Bearer Token 认证（浏览器 Cookie 登录后获取）
// Base URL: https://get-notes.luojilab.com
// 支持 refresh_token 自动刷新
// ============================================================

import { GetNoteWebConfig, TokenInfo } from "./types";
import { NotesAPI } from "./api/notes";
import { SearchAPI } from "./api/search";
import { TagsAPI } from "./api/tags";
import { KnowledgeAPI } from "./api/knowledge";
import { AuthAPI } from "./api/auth";

export class GetNoteClient {
  private baseUrl: string;
  private token: string;
  private csrfToken: string;
  private deviceId: string;
  private auth: AuthAPI | null = null;

  /** 笔记操作 */
  public notes: NotesAPI;
  /** 搜索 */
  public search: SearchAPI;
  /** 标签管理 */
  public tags: TagsAPI;
  /** 知识库管理 */
  public knowledge: KnowledgeAPI;

  constructor(config: GetNoteWebConfig) {
    this.baseUrl = config.baseUrl || "https://get-notes.luojilab.com";
    this.token = config.token;
    this.csrfToken = config.csrfToken;
    this.deviceId = config.deviceId;

    // 初始化认证模块（如果提供了 refresh_token）
    if (config.refreshToken) {
      const tokenInfo: TokenInfo = {
        token: config.token,
        token_expire_at: config.tokenExpireAt || 0,
        refresh_token: config.refreshToken,
        refresh_token_expire_at: config.refreshTokenExpireAt || 0,
      };
      this.auth = new AuthAPI(
        config.authBaseUrl,
        tokenInfo,
        (newInfo: TokenInfo) => this._onTokenRefreshed(newInfo)
      );
    }

    this.notes = new NotesAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
    this.search = new SearchAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
    this.tags = new TagsAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
    this.knowledge = new KnowledgeAPI(this.baseUrl, this.token, this.csrfToken, this.deviceId);
  }

  /** token 刷新后同步所有子 API */
  private _onTokenRefreshed(info: TokenInfo): void {
    this.token = info.token;
    this.notes.updateCredentials(info.token, this.csrfToken, this.deviceId);
    this.search.updateCredentials(info.token, this.csrfToken, this.deviceId);
    this.tags.updateCredentials(info.token, this.csrfToken, this.deviceId);
    this.knowledge.updateCredentials(info.token, this.csrfToken, this.deviceId);
  }

  /** 更新凭证（热切换） */
  setCredentials(token: string, csrfToken: string, deviceId: string, refreshToken?: string, tokenExpireAt?: number, refreshTokenExpireAt?: number): void {
    this.token = token;
    this.csrfToken = csrfToken;
    this.deviceId = deviceId;

    if (refreshToken) {
      const tokenInfo: TokenInfo = {
        token,
        token_expire_at: tokenExpireAt || 0,
        refresh_token: refreshToken,
        refresh_token_expire_at: refreshTokenExpireAt || 0,
      };
      if (this.auth) {
        this.auth.setTokenInfo(tokenInfo);
      } else {
        this.auth = new AuthAPI(
          undefined,
          tokenInfo,
          (newInfo: TokenInfo) => this._onTokenRefreshed(newInfo)
        );
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
  async ensureToken(): Promise<void> {
    if (!this.auth) return;
    if (this.auth.needsRefresh()) {
      const info = await this.auth.refreshToken();
      // _onTokenRefreshed 回调已更新子 API
    }
  }

  /** 检查 refresh_token 是否已过期 */
  isLoginValid(): boolean {
    if (!this.auth) return true; // 没有 auth 模块时不判断
    return !this.auth.isRefreshTokenExpired();
  }

  /** 获取当前 token 信息 */
  getTokenInfo(): TokenInfo | null {
    return this.auth?.getTokenInfo() || null;
  }

  /** 主动刷新 token */
  async refreshToken(): Promise<TokenInfo> {
    if (!this.auth) throw new Error("未配置 refresh_token");
    return this.auth.refreshToken();
  }
}
