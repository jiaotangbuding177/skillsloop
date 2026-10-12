"use strict";
// ============================================================
// Get笔记 Web SDK 入口
// ============================================================
Object.defineProperty(exports, "__esModule", { value: true });
exports.sleep = exports.GetNoteWebError = exports.parseWebResponse = exports.AuthAPI = exports.KnowledgeAPI = exports.TagsAPI = exports.SearchAPI = exports.NotesAPI = exports.GetNoteClient = void 0;
var client_1 = require("./client");
Object.defineProperty(exports, "GetNoteClient", { enumerable: true, get: function () { return client_1.GetNoteClient; } });
var notes_1 = require("./api/notes");
Object.defineProperty(exports, "NotesAPI", { enumerable: true, get: function () { return notes_1.NotesAPI; } });
var search_1 = require("./api/search");
Object.defineProperty(exports, "SearchAPI", { enumerable: true, get: function () { return search_1.SearchAPI; } });
var tags_1 = require("./api/tags");
Object.defineProperty(exports, "TagsAPI", { enumerable: true, get: function () { return tags_1.TagsAPI; } });
var knowledge_1 = require("./api/knowledge");
Object.defineProperty(exports, "KnowledgeAPI", { enumerable: true, get: function () { return knowledge_1.KnowledgeAPI; } });
var auth_1 = require("./api/auth");
Object.defineProperty(exports, "AuthAPI", { enumerable: true, get: function () { return auth_1.AuthAPI; } });
var utils_1 = require("./utils");
Object.defineProperty(exports, "parseWebResponse", { enumerable: true, get: function () { return utils_1.parseWebResponse; } });
Object.defineProperty(exports, "GetNoteWebError", { enumerable: true, get: function () { return utils_1.GetNoteWebError; } });
Object.defineProperty(exports, "sleep", { enumerable: true, get: function () { return utils_1.sleep; } });
//# sourceMappingURL=index.js.map