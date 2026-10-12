import { GetNoteWebConfig, TokenInfo } from "./types";
import { NotesAPI } from "./api/notes";
import { SearchAPI } from "./api/search";
import { TagsAPI } from "./api/tags";
import { KnowledgeAPI } from "./api/knowledge";
export declare class GetNoteClient {
    private baseUrl;
    private token;
    private csrfToken;
    private deviceId;
    private auth;
    /** 笔记操作 */
    notes: NotesAPI;
    /** 搜索 */
    search: SearchAPI;
    /** 标签管理 */
    tags: TagsAPI;
    /** 知识库管理 */
    knowledge: KnowledgeAPI;
    constructor(config: GetNoteWebConfig);
    /** token 刷新后同步所有子 API */
    private _onTokenRefreshed;
    /** 更新凭证（热切换） */
    setCredentials(token: string, csrfToken: string, deviceId: string, refreshToken?: string, tokenExpireAt?: number, refreshTokenExpireAt?: number): void;
    /**
     * 确保 token 有效（如已过期或即将过期则自动刷新）
     * 在每次 API 调用前调用此方法
     */
    ensureToken(): Promise<void>;
    /** 检查 refresh_token 是否已过期 */
    isLoginValid(): boolean;
    /** 获取当前 token 信息 */
    getTokenInfo(): TokenInfo | null;
    /** 主动刷新 token */
    refreshToken(): Promise<TokenInfo>;
}
//# sourceMappingURL=client.d.ts.map