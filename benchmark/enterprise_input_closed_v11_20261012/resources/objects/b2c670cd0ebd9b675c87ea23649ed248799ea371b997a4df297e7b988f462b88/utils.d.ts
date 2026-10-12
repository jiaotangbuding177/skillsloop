/**
 * 从 HTTP 响应中解析 Web API 格式的 JSON
 * Web API 格式: { h: { c, e, s, t, apm }, c: {...} }
 */
export declare function parseWebResponse<T>(response: Response): Promise<T>;
/**
 * 睡眠等待
 */
export declare function sleep(ms: number): Promise<void>;
/**
 * Get笔记 Web API 错误类
 */
export declare class GetNoteWebError extends Error {
    code: number;
    traceId?: string;
    constructor(message: string, code: number, traceId?: string);
}
//# sourceMappingURL=utils.d.ts.map