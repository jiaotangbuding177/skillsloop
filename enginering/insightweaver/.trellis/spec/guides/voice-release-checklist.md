# Voice Feature Release Checklist（语音功能发布检查清单）

> !225/!227/!228 发布沉淀，2026-08-20

语音功能（前端麦克风按钮 + 后端 WS 代理 + 配额计费）发布前逐项检查：

## 1. 环境变量（缺失 = API 启动即崩）

`SpeechService` 构造器用 `getOrThrow` 读取，**任一缺失整个 API 无法启动**：

| 变量 | 说明 |
|------|------|
| `ALIYUN_ACCESS_KEY_ID` / `ALIYUN_ACCESS_KEY_SECRET` | 阿里云凭据（换取 NLS token） |
| `ALIYUN_NLS_APPKEY` | NLS 识别应用 key（⚠️ env 模板未登记，生产必须手动配置） |

可选（有默认值）：`ALIYUN_NLS_WS_URL`（默认上海节点）、`VOICE_MAX_DURATION_MS`（60s）、`VOICE_SETTLE_STALE_MS`（90s）。

## 2. 数据库

**无 schema 变更、无需 migrate**。语音复用既有表：`billing_task`、`zclaw_enterprise_token_usage_settlements`（`quotaMode` 字段既有）、`zclaw_enterprise_conversation_quota_usages`（`remainingConversations` 既有）。

## 3. 计费配置（工具扣费）

管理后台 → 基础设置 → 工具计费（`/api/admin/config/tool-billing`）：

- 确认 `tool_call_billing_configs` 有 `toolType='voice_input'` 行（无则用默认 100000/60s）
- `tokensPerUnit` = **60 秒全价**（10s 结算 ≈ 单价×10/60，floor 取整）
- `enterpriseId=null` = 全局价；企业专属行 = 覆盖价（优先级：企业 > 全局 > 默认）

## 4. 配额行为（!228 后）

| 场景 | 行为 |
|------|------|
| conversation 模式语音 | 扣 1 次会话（admin/owner 豁免） |
| token/batch 模式配额耗尽 | start 拦截（`ZclawTokenQuotaExceededError`），不冻结 |
| C 端 | billing token 扣费，无企业配额拦截 |
| 明细显示 | conversation 模式显示「语音输入（会话数模式）」 |

## 5. P0 抽验（合入后）

- [ ] 语音录制/转写/按实际时长扣费（1s ≈ 单价/60）
- [ ] 60s 硬切断提示 + 全价结算
- [ ] conversation 模式语音扣 1 次会话（明细「语音输入（会话数模式）」）
- [ ] token 模式配额耗尽：语音 start 被拦截
- [ ] 余额不足（4001）提示；断网 0 秒不扣费

## 6. 发布顺序（分支依赖链）

```
!225 语音功能 → !227 测试健康 → !228 配额计费
```

- 增量分支基于前序分支 head；squash 合并后增量分支 merge release 时
  「ours 冲突」处理法：冲突文件 `git checkout --ours` + 验证 diff 仅剩增量（见 pre-push-checklist）
