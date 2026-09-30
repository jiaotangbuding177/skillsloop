# IntersectionObserver 哨兵分批加载契约

> 来源：bugfix-20260908-history-sentinel-observer（2026-09-09）。AI 会话记录列表「折叠面板→再展开→滚动不加载」间歇失效的根因修复沉淀。

## Scope / Trigger

适用条件：列表数据全量在 state、用「哨兵元素 + IntersectionObserver + 计数裁剪」做 DOM 分批渲染（如 ZclawShell 历史面板 `visibleHistoryCount` 模式）。凡新增此类哨兵，**必须**复用本文契约，禁止手写 effect+ref 绑定。

## 契约（Signatures）

```ts
// apps/web/src/hooks/useSentinelIntersectionObserver.ts
function useSentinelIntersectionObserver(
  onIntersect: () => void,
  options?: IntersectionObserverInit,
): (node: HTMLElement | null) => void; // callback ref，直接绑哨兵元素
```

- **观察器生命周期绑节点生命周期**：节点挂载（ref callback 收到 node）即创建并 `observe`；卸载/替换（收到 null）即 `disconnect`。禁止把 observe 放进依赖数组只含数据的 effect——节点重挂载不等于 effect 重跑。
- **触发后自重臂**：回调触发后 `observer.unobserve(node); observer.observe(node)`。IO 只在交叉状态**翻转**时通知；丢失重臂会导致「追加后哨兵仍在区域内（高面板/短内容）时中途停摆且滚动无法解锁」——effect 重跑的旧写法隐式提供每批重新 observe 的初始通知，改写时必须显式保持该语义。循环终止于哨兵推出区域或条件渲染卸载哨兵。
- **onIntersect 经 latest-ref**：回调身份变化不重建观察器（无重订阅抖动）。
- **options 取 attach 时刻最新渲染值**，此后变更不影响已创建的观察器（传常量字面量）。

## Wrong vs Correct

```tsx
// ❌ Wrong：effect+ref，依赖只含数据——重挂载路径失效（本 bug 根因）
const sentinelRef = React.useRef<HTMLDivElement | null>(null);
React.useEffect(() => {
  const sentinel = sentinelRef.current;
  if (!sentinel) return;
  const observer = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) setVisible((c) => c + PAGE);
  }, { rootMargin: "200px" });
  observer.observe(sentinel);
  return () => observer.disconnect();
}, [visibleCount, items.length]); // 数据依赖：count 重置同值 bailout 时不重跑

// ✅ Correct：callback ref 绑节点生命周期
const sentinelRef = useSentinelIntersectionObserver(() => {
  setVisible((c) => c + PAGE);
}, { rootMargin: "200px" });
{hasMore ? <div ref={sentinelRef} aria-hidden="true" className="h-px" /> : null}
```

## 测试要求（apps/web/src/hooks/__tests__/useSentinelIntersectionObserver.test.tsx 为基准）

jsdom 无 IO 实现，mock 必须**语义保真**，否则回归是 false green：

1. `observe()` 必发**异步宏任务**初始通知，isIntersecting 读投递时刻可见性（真实 IO：observe 即通知）。手动 `trigger(true)` 直调回调绕过该语义，曾掩盖自重臂回归（CR 实证）。
2. 可见性变化仅**翻转**时通知（crossing 语义）。
3. 投递前校验 `disconnected`/仍观察中（disconnect 后已排队通知不投递）。
4. 投递必须用 `setTimeout`（宏任务），**禁止 queueMicrotask**——重臂链在微任务下形成无限链、React 调度器无插入点（worker OOM 实证）。
5. 断言用单调终态（如「最终包含 session-34 且哨兵卸载」），不依赖「每 flush 恰一批」——Node 定时器桶序有抖动，一次宏任务排空可能合并多批。
6. 必备用例：区域内连续追加直至条件翻转卸载（锁自重臂）；节点重挂载（折叠→展开、依赖未变）后新节点可触发（锁本 bug）；卸载 disconnect（清理契约）。
7. 反验：移除重臂/复刻旧绑定模式，对应用例必须变红。

## 既有用法处置（审计结论 2026-09-09）

MessageList/ZclawAssistantPage 顶部哨兵、SuperLobsterPage 消息懒恢复、ResearchInterface ScrollSpy、useScrollReveal 共 5 处 effect/query 绑定——均有依赖变化兜底或静态场景，无失效路径，**保持不动**；若未来给它们引入「无依赖变化的重挂载路径」，必须先迁移到本契约 hook。
