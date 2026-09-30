# 设计：消息时间戳「月-日 + 时间」

## 方案对比

| 方案 | 优点 | 缺点 | 复杂度 |
|------|------|------|--------|
| A：在 format-utils 加纯函数 + MessageBubble 调用 | 复用现有工具模式、可测试、改动集中 | 需新增函数 | 低 |
| B：直接在 MessageBubble 内联 Intl 逻辑 | 不新增文件 | 逻辑混在组件里、难测、违反"small pure helpers" | 低 |

**选 A**（简单方案优先 + AGENTS.md 偏好 pure helpers）。

## 设计

### format-utils.ts 新增

```ts
export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

const pad2 = (n: number) => String(n).padStart(2, "0");

export function formatMessageTime(
  value?: string | null,
  locale = "zh-CN",
  now: Date = new Date(),
): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const time = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
  if (isSameDay(date, now)) return time;
  return `${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${time}`;
}
```

- 时间部分沿用 `Intl.DateTimeFormat` locale-aware 渲染（与现状 `toLocaleTimeString` 行为一致），zh/en 都正确
- 日期部分用数字 `MM-DD`（grill 决策）
- `now` 参数可注入，便于测试
- 无效日期回退原字符串（与 formatDateTime 一致）

### MessageBubble.tsx

把 875-878 的 `new Date(...).toLocaleTimeString(...)` 替换为 `formatMessageTime(message.createdAt, timeLocale)`。状态后缀逻辑不动。

## 状态机 / 竞态

无异步、无共享状态、无状态转换——纯同步渲染，无竞态风险。

## 接缝

`formatMessageTime` 为纯函数（输入 value/locale/now，输出 string），可独立单测。
