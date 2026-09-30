# Database Access

## Prisma Client Injection

The Prisma client is provided as a singleton through the `DatabaseModule` and injected via a string token. This is the universal pattern across all services.

### Provider Registration

```typescript
// apps/api/src/database/database.module.ts
import { Module } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Module({
  providers: [
    {
      provide: 'PrismaClient',
      useFactory: () => new PrismaClient(),
    },
  ],
  exports: ['PrismaClient'],
})
export class DatabaseModule {}
```

### Service Injection

```typescript
// Any service file
import { Inject, Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class BillingPlanService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
  ) {}
}
```

### Why String Token

Using `@Inject('PrismaClient')` instead of `@Inject(PrismaClient)` allows:
1. The factory to control client lifecycle (singleton)
2. Easy substitution in tests with mock objects
3. Avoidance of circular import issues between `@prisma/client` types and NestJS DI

## Singleton Access

The Prisma client is instantiated once via `useFactory` in `DatabaseModule`. Every service that injects `'PrismaClient'` receives the same instance. This is critical because:

- Prisma's connection pool is managed per-client instance
- Multiple instances would create multiple connection pools
- The `$transaction` method relies on a single client for connection management

## Transaction Client Typing

Prisma's interactive transactions pass a transaction client as the callback argument. The codebase defines type aliases for readability:

### Type Alias Pattern

```typescript
// apps/api/src/billing/entitlement.service.ts
import { Prisma } from '@prisma/client';

// Module-specific alias
type EntitlementTx = Prisma.TransactionClient;

// Usage
async deductCredits(userId: string, amount: bigint) {
  return this.prisma.$transaction(async (tx: EntitlementTx) => {
    // tx has the same API as this.prisma
    const record = await tx.entitlement.findFirst({ ... });
    await tx.entitlement.updateMany({ ... });
  });
}
```

### Available Operations on tx

The `Prisma.TransactionClient` type exposes the same model accessors as `PrismaClient`:

```typescript
tx.entitlement.findFirst(...)
tx.entitlement.findUnique(...)
tx.entitlement.findMany(...)
tx.entitlement.create(...)
tx.entitlement.update(...)
tx.entitlement.updateMany(...)
tx.entitlement.delete(...)
tx.entitlement.deleteMany(...)
tx.entitlement.upsert(...)
tx.entitlement.count(...)

// Raw queries
tx.$queryRaw(...)
tx.$executeRaw(...)
```

**Not available on tx:** `$connect`, `$disconnect`, `$on`, `$transaction`, `$use` (middleware). These are client-level operations.

### Transaction Options

```typescript
// Default: 5 second timeout, ReadCommitted isolation
await this.prisma.$transaction(async (tx) => { ... });

// Custom timeout and isolation level
await this.prisma.$transaction(
  async (tx) => { ... },
  {
    maxWait: 5000,           // max ms to wait for transaction to start
    timeout: 10000,          // max ms for the transaction to complete
    isolationLevel: 'Serializable',  // for strict consistency
  },
);
```

## Raw SQL Queries

For operations that Prisma's query builder cannot express efficiently (row locking, complex joins, bulk operations), use raw SQL.

### Tagged Template Syntax (Preferred)

```typescript
// Parameterized automatically — safe from SQL injection
const entitlements = await tx.$queryRaw`
  SELECT id, user_id, balance, token_balance
  FROM entitlement
  WHERE user_id = ${userId}
    AND status = 'ACTIVE'
  FOR UPDATE
`;
```

### String Syntax (Avoid)

```typescript
// Only when dynamic SQL is needed — use Prisma.sql for parameterization
import { Prisma } from '@prisma/client';

const conditions = Prisma.sql`user_id = ${userId}`;
const results = await tx.$queryRaw`
  SELECT * FROM entitlement WHERE ${conditions}
`;
```

### Row Locking with FOR UPDATE

Critical for preventing race conditions in read-then-update patterns:

```typescript
async function deductWithLock(tx: EntitlementTx, userId: string, amount: bigint) {
  // Lock the row — other transactions will wait
  const [entitlement] = await tx.$queryRaw`
    SELECT * FROM entitlement
    WHERE user_id = ${userId} AND status = 'ACTIVE'
    FOR UPDATE
  `;

  if (!entitlement || entitlement.balance < amount) {
    throw new BusinessException(ErrorCode.INSUFFICIENT_CREDITS, '余额不足');
  }

  // Safe to update — row is locked
  await tx.$executeRaw`
    UPDATE entitlement
    SET balance = balance - ${amount}
    WHERE id = ${entitlement.id}
  `;
}
```

### $queryRaw vs $executeRaw

| Method | Returns | Use For |
|--------|---------|---------|
| `$queryRaw` | Array of result rows | SELECT queries |
| `$executeRaw` | Number of affected rows | INSERT, UPDATE, DELETE |

### Type Casting Raw Results

Raw queries return untyped objects. Cast explicitly:

```typescript
interface EntitlementRow {
  id: string;
  user_id: string;
  balance: bigint;
  token_balance: bigint;
}

const rows = await tx.$queryRaw`
  SELECT id, user_id, balance, token_balance
  FROM entitlement
  WHERE user_id = ${userId}
` as EntitlementRow[];
```

## Common Query Patterns

### Find with Conditions

```typescript
const activeEntitlements = await this.prisma.entitlement.findMany({
  where: {
    userId,
    status: 'ACTIVE',
    expiresAt: { gt: new Date() },
  },
  include: {
    billingPlan: true,  // join related model
  },
  orderBy: { createdAt: 'desc' },
  take: 20,
  skip: 0,
});
```

### Upsert (Create or Update)

```typescript
await this.prisma.userProfile.upsert({
  where: { userId },
  create: { userId, name, email },
  update: { name, email },
});
```

### Batch Operations

```typescript
// Update multiple records
await this.prisma.entitlement.updateMany({
  where: { enterpriseId, status: 'ACTIVE' },
  data: { status: 'SUSPENDED' },
});

// Delete multiple records
await this.prisma.creditTransaction.deleteMany({
  where: {
    createdAt: { lt: retentionDate },
  },
});
```

### Aggregation

```typescript
const stats = await this.prisma.creditTransaction.aggregate({
  where: { userId, createdAt: { gte: startDate } },
  _sum: { amount: true },
  _count: true,
  _avg: { amount: true },
});
```

## BigInt in Database Operations

All monetary/token/byte fields use `BigInt` in both TypeScript and Prisma schema:

```typescript
// In service code
const amount = 100000n;  // BigInt literal

await this.prisma.entitlement.create({
  data: {
    userId,
    balance: amount,       // BigInt
    tokenBalance: 0n,      // BigInt literal
    byteQuota: 1073741824n,  // 1 GB in bytes
  },
});

// Comparisons
const sufficient = entitlement.balance >= amount;  // BigInt comparison

// Arithmetic
const newBalance = entitlement.balance - amount;  // BigInt arithmetic
```

## Schema Location

The Prisma schema file is at `apps/api/prisma/schema.prisma`. Generated client types are at `apps/api/node_modules/.prisma/client/`.
