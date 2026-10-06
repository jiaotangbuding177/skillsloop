// ============================================================
// Get笔记 Web API 类型定义
// Base URL: https://get-notes.luojilab.com
// 通过 JWT Bearer Token 认证（浏览器 Cookie 登录后获取）
// ============================================================

// === 通用响应结构（Web API 格式）===

export interface WebApiHeader {
  c: number;        // 状态码，0=成功
  e: string;        // 错误信息
  s: number;        // 服务器时间戳
  t: number;        // 请求耗时(ms)
  apm: string;      // trace id
}

export interface WebApiResponse<T = any> {
  h: WebApiHeader;
  c: T;
}

// === 笔记类型 ===

export type NoteType =
  | "plain_text"
  | "img_text"
  | "link"
  | "audio"
  | "meeting"
  | "local_audio"
  | "internal_record"
  | "class_audio"
  | "recorder_audio"
  | "recorder_flash_audio";

export interface TagInfo {
  id: string;
  name: string;
  type: "ai" | "manual" | "system";
  visible: boolean;
  is_deleted: number;
  create_time: number;
  update_time: number;
  note_count: number;
}

export interface TopicInfo {
  topic_id: number;
  topic_id_alias: string;
  topic_name: string;
  topic_scope: string;
  resource_id: number;
}

export interface AttachmentInfo {
  type: string;
  url: string;
  original_url?: string;
  title?: string;
}

export interface ResInfo {
  title: string;
  url: string;
  ptype: number;
  ptype_cn_name: string;
}

export interface BookInfo {
  can_read_online: boolean;
  chapter_name: string;
  jump_url: string;
}

/** 笔记列表项 */
export interface NoteListItem {
  id: string;
  note_id: string;
  source: string;
  entry_type: string;
  note_type: NoteType;
  title: string;
  json_content: string;
  ref_content: string;
  res_info: ResInfo;
  tags: string[];
  is_ai_generated: boolean;
  date_str: string;
  time_scale: string;
  attachments: AttachmentInfo[];
  relevant_questions: string[];
  audio_state: number;
  status: number;
  display_status: number;
  share_scope: number;
  share_exclude_audio: boolean;
  share_id: string;
  is_child_note: boolean;
  parent_id: string;
  small_images: string[];
  original_images: string[];
  has_ai_processed: boolean;
  ai_error_type: string;
  ai_error_reason: string;
  edit_time: string;
  created_at: string;
  updated_at: string;
  version: number;
  event_status: number;
  is_author: boolean;
  is_in_topic: boolean;
  is_in_book_topic: boolean;
  can_append_note: boolean;
  hide_source_entrance: boolean;
  book: BookInfo;
  prime_id: string;
  link_redirects: any;
  tabs: any[];
  topics: TopicInfo[];
  book_topics: any[];
  post: { follow_id: number };
}

export interface NoteListData {
  total_items: number;
  list: NoteListItem[];
}

// === 笔记详情 ===

export interface NoteDetail extends NoteListItem {
  // 详情包含所有列表项字段 + 可能的额外字段
  content?: string;
}

// === 笔记列表请求 ===

export interface NoteListRequest {
  limit?: number;
  since_id?: string;
  sort?: "create_desc" | "create_asc" | "update_desc" | "update_asc";
  note_type_list?: NoteType[];
}

// === 创建笔记请求 ===

export interface CreateNoteRequest {
  note_type: NoteType;
  title?: string;
  json_content?: string;    // ProseMirror JSON 格式
  text?: string;            // 纯文本
  tags?: string[];
  source?: string;
  entry_type?: string;
  link_url?: string;
  image_urls?: string[];
  topic_id?: number;
}

export interface CreateNoteData {
  id: string;
  note_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

// === 更新笔记请求 ===

export interface UpdateNoteRequest {
  note_id: string;
  prime_id?: string;
  title?: string;
  json_content?: string;
  content?: string;
  note_type?: NoteType;
  tags?: string[];
  version?: number;
  source?: string;
  entry_type?: string;
  share_scope?: number;
  share_exclude_audio?: boolean;
}

// === 删除笔记 ===

export interface DeleteNoteResponse {
  note_id: string;
}

// === 搜索 ===

export interface SearchNoteRequest {
  query: string;
  page?: number;
  page_size?: number;
}

export interface SearchNoteResult {
  note_id: string;
  title: string;
  content: string;
  note_type: string;
  created_at: string;
  updated_at: string;
}

export interface SearchNoteData {
  total: number;
  list: SearchNoteResult[];
}

// === 标签 ===

export interface AddTagRequest {
  tags: string[];
}

export interface TagListData {
  total: number;
  has_more: boolean;
  items: TagInfo[];
}

// === 回收站 ===

export interface RecycleBinItem {
  note_id: string;
  title: string;
  deleted_at: string;
}

export interface RecycleBinData {
  total: number;
  list: RecycleBinItem[];
}

// === 认证（Token 刷新）===

export interface TokenInfo {
  token: string;
  token_expire_at: number;
  refresh_token: string;
  refresh_token_expire_at: number;
}

export interface RefreshTokenResponse {
  success: boolean;
  status: number;
  uid: number;
  token: {
    jti: string;
    token: string;
    token_expire_at: number;
    refresh_token: string;
    refresh_token_expire_at: number;
  };
}

// === 客户端配置 ===

export interface GetNoteWebConfig {
  baseUrl?: string;              // 默认 https://get-notes.luojilab.com
  token: string;                 // JWT Bearer Token
  csrfToken: string;             // Xi-Csrf-Token
  deviceId: string;              // x-d 设备ID
  refreshToken?: string;         // refresh_token（可选，提供后自动刷新）
  refreshTokenExpireAt?: number; // refresh_token 过期时间戳（可选）
  tokenExpireAt?: number;        // token 过期时间戳（可选，用于提前刷新判断）
  authBaseUrl?: string;          // 认证服务地址，默认 https://ddll-api.trytalks.com
  timeout?: number;
}
