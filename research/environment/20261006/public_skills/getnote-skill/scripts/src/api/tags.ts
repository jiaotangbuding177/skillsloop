// ============================================================
// 标签 API：列表、添加、删除
// Base URL: https://get-notes.luojilab.com
// ============================================================

import { TagListData, AddTagRequest, TagInfo } from "../types";
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

export class TagsAPI {
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
   * 获取标签列表
   * GET /voicenotes/web/tags?page_size=
   */
  async list(pageSize = 200): Promise<TagListData> {
    const url = `${this.baseUrl}/voicenotes/web/tags?page_size=${pageSize}`;
    const res = await fetch(url, {
      method: "GET",
      headers: this.headers,
    });
    return parseWebResponse<{ data: TagListData }>(res).then(r => r.data);
  }

  /**
   * 为笔记添加标签
   * POST /voicenotes/web/notes/{noteId}/tags
   */
  async add(noteId: string, tags: string[]): Promise<TagInfo[]> {
    const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}/tags`;
    const res = await fetch(url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ tags }),
    });
    return parseWebResponse<TagInfo[]>(res);
  }

  /**
   * 删除笔记标签
   * DELETE /voicenotes/web/notes/{noteId}/tags
   */
  async remove(noteId: string, tagIds: string[]): Promise<void> {
    const url = `${this.baseUrl}/voicenotes/web/notes/${noteId}/tags`;
    const res = await fetch(url, {
      method: "DELETE",
      headers: this.headers,
      body: JSON.stringify({ tag_ids: tagIds }),
    });
    await parseWebResponse(res);
  }
}
