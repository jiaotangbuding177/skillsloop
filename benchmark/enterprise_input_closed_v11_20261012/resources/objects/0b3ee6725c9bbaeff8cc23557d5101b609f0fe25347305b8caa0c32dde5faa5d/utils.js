"use strict";
// ============================================================
// Get笔记 Web SDK 工具函数
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.GetNoteWebError = void 0;
exports.parseWebResponse = parseWebResponse;
exports.sleep = sleep;
/**
 * 从 HTTP 响应中解析 Web API 格式的 JSON
 * Web API 格式: { h: { c, e, s, t, apm }, c: {...} }
 */
async function parseWebResponse(response) {
    const text = await response.text();
    let json;
    try {
        json = JSON.parse(text);
    }
    catch {
        throw new Error(`无法解析响应: ${text.slice(0, 200)}`);
    }
    const header = json.h;
    if (!header) {
        throw new Error(`响应格式异常: ${text.slice(0, 200)}`);
    }
    if (header.c !== 0) {
        throw new GetNoteWebError(header.e || "未知错误", header.c, header.apm);
    }
    return json.c;
}
/**
 * 睡眠等待
 */
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
/**
 * Get笔记 Web API 错误类
 */
class GetNoteWebError extends Error {
    constructor(message, code, traceId) {
        super(message);
        this.name = "GetNoteWebError";
        this.code = code;
        this.traceId = traceId;
    }
}
exports.GetNoteWebError = GetNoteWebError;
//# sourceMappingURL=utils.js.map