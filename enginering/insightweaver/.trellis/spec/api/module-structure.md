# NestJS Module Organization

## Root Module

All feature modules are registered in `apps/api/src/app.module.ts`. The root module serves as the composition root — it imports every feature module but contains no business logic itself.

```typescript
// apps/api/src/app.module.ts
@Module({
  imports: [
    DatabaseModule,
    RedisModule,
    CommonModule,
    AuthModule,
    BillingModule,
    EnterpriseModule,
    ZclawModule,
    SkillModule,
    AgentModule,
    AgentManagementModule,
    ResearchModule,
    AttachmentModule,
    CreditsModule,
    DashboardModule,
    AdminUsersModule,
    McpModule,
    WechatPayModule,
    HealthModule,
  ],
})
export class AppModule {}
```

## Module Composition

Each module follows the standard NestJS `@Module` decorator pattern with four properties:

```typescript
@Module({
  imports: [forwardRef(() => WechatPayModule)],  // cross-module deps
  controllers: [BillingPlanController],
  providers: [BillingPlanService],
  exports: [BillingPlanService],                  // expose to other modules
})
export class BillingModule {}
```

- **imports:** Other modules whose exported providers are needed
- **controllers:** Route handlers for HTTP endpoints
- **providers:** Services, repositories, and other injectables
- **exports:** Providers made available to importing modules

## File Naming Convention

All files use **kebab-case**:

| Pattern | Example |
|---------|---------|
| Module | `billing.module.ts` |
| Controller | `billing-plan.controller.ts` |
| Service | `billing-plan.service.ts` |
| DTO | `create-billing-plan.dto.ts` |
| Guard | `jwt-auth.guard.ts` |
| Filter | `all-exceptions.filter.ts` |
| Interceptor | `logging.interceptor.ts` |

## Class Naming Convention

All classes use **PascalCase** with a type suffix:

| Type | Suffix | Example |
|------|--------|---------|
| Module | `Module` | `BillingModule` |
| Controller | `Controller` | `BillingPlanController` |
| Service | `Service` | `BillingPlanService` |
| DTO | `Dto` | `CreateBillingPlanDto` |
| Guard | `Guard` | `JwtAuthGuard` |
| Filter | `Filter` | `AllExceptionsFilter` |
| Interceptor | `Interceptor` | `LoggingInterceptor` |

## Dependency Injection Patterns

### String Token Injection (Prisma)

Prisma is injected using a string token rather than a class token. This is the canonical pattern throughout the codebase:

```typescript
// apps/api/src/billing/billing-plan.service.ts
@Injectable()
export class BillingPlanService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
  ) {}
}
```

The `DatabaseModule` provides this token:

```typescript
// apps/api/src/database/database.module.ts
providers: [
  {
    provide: 'PrismaClient',
    useFactory: () => new PrismaClient(),
  },
],
exports: ['PrismaClient'],
```

### Optional Injection for Loose Coupling

When a service has a non-critical dependency (e.g., a feature that may not be available in all environments), use `@Optional()`:

```typescript
@Injectable()
export class BillingService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    @Optional() private readonly wechatPayService?: WechatPayService,
  ) {}
}
```

This allows the module to function even when the optional dependency's module is not imported.

## Cross-Module Dependencies with forwardRef

When two modules depend on each other (circular dependency), use `forwardRef`:

```typescript
// apps/api/src/billing/billing.module.ts
@Module({
  imports: [forwardRef(() => WechatPayModule)],
  providers: [BillingService],
})
export class BillingModule {}

// apps/api/src/wechat-pay/wechat-pay.module.ts
@Module({
  imports: [forwardRef(() => BillingModule)],
  providers: [WechatPayService],
})
export class WechatPayModule {}
```

Both sides must use `forwardRef` and inject with `@Inject(forwardRef(() => ServiceName))`.

**Known circular dependency:** `BillingModule` <-> `WechatPayModule` (payment processing requires billing context, billing needs payment status).

## Directory Structure

Each module lives in its own directory under `apps/api/src/`:

```
apps/api/src/
  app.module.ts
  main.ts
  auth/
    auth.module.ts
    jwt-auth.guard.ts
    optional-jwt-auth.guard.ts
  billing/
    billing.module.ts
    billing-plan.controller.ts
    billing-plan.service.ts
    entitlement.service.ts
    dto/
  common/
    app-logger.service.ts
    constants/
      error-codes.ts
    filters/
      all-exceptions.filter.ts
    interceptors/
      logging.interceptor.ts
      response.interceptor.ts
```

## Module Responsibility Boundaries

| Module | Responsibility |
|--------|---------------|
| DatabaseModule | Prisma client lifecycle, `'PrismaClient'` token |
| RedisModule | Redis connection, caching |
| CommonModule | Logger, request context, shared utilities |
| AuthModule | JWT guards, authentication strategies |
| BillingModule | Plans, entitlements, usage tracking |
| EnterpriseModule | Organization management |
| WechatPayModule | WeChat Pay integration, webhook handling |
| HealthModule | Health check endpoints |
