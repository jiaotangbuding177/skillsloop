# Pre-Push Checklist

每次 `git push` 前必须通过以下检查：

## 1. TypeScript 编译（双端必须都跑）

```bash
pnpm --filter @insightweaver/api build  # 后端
pnpm --filter @insightweaver/web build  # 前端（如改过）
```

> ⚠️ **常见失误（2026-08-18 CI 教训）**：只跑了一端的 tsc 就推送，CI `next build` 才报另一端类型错误。API 和 Web 是**独立 tsconfig**，`apps/api` 下的 `tsc` 不会检查 Web 文件；eslint 也不检查 TS 类型语义（如联合类型无交集的字符串比较）。**无论改了哪一端，双端 tsc 都要跑**（改动跨层时尤其如此）。
>
> ⚠️ `npx tsx --test` **不是** `tsc` 的替代品。`tsx` 运行时会容忍类型错误（接口字段缺失等），`tsc` 会严格检查。

> **本地快速检查**（比 `build` 快）：
> ```bash
> cd apps/api && npx tsc -p tsconfig.json --noEmit --pretty false
> cd apps/web && npx tsc --noEmit --pretty false
> ```

## 2. 全量测试

```bash
cd apps/api && npx tsx --test src/**/*.test.ts  # 后端
cd apps/web && npx vitest run                    # 前端
```

## 3. 新增/修改的类型字段检查

如果新增了 interface 字段（如 `isQuotaExempt?`）：

- [ ] 后端接口定义已加 → `apps/api/src/zclaw/zclaw.service.ts`
- [ ] 前端 `@/api` 类型定义已加 → `apps/web/src/api/moudles/zclaw.ts`
- [ ] 返回值中实际写入该字段（不是仅定义类型）
- [ ] `pnpm build` 双端通过

## 4. 新增 i18n key

- [ ] `zh.json` 和 `en.json` 都已添加
- [ ] key 路径与 useTranslations namespace 匹配
