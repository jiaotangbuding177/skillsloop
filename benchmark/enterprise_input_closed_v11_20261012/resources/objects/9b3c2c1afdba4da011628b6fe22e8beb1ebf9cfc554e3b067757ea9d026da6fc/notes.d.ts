import { NoteListData, NoteListRequest, NoteDetail, CreateNoteRequest, CreateNoteData, UpdateNoteRequest, DeleteNoteResponse, SearchNoteData, RecycleBinData } from "../types";
export declare class NotesAPI {
    private baseUrl;
    private token;
    private csrfToken;
    private deviceId;
    constructor(baseUrl: string, token: string, csrfToken: string, deviceId: string);
    /** 更新凭证 */
    updateCredentials(token: string, csrfToken: string, deviceId: string): void;
    private get headers();
    /**
     * 获取笔记列表
     * GET /voicenotes/web/notes?limit=&since_id=&sort=
     */
    list(options?: NoteListRequest): Promise<NoteListData>;
    /**
     * 获取笔记详情
     * GET /voicenotes/web/notes/{noteId}
     */
    detail(noteId: string): Promise<NoteDetail>;
    /**
     * 创建笔记
     * POST /voicenotes/web/notes
     */
    create(body: CreateNoteRequest): Promise<CreateNoteData>;
    /**
     * 创建文本笔记（便捷方法）
     * 自动将换行符拆分为独立段落，确保 ProseMirror 正确渲染
     */
    createText(title: string, text: string, tags?: string[]): Promise<CreateNoteData>;
    /**
     * 更新笔记
     * PUT /voicenotes/web/notes/{noteId}
     * 使用 prime_id 或 note_id 定位笔记
     */
    update(noteId: string, body: UpdateNoteRequest): Promise<NoteDetail>;
    /**
     * 更新笔记标题和内容（便捷方法）
     */
    updateContent(noteId: string, title: string, text: string, version?: number, tags?: string[]): Promise<NoteDetail>;
    /**
     * 删除笔记（移入回收站）
     * DELETE /voicenotes/web/notes/{noteId}
     */
    delete(noteId: string): Promise<DeleteNoteResponse>;
    /**
     * 搜索笔记
     * GET /voicenotes/web/notes/search?page=&page_size=&query=
     */
    search(query: string, page?: number, pageSize?: number): Promise<SearchNoteData>;
    /**
     * 获取回收站列表
     * GET /voicenotes/web/notes/recycle/
     */
    recycleBin(page?: number, pageSize?: number): Promise<RecycleBinData>;
    /**
     * 回收站搜索
     * GET /voicenotes/web/notes/recycle/search?query=
     */
    searchRecycleBin(query: string, page?: number, pageSize?: number): Promise<RecycleBinData>;
    /**
     * 回收站批量操作（恢复/彻底删除）
     * POST /voicenotes/web/notes/recycle/op/batch
     */
    recycleBinBatchOp(noteIds: string[], action: "restore" | "delete"): Promise<any>;
    /**
     * 清空回收站
     * POST /voicenotes/web/notes/recycle/op/clear
     */
    clearRecycleBin(): Promise<any>;
    /**
     * 获取笔记总数
     * GET /voicenotes/web/notes/count
     */
    count(): Promise<{
        total: number;
    }>;
    /**
     * 获取所有笔记（自动翻页直到没有更多数据）
     */
    listAll(pageSize?: number): Promise<NoteListData>;
}
//# sourceMappingURL=notes.d.ts.map