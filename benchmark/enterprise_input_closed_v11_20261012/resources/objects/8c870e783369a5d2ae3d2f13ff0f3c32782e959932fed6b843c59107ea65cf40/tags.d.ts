import { TagListData, TagInfo } from "../types";
export declare class TagsAPI {
    private baseUrl;
    private token;
    private csrfToken;
    private deviceId;
    constructor(baseUrl: string, token: string, csrfToken: string, deviceId: string);
    updateCredentials(token: string, csrfToken: string, deviceId: string): void;
    private get headers();
    /**
     * 获取标签列表
     * GET /voicenotes/web/tags?page_size=
     */
    list(pageSize?: number): Promise<TagListData>;
    /**
     * 为笔记添加标签
     * POST /voicenotes/web/notes/{noteId}/tags
     */
    add(noteId: string, tags: string[]): Promise<TagInfo[]>;
    /**
     * 删除笔记标签
     * DELETE /voicenotes/web/notes/{noteId}/tags
     */
    remove(noteId: string, tagIds: string[]): Promise<void>;
}
//# sourceMappingURL=tags.d.ts.map