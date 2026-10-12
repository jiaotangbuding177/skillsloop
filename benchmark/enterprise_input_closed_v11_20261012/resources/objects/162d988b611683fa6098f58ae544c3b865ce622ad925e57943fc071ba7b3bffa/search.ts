// ============================================================
// 搜索 API：笔记搜索
// Base URL: https://get-notes.luojilab.com
// ============================================================

import { SearchNoteData } from "../types";
import { parseWebResponse } from "../utils";

function buildHeaders(token: string, csrfToken: string, deviceId: string): Record<string, string> {
  return {
    "Authorization": `Bearer ${token}`,
    "Xi-Csrf-Token": csrfToken,
    "x-d": deviceId,
    "Xi-App-Client-Source": "getnote",
    "Content-Type": "application/json",
    "Origin": "https://www.biji.com",
  };
}

export class SearchAPI {
  private baseUrl: string;
  private token: string;
  private csrfToken: string;
  private deviceId: string;

  constructor(baseUrl: string, token: string, csrfToken: string, deviceId: string) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.csrfToken = csrfToken;
    this.deviceId = deviceId;
  }

  updateCredentials(token: string, csrfToken: string, deviceId: string): void {
    this.token = token;
    this.csrfToken = csrfToken;
    this.deviceId = deviceId;
  }

  private get headers(): Record<string, string> {
    return buildHeaders(this.token, this.csrfToken, this.deviceId);
  }

  /**
   * 搜索笔记
   * GET /voicenotes/web/notes/search?page=&page_size=&query=
   */
  async search(query: string, page = 1, pageSize = 10): Promise<SearchNoteData> {
    const params = new URLSearchParams();
    params.set("query", query);
    params.set("page", String(page));
    params.set("page_size", String(pageSize));

    const url = `${this.baseUrl}/voicenotes/web/notes/search?${params.toString()}`;
    const res = await fetch(url, {
      method: "GET",
      headers: this.headers,
    });
    return parseWebResponse<SearchNoteData>(res);
  }
}
