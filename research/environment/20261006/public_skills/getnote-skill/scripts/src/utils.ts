// ============================================================
// Get笔记 Web SDK 工具函数
// ============================================================

/**
 * 从 HTTP 响应中解析 Web API 格式的 JSON
 * Web API 格式: { h: { c, e, s, t, apm }, c: {...} }
 */
export async function parseWebResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let json: any;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`无法解析响应: ${text.slice(0, 200)}`);
  }

  const header = json.h;
  if (!header) {
    throw new Error(`响应格式异常: ${text.slice(0, 200)}`);
  }

  if (header.c !== 0) {
    throw new GetNoteWebError(
      header.e || "未知错误",
      header.c,
      header.apm
    );
  }

  return json.c as T;
}

/**
 * 睡眠等待
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Get笔记 Web API 错误类
 */
export class GetNoteWebError extends Error {
  public code: number;
  public traceId?: string;

  constructor(message: string, code: number, traceId?: string) {
    super(message);
    this.name = "GetNoteWebError";
    this.code = code;
    this.traceId = traceId;
  }
}
