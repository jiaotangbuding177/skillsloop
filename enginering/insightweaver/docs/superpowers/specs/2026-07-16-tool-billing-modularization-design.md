---
comet_change: tool-billing-modularization
role: technical-design
canonical_spec: openspec
---

# 工具调用计费模块化 — 技术设计文档

## 1. 架构概览

将图片计费从 Redis `ImageBillingConfigService` 迁移到数据库表 `tool_call_billing_configs`，新增 tavily 搜索计费，统一配额模式。

**核心组件：**
- `ToolCallBillingService`：DB 读写 + 计费计算
- Admin API：`GET/PATCH /admin/config/tool-billing`
- 前端 Section：集成到 `/admin/basic-settings` 底部

## 2. 数据库设计

### 2.1 Prisma Model

```prisma
model ToolCallBillingConfig {
  id              String   @id @default(uuid())
  enterpriseId    String?  // null = 全局默认
  toolType        String   // 'image_generation', 'web_search_tavily'
  toolLabel       String   // '图片生成', 'Tavily 搜索'
  toolNames       String[] // ['process'], ['tavily','tavily_search']
  countingStrategy String  // 'per_output_image' | 'per_completed_call'
  tokensPerUnit   BigInt   @default(100000)
  isEnabled       Boolean  @default(true)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@unique([enterpriseId, toolType])
  @@index([enterpriseId, isEnabled])
  @@map("tool_call_billing_configs")
}
```

### 2.2 种子数据

启动时 `onModuleInit()` upsert 两条默认记录：

| toolType | toolLabel | toolNames | countingStrategy | tokensPerUnit |
|----------|-----------|-----------|-----------------|---------------|
| image_generation | 图片生成 | `['process']` | per_output_image | 100000 |
| web_search_tavily | Tavily 搜索 | `['tavily','tavily_search']` | per_completed_call | 100000 |

## 3. 后端服务

### 3.1 ToolCallBillingService

**文件：** `apps/api/src/billing/tool-call-billing.service.ts`

**核心方法：**

```typescript
@Injectable()
export class ToolCallBillingService implements OnModuleInit {
  async onModuleInit() {
    // upsert 两条种子记录
  }

  async calculateToolBillingTokens(
    enterpriseId: string | null,
    toolActivities: Map<string, { name: string; status: string; output?: unknown }>
  ): Promise<number> {
    const configs = await this.getActiveConfigs(enterpriseId);
    const toolNameMap = this.buildToolNameMap(configs);
    let totalUnits = 0;
    
    for (const activity of toolActivities.values()) {
      if (activity.status !== 'completed') continue;
      const config = toolNameMap.get(activity.name);
      if (!config) continue;
      totalUnits += this.countUnits(config.countingStrategy, activity);
    }
    
    const tokensPerUnit = configs[0]?.tokensPerUnit ?? 100000n;
    return Number(BigInt(totalUnits) * tokensPerUnit);
  }

  private countUnits(strategy: string, activity): number {
    switch (strategy) {
      case 'per_output_image':
        return extractImageCountFromOutput(activity.output);
      case 'per_completed_call':
        return 1;
      default:
        return 0;
    }
  }

  async getAllConfigs(): Promise<ToolCallBillingConfig[]> { }
  async getUnifiedTokensPerUnit(): Promise<bigint> { }
  async updateUnifiedTokensPerUnit(value: bigint): Promise<void> {
    // 批量更新所有行的 tokensPerUnit
  }
}
```

### 3.2 计费流程重构

**Path A（billing entitlement）：**
```diff
- const imageCount = countImagesFromToolActivities(toolActivities);
- const tokensPerImage = await this.imageBillingConfigService.getTokensPerImage();
- const totalTokens = llmTokens + imageCount * tokensPerImage;
+ const toolBillingTokens = await this.toolCallBillingService.calculateToolBillingTokens(
+   enterpriseIdForEfficiency, toolActivities
+ );
+ const totalTokens = llmTokens + toolBillingTokens;
```

**Path B（enterprise quota）：**
```diff
- const imageCount = countImagesFromToolActivities(toolActivities);
+ const toolBillingTokens = await this.toolCallBillingService.calculateToolBillingTokens(
+   enterpriseIdForEfficiency, toolActivities
+ );
  await this.settleEnterpriseTokenUsageIfNeeded(
-   enterpriseId, userId, messageId, usage, imageCount
+   enterpriseId, userId, messageId, usage, toolBillingTokens
  );
```

**settleEnterpriseTokenUsageIfNeeded：**
```diff
- imageCount = 0
+ toolBillingTokens = 0
- const tokensPerImage = await this.imageBillingConfigService.getTokensPerImage();
- const imageTokens = imageCount * tokensPerImage;
- if (imageTokens > 0) {
-   usage = { ...usage, output: (usage.output ?? 0) + Math.ceil(imageTokens / 6) };
+ if (toolBillingTokens > 0) {
+   usage = { ...usage, output: (usage.output ?? 0) + Math.ceil(toolBillingTokens / 6) };
  }
```

## 4. 管理 API

### 4.1 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/admin/config/tool-billing` | 返回所有配置 + unifiedTokensPerUnit |
| PATCH | `/admin/config/tool-billing/unified` | 更新全局 tokensPerUnit |

### 4.2 响应格式

```json
{
  "items": [
    {
      "id": "uuid",
      "toolType": "image_generation",
      "toolLabel": "图片生成",
      "toolNames": ["process"],
      "countingStrategy": "per_output_image",
      "tokensPerUnit": 100000,
      "isEnabled": true
    },
    {
      "id": "uuid",
      "toolType": "web_search_tavily",
      "toolLabel": "Tavily 搜索",
      "toolNames": ["tavily", "tavily_search"],
      "countingStrategy": "per_completed_call",
      "tokensPerUnit": 100000,
      "isEnabled": true
    }
  ],
  "unifiedTokensPerUnit": 100000
}
```

## 5. 前端

### 5.1 API 模块

```typescript
export interface ToolBillingConfigItem {
  id: string;
  toolType: string;
  toolLabel: string;
  toolNames: string[];
  countingStrategy: string;
  tokensPerUnit: number;
  isEnabled: boolean;
}

export const getToolBillingConfigsApi = () =>
  http.get<{ items: ToolBillingConfigItem[]; unifiedTokensPerUnit: number }>(
    '/api/admin/config/tool-billing'
  );

export const updateUnifiedTokensPerUnitApi = (tokensPerUnit: number) =>
  http.patch('/api/admin/config/tool-billing/unified', { tokensPerUnit });
```

### 5.2 UI 集成

在 `basic-settings/page.tsx` 底部新增 Section：

```tsx
{isPlatformAdmin && (
  <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
    <h2>工具调用计费</h2>
    <p>AI 对话中每次工具调用额外扣除的 Token 数量。</p>
    
    {/* 统一配额编辑框 */}
    <div>
      <label>统一配额</label>
      <input type="number" value={wanValue} onChange={...} />
      <span>万</span>
      <button onClick={handleSave}>保存</button>
    </div>
    
    {/* 已注册工具列表 */}
    <div>
      {items.map(item => (
        <div key={item.id}>
          <span>{item.toolLabel}</span>
          <span>匹配工具: {item.toolNames.join(', ')}</span>
          <span>计数: {策略中文}</span>
        </div>
      ))}
    </div>
  </section>
)}
```

## 6. 清理

- 删除 `apps/web/src/app/[locale]/(zclaw-shell)/admin/billing-config/page.tsx`
- 删除 admin 首页 `billingConfig` 入口卡片
- 旧 Redis 键 `config:tokens_per_image` 保留不删

## 7. 测试验证

1. `pnpm db:migrate` 建表成功
2. 启动服务后种子数据 upsert 成功（2 条记录）
3. `GET /api/admin/config/tool-billing` 返回 2 条配置
4. `PATCH /api/admin/config/tool-billing/unified` 更新成功
5. 图片生成：1 张图 × tokensPerUnit 扣费
6. Tavily 搜索：1 次调用 × tokensPerUnit 扣费
7. `/admin/basic-settings` 底部显示工具计费 Section，仅超管可见
8. 旧页面 `/admin/billing-config` 已删除

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| DB 查询延迟 | 仅查 1-2 行，可忽略；未来可加缓存 |
| Tavily 工具名不匹配 | 兼容两种名字；上线后日志确认 |
| 旧 Redis 键残留 | 保留不删，无影响 |
