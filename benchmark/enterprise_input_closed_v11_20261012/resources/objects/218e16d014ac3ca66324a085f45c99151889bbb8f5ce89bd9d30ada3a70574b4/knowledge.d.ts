export declare class KnowledgeAPI {
    private baseUrl;
    private token;
    private csrfToken;
    private deviceId;
    constructor(baseUrl: string, token: string, csrfToken: string, deviceId: string);
    updateCredentials(token: string, csrfToken: string, deviceId: string): void;
    private get headers();
    /**
     * 将笔记添加到话题（知识库）
     * POST /voicenotes/web/topics/import/notes
     */
    addNotesToTopic(topicId: number, noteIds: string[]): Promise<any>;
    /**
     * 从话题中删除笔记
     * DELETE /voicenotes/web/topics/{topicId}/notes/{noteId}
     */
    removeNoteFromTopic(topicId: number, noteId: string): Promise<any>;
    /**
     * 在话题中创建笔记
     * POST /voicenotes/web/topics/notes
     */
    createNoteInTopic(body: {
        topic_id: number;
        title: string;
        json_content: string;
        note_type?: string;
        tags?: string[];
    }): Promise<any>;
    /**
     * 获取博主列表
     * GET /v1/web/follow/list?topic_id=-1&topic_id_alias=
     */
    getBloggerList(topicAlias?: string): Promise<any>;
    /**
     * 获取博主内容列表
     * GET /v1/web/follow/account/posts?follow_id=&page=&page_size=
     */
    getBloggerPosts(followId: string, page?: number, pageSize?: number): Promise<any>;
    /**
     * 取消关注博主
     * DELETE /v1/web/follow/delete
     */
    unfollowBlogger(followIds: string[]): Promise<any>;
}
//# sourceMappingURL=knowledge.d.ts.map