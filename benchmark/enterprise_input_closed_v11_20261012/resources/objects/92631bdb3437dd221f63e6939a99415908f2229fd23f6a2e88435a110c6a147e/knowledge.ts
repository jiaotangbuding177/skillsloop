// ============================================================
// 知识库 API：博主/直播订阅、知识库管理
// 知识库在 biji.com 中称为"话题"（Topic）
// Base URL: https://get-notes.luojilab.com
// ============================================================

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

export class KnowledgeAPI {
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
   * 将笔记添加到话题（知识库）
   * POST /voicenotes/web/topics/import/notes
   */
  async addNotesToTopic(topicId: number, noteIds: string[]): Promise<any> {
    const url = `${this.baseUrl}/voicenotes/web/topics/import/notes`;
    const res = await fetch(url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({
        ids: noteIds,
        topic_id: topicId,
      }),
    });
    return parseWebResponse(res);
  }

  /**
   * 从话题中删除笔记
   * DELETE /voicenotes/web/topics/{topicId}/notes/{noteId}
   */
  async removeNoteFromTopic(topicId: number, noteId: string): Promise<any> {
    const url = `${this.baseUrl}/voicenotes/web/topics/${topicId}/notes/${noteId}`;
    const res = await fetch(url, {
      method: "DELETE",
      headers: this.headers,
    });
    return parseWebResponse(res);
  }

  /**
   * 在话题中创建笔记
   * POST /voicenotes/web/topics/notes
   */
  async createNoteInTopic(body: {
    topic_id: number;
    title: string;
    json_content: string;
    note_type?: string;
    tags?: string[];
  }): Promise<any> {
    const url = `${this.baseUrl}/voicenotes/web/topics/notes`;
    const res = await fetch(url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(body),
    });
    return parseWebResponse(res);
  }

  /**
   * 获取博主列表
   * GET /v1/web/follow/list?topic_id=-1&topic_id_alias=
   */
  async getBloggerList(topicAlias = ""): Promise<any> {
    const url = `${this.baseUrl}/v1/web/follow/list?topic_id=-1&topic_id_alias=${topicAlias}`;
    const res = await fetch(url, {
      method: "GET",
      headers: this.headers,
    });
    return parseWebResponse(res);
  }

  /**
   * 获取博主内容列表
   * GET /v1/web/follow/account/posts?follow_id=&page=&page_size=
   */
  async getBloggerPosts(followId: string, page = 1, pageSize = 20): Promise<any> {
    const params = new URLSearchParams();
    params.set("follow_id", followId);
    params.set("page", String(page));
    params.set("page_size", String(pageSize));

    const url = `${this.baseUrl}/v1/web/follow/account/posts?${params.toString()}`;
    const res = await fetch(url, {
      method: "GET",
      headers: this.headers,
    });
    return parseWebResponse(res);
  }

  /**
   * 取消关注博主
   * DELETE /v1/web/follow/delete
   */
  async unfollowBlogger(followIds: string[]): Promise<any> {
    const url = `${this.baseUrl}/v1/web/follow/delete`;
    const res = await fetch(url, {
      method: "DELETE",
      headers: this.headers,
      body: JSON.stringify({ follow_ids: followIds }),
    });
    return parseWebResponse(res);
  }
}
