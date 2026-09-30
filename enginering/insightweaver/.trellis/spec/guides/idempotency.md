# Idempotency

Mutation endpoints (create, purchase, top-up, quota allocation) must be safe against double-submit, browser retries, and network-level replays. The platform uses a client-generated idempotency key pattern validated server-side via database unique constraints.

---

## End-to-End Flow

```
Web: user clicks "Purchase"
  -> Web generates idempotency key: "order-1720000000000-a1b2c3"
    -> Web stores key in component state (survives re-render, not page reload)
      -> Web sends POST /api/billing/orders with header: idempotency-key: order-...
        -> API controller reads header via getIdempotencyKey(headers)
          -> API service attempts INSERT with idempotencyKey as a unique field
            -> Success: row created, 200 returned with order data
            -> Prisma P2002 (unique constraint): duplicate detected
              -> Service queries existing row by idempotencyKey
                -> Returns 200 with existing row data (NOT an error)
      <- Web receives success response, clears pending state
    <- UI shows confirmation
```

---

## Idempotency Key Format

Keys are generated client-side in web pages:

```ts
// Pattern used in web pages (e.g., admin/billing-plans/page.tsx)
const idempotencyKey = `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
```

**Format:** `<scope>-<timestamp>-<random_hex>`

- `scope` is the operation type: `order`, `topup`, `quota_alloc`.
- `timestamp` (`Date.now()`) provides rough ordering and aids debugging.
- `random` (`Math.random().toString(16).slice(2)`) ensures uniqueness across concurrent submissions.

**Example:** `order-1720000000000-a1b2c3d4e5f6`

---

## Web-Side Key Generation

The key is generated at the moment the user initiates the action (button click), not when the component mounts. This ensures:

- Each distinct user action gets a distinct key.
- Refreshing the page generates a new key on next click (correct behavior — a refresh is a new intent).

```ts
// In a React page component
const handlePurchase = async () => {
  const idempotencyKey = `order-${Date.now()}-${Math.random().toString(16).slice(2)}`
  setPending(true)
  try {
    const order = await createBillingOrderApi({
      ...formData,
      idempotencyKey,
    })
    setSuccess(order)
  } catch (err) {
    errorToast(err)
  } finally {
    setPending(false)
  }
}
```

**Do not** persist the idempotency key to localStorage. A page reload after a successful submission should not replay the request.

---

## API-Side Validation

### Header Extraction

The `getIdempotencyKey()` utility reads the header from the request:

```ts
// apps/api/src/utils/ — getIdempotencyKey utility
function getIdempotencyKey(headers: Record<string, string>): string | undefined {
  return headers["idempotency-key"] || headers["Idempotency-Key"]
}
```

Controllers pass the key to service methods:

```ts
// In a controller
@Post()
async createOrder(
  @Body() dto: CreateOrderDto,
  @Headers() headers: Record<string, string>,
) {
  const idempotencyKey = getIdempotencyKey(headers)
  return this.billingService.createOrder(dto, idempotencyKey)
}
```

### Unique Constraint Validation

The service passes the idempotency key as a field in the Prisma create call. The database enforces uniqueness:

```ts
// In a service method
async createOrder(dto: CreateOrderDto, idempotencyKey?: string) {
  try {
    return await this.prisma.billingOrder.create({
      data: {
        enterpriseId: dto.enterpriseId,
        planId: dto.planId,
        amountCents: BigInt(dto.amountCents),
        idempotencyKey: idempotencyKey ?? null,
        // ... other fields
      },
    })
  } catch (err) {
    if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
      // Unique constraint violation = duplicate idempotency key
      const target = (err.meta as any)?.target as string[] | undefined
      if (target?.includes("idempotencyKey")) {
        // Idempotent replay — return existing row
        return this.prisma.billingOrder.findFirst({
          where: { idempotencyKey, isDeleted: false },
        })
      }
      // Different field conflict — throw business exception
      throw new BusinessException(ErrorCode.BUSINESS_CONFLICT)
    }
    throw err
  }
}
```

### P2002 Handling Rules

1. **P2002 on `idempotencyKey`**: This is expected. Query the existing row and return it as a success response. Do NOT throw an error.
2. **P2002 on any other field**: This is a real business logic conflict (e.g., duplicate enterprise name). Throw a `BusinessException` with the appropriate error code.
3. **Distinguishing the two**: Check `err.meta?.target` — Prisma populates this with the field(s) that violated the constraint. Only treat it as idempotent if `target` includes `idempotencyKey`.

---

## Schema Requirements

Any model that supports idempotent creation must have:

```prisma
model BillingOrder {
  // ... other fields
  idempotencyKey String?  @unique  // nullable, unique when present

  @@map("billing_orders")
}
```

- `String?` (nullable): Not all creates go through the idempotency path. Internal/system creates omit the key.
- `@unique`: The database-level constraint that makes P2002 possible.
- Only one `@unique` idempotency key per model. If you need composite idempotency (e.g., unique per enterprise + key), use `@@unique([enterpriseId, idempotencyKey])`.

---

## Which Endpoints Need Idempotency

| Endpoint Type | Idempotency Key? | Reason |
|---|---|---|
| Create billing order | Yes | Double-charge risk |
| Quota top-up | Yes | Double-credit risk |
| Quota allocation to member | Yes | Double-allocation risk |
| Update enterprise settings | No | PUT is naturally idempotent |
| Create chat session | No | Duplicate sessions are harmless |
| Send chat message | No | Message dedup is handled by session ordering |

**Rule of thumb:** If the operation transfers value (money, tokens, quota), it needs an idempotency key. If it just creates a container or reads data, it does not.

---

## Testing Idempotency

### API Unit Test

```ts
import test from "node:test"
import { strict as assert } from "node:assert"

test("returns the same order for the same idempotency key", async () => {
  let callCount = 0
  const fakePrisma = {
    billingOrder: {
      create: async (args: any) => {
        callCount++
        if (callCount === 1) return { id: "order_1", ...args.data }
        // Simulate P2002 on second call
        const err = new Error("Unique constraint") as any
        err.code = "P2002"
        err.meta = { target: ["idempotencyKey"] }
        throw err
      },
      findFirst: async () => ({ id: "order_1", idempotencyKey: "idem_test" }),
    },
  }

  const service = new BillingService(fakePrisma as any)
  const first = await service.createOrder(dto, "idem_test")
  const second = await service.createOrder(dto, "idem_test")
  assert.equal(first.id, second.id)
})
```

### Web Unit Test

Test that the idempotency key generation:
- Contains the scope prefix
- Includes a timestamp
- Produces unique values across 1000 consecutive calls (no collisions)

---

## Common Mistakes

1. **Generating the key at component mount instead of action time.** This causes the same key to be reused if the user clicks "Purchase" twice without navigating away. Generate at click time.

2. **Returning an error on P2002 for idempotencyKey.** The duplicate is the entire point — return the existing row as a success, not a 409 conflict.

3. **Storing the key in localStorage.** A page reload should not replay a submitted order. Keep the key in React state only.

4. **Omitting `target` check in P2002 handler.** A P2002 on a different unique field (e.g., `name`) is a real conflict, not an idempotent replay. Always check which field triggered the violation.

5. **Using the same scope for different operations.** An `order-*` key and a `topup-*` key will never collide because of the scope segment. But if both used `generic-*`, a top-up could accidentally replay an order. Use distinct scopes.
