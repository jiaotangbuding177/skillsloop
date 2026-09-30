# Testing Patterns

## Test Runner and Framework

The API uses Node.js built-in `node:test` module, executed via `tsx --test`. There is no Jest, Vitest, or other test framework.

### Runner Configuration

Tests are run with:

```bash
tsx --test apps/api/src/**/*.test.ts
```

Or via package.json script:

```json
{
  "scripts": {
    "test": "tsx --test \"src/**/*.test.ts\""
  }
}
```

### Import Pattern

Every test file uses these imports:

```typescript
import test from 'node:test';
import { strict as assert } from 'node:assert';
```

- `test` provides `describe`, `it`, `before`, `after`, `mock`
- `strict as assert` provides strict equality assertions (`===` not `==`)

## Test Structure

### Basic Test Layout

```typescript
// apps/api/src/billing/billing-plan.service.test.ts
import test from 'node:test';
import { strict as assert } from 'node:assert';
import { BillingPlanService } from './billing-plan.service';

test.describe('BillingPlanService', () => {
  test.describe('createPlan', () => {
    test.it('should create a plan with valid data', async () => {
      // Arrange
      const mockPrisma = {
        billingPlan: {
          create: async (args: any) => ({
            id: 'plan-1',
            ...args.data,
          }),
        },
      };

      const service = new BillingPlanService(mockPrisma as any);

      // Act
      const result = await service.createPlan({
        name: 'Basic',
        price: 1000n,
      });

      // Assert
      assert.equal(result.id, 'plan-1');
      assert.equal(result.name, 'Basic');
    });
  });
});
```

## Mocking Prisma Client

The primary testing strategy is injecting a fake Prisma client into the service constructor. This avoids database setup and makes tests fast and deterministic.

### Minimal Mock

Only mock the methods the test actually calls:

```typescript
const mockPrisma = {
  billingPlan: {
    findFirst: async () => null,
  },
} as any;

const service = new BillingPlanService(mockPrisma);
```

### Gotcha: Keep Mocks In Sync With New Prisma Queries

When you add a new `this.prisma.<Model>.<method>(...)` call to a service, **every test harness that mocks that service's prisma MUST add the `<Model>` delegate** — otherwise existing tests break with `TypeError: ... is not a function`.

```typescript
// Service gained a new query:
const cfg = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({ ... });

// Test mock MUST add the delegate (returning a behavior-preserving default):
const prisma = {
  // ...existing delegates...
  zclawEnterpriseConversationQuotaConfig: {
    findUnique: async () => ({ quotaMode: null }), // null = non-unlimited → existing behavior
  },
};
```

- **Symptom**: `TypeError: this.prisma.<Model>.<method> is not a function` in tests that previously passed.
- **Cause**: The mock object didn't provide the newly-queried model delegate.
- **Prevention**: When adding a prisma query to a service method, grep the test files that construct that service and add the delegate with a behavior-preserving default (e.g. `quotaMode: null` keeps the non-unlimited path).

### Gotcha: Scheduler 类测试必须清理重调度定时器（否则全量套件挂起）

Service 的 `runOnce()`/`onModuleInit()` 若在 finally 中调用 `scheduleNextRun()`（自重调度模式），
测试直接调用 `runOnce()` 后会残留一个长延时 `setTimeout`（如到次日零点）——**pending timer 会保持
node 事件循环存活**，单文件测试看似通过（runner 结束后退出），但全量 `tsx --test "src/**/*.test.ts"`
在最后永远挂起，直到 CI/脚本超时被杀。

**实证**（!227）：`entitlement-auto-allocate.scheduler.test.ts` 6 处 `runOnce()` 导致全量套件 9 分钟超时；
修复 = 每处调用后 `scheduler.onModuleDestroy()`（置 `destroyed=true` + `clearTimeout`）。

```typescript
// runOnce 的 finally 会重调度（scheduler 源码）：
} finally {
  if (!this.destroyed) {
    this.scheduleNextRun(); // 长延时 setTimeout
  }
}

// 测试必须清理（否则全量套件挂起）：
await (scheduler as any).runOnce();
scheduler.onModuleDestroy(); // destroyed=true + clearTimeout
```

- **Symptom**: 全量套件在最后一个文件处挂起（单文件跑正常），`timeout` 杀进程（exit 124/143）
- **Cause**: runOnce finally 重调度定时器未销毁，pending timer 保持事件循环
- **Detection**: 逐文件 `timeout 40 npx tsx --test <file>` 二分定位 HANG 文件
- **Prevention**: 凡测试触发 service 的 `runOnce`/`onModuleInit`（含 finally 重调度），断言后必须 `onModuleDestroy()` 或等价清理

### Mock with Query Shape Capture

To verify the service sends correct query parameters:

```typescript
test.it('should query by userId and active status', async () => {
  let capturedArgs: any;

  const mockPrisma = {
    entitlement: {
      findMany: async (args: any) => {
        capturedArgs = args;
        return [];
      },
    },
  };

  const service = new EntitlementService(mockPrisma as any);
  await service.listByUser('user-123');

  assert.deepEqual(capturedArgs.where, {
    userId: 'user-123',
    status: 'ACTIVE',
  });
});
```

### Mock with Configurable Return Values

For testing different scenarios:

```typescript
test.it('should throw when plan not found', async () => {
  const mockPrisma = {
    billingPlan: {
      findUnique: async () => null,
    },
  };

  const service = new BillingPlanService(mockPrisma as any);

  await assert.rejects(
    () => service.getPlan('nonexistent'),
    (err: any) => {
      assert.equal(err.code, ErrorCode.INVALID_ARGUMENT);
      return true;
    },
  );
});
```

### Mock for Transaction Testing

Transactions require mocking `$transaction`:

```typescript
test.it('should deduct credits atomically', async () => {
  const mockPrisma = {
    $transaction: async (fn: Function) => {
      // Create a fake tx client
      const fakeTx = {
        entitlement: {
          findFirst: async () => ({
            id: 'ent-1',
            balance: 5000n,
          }),
          updateMany: async (args: any) => ({ count: 1 }),
        },
        creditTransaction: {
          create: async (args: any) => ({ id: 'tx-1' }),
        },
      };
      return fn(fakeTx);
    },
  };

  const service = new EntitlementService(mockPrisma as any);
  const result = await service.deductCredits('user-1', 1000n);

  assert.equal(result.success, true);
});
```

### Mock for Idempotency (P2002 Error)

```typescript
test.it('should return existing record on duplicate idempotency key', async () => {
  let callCount = 0;
  const existingRecord = { id: 'plan-1', name: 'Basic', idempotencyKey: 'key-1' };

  const mockPrisma = {
    billingPlan: {
      create: async () => {
        callCount++;
        const error = new Error() as any;
        error.code = 'P2002';
        error.constructor = { name: 'PrismaClientKnownRequestError' };
        // Simulate PrismaClientKnownRequestError
        throw Object.assign(error, {
          code: 'P2002',
          meta: { target: ['idempotencyKey'] },
        });
      },
      findFirst: async () => existingRecord,
    },
  };

  const service = new BillingPlanService(mockPrisma as any);
  const result = await service.createPlan(
    { name: 'Basic', price: 1000n },
    'key-1',
  );

  assert.equal(result.id, 'plan-1');
  assert.equal(callCount, 1);
});
```

## Assertion Patterns

### Strict Equality

```typescript
assert.equal(actual, expected);        // ===
assert.notEqual(actual, expected);     // !==
```

### Deep Equality

```typescript
assert.deepEqual(actual, expected);    // recursive === for objects/arrays
```

### Exception Testing

```typescript
// For sync functions
assert.throws(
  () => service.validate(input),
  (err: any) => {
    assert.equal(err.code, ErrorCode.INVALID_ARGUMENT);
    return true;  // returning true means the assertion passed
  },
);

// For async functions
await assert.rejects(
  () => service.createPlan(dto),
  (err: any) => {
    assert.equal(err.code, ErrorCode.INSUFFICIENT_CREDITS);
    assert.match(err.message, /余额不足/);
    return true;
  },
);
```

### Truthiness and Type Checks

```typescript
assert.ok(value);                // value is truthy
assert.strictEqual(typeof value, 'bigint');
assert.equal(value, 0n);         // BigInt comparison
```

### Array Assertions

```typescript
assert.equal(results.length, 3);
assert.ok(results.every(r => r.status === 'ACTIVE'));
assert.deepEqual(results.map(r => r.id), ['a', 'b', 'c']);
```

## Test Organization

### File Placement

Test files live alongside source files with `.test.ts` suffix:

```
apps/api/src/billing/
  billing-plan.service.ts
  billing-plan.service.test.ts
  entitlement.service.ts
  entitlement.service.test.ts
```

### Describe Block Naming

```typescript
test.describe('ServiceName', () => {
  test.describe('methodName', () => {
    test.it('should do X when Y', async () => { ... });
    test.it('should throw when Z', async () => { ... });
  });
});
```

### Test Naming Convention

Test descriptions are written in English, following the pattern:

```
should [expected behavior] when [condition]
should throw [error type] when [condition]
```

## What Gets Tested

### Unit-Level (Current Scope)

- Service methods with mocked Prisma
- Query shape verification (what arguments are passed to Prisma)
- Error throwing for edge cases
- Idempotency handling
- Transaction flow logic

### Not Tested (Current Gaps)

- No integration tests (no real database)
- No controller-level tests (no HTTP testing)
- No end-to-end tests
- No middleware/interceptor/filter tests

## Running Tests

```bash
# All tests
cd apps/api && npx tsx --test "src/**/*.test.ts"

# Single test file
cd apps/api && npx tsx --test src/billing/billing-plan.service.test.ts

# Watch mode (not built-in, use external watcher)
cd apps/api && npx tsx watch --test "src/**/*.test.ts"
```

## Tips for Writing Tests

1. **Cast mocks with `as any`** — TypeScript's strict typing will reject partial mocks
2. **Only mock what you use** — Don't create a full PrismaClient mock; only the models and methods the test exercises
3. **Capture query shapes** — The most valuable assertions verify what queries the service sends to Prisma
4. **Test the error paths** — Every `throw new BusinessException(...)` should have a corresponding test
5. **Use `bigint` literals** — When mocking return values for monetary fields, use `1000n` not `1000`
