# 测试报告：消息时间戳「月-日 + 时间」

## 单元测试结果

| 测试 | 结果 |
|------|------|
| formatMessageTime same-day → `18:02` | ✅ |
| formatMessageTime prior-day → `08-03 09:05` | ✅ |
| formatMessageTime single-digit padding → `01-04 08:07` | ✅ |
| formatMessageTime invalid date → raw fallback | ✅ |
| formatMessageTime null/undefined → `-` | ✅ |
| isSameDay same day → true | ✅ |
| isSameDay different day → false | ✅ |
| isSameDay cross-year → false | ✅ |

## TypeScript

- `tsc --noEmit` — 零新增错误 ✅

## Code Review

- Standards: 测试文件双引号已修 ✅
- Spec: Intl.DateTimeFormat locale 依赖已移除，改为 24h pad2 ✅
