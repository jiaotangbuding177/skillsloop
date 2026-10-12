import { SearchNoteData } from "../types";
export declare class SearchAPI {
    private baseUrl;
    private token;
    private csrfToken;
    private deviceId;
    constructor(baseUrl: string, token: string, csrfToken: string, deviceId: string);
    updateCredentials(token: string, csrfToken: string, deviceId: string): void;
    private get headers();
    /**
     * 搜索笔记
     * GET /voicenotes/web/notes/search?page=&page_size=&query=
     */
    search(query: string, page?: number, pageSize?: number): Promise<SearchNoteData>;
}
//# sourceMappingURL=search.d.ts.map