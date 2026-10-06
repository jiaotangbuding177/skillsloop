import {
  CallHandler,
  ExecutionContext,
  Inject,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import type { PrismaClient } from '@prisma/client';
import { Observable, from } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { EnterpriseService } from '../../enterprises/enterprise.service.js';
import { readEnterpriseId } from '../zclaw-enterprise-id.util.js';
import { ZclawKmAgentClient } from '../zclaw-km-agent.client.js';

@Injectable()
export class ZclawEnterpriseContextInterceptor implements NestInterceptor {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseService: EnterpriseService,
    private readonly kmAgentClient: ZclawKmAgentClient,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const req = context.switchToHttp().getRequest();
    const userId = req?.user?.userId as string | undefined;
    const enterpriseId = readEnterpriseId(req);
    if (!userId) {
      return next.handle();
    }
    if (this.isConsumerAccessRoute(req)) {
      return next.handle();
    }

    if (enterpriseId && (this.isSharedWorkspaceRoute(req) || this.isSharedWorkspaceRagflowRoute(req))) {
      return this.runWithSharedWorkspaceTarget(userId, enterpriseId, next);
    }

    if (this.isRagflowGraphRoute(req)) {
      return from(this.isPlatformAdmin(userId)).pipe(
        mergeMap((isPlatformAdmin) =>
          isPlatformAdmin
            ? this.toObservable(next.handle())
            : this.runWithEnterpriseTarget(userId, enterpriseId, next),
        ),
      );
    }

    return this.runWithEnterpriseTarget(userId, enterpriseId, next);
  }

  private runWithSharedWorkspaceTarget(userId: string, enterpriseId: string, next: CallHandler) {
    return from(this.enterpriseService.resolveSharedWorkspaceTargetForUser(userId, enterpriseId)).pipe(
      mergeMap((target) => this.kmAgentClient.runWithTarget(target, () => this.toPromise(next.handle()))),
    );
  }

  private runWithEnterpriseTarget(userId: string, enterpriseId: string | null | undefined, next: CallHandler) {
    return from(this.enterpriseService.resolveZclawTargetForUser(userId, enterpriseId)).pipe(
      mergeMap((target) => this.kmAgentClient.runWithTarget(target, () => this.toPromise(next.handle()))),
    );
  }

  private async isPlatformAdmin(userId: string) {
    const user = await this.prisma.user.findFirst({
      where: { id: userId, isDeleted: false },
      select: { role: true },
    });
    return user?.role === 'admin';
  }

  private isRagflowGraphRoute(req: { path?: string; url?: string; originalUrl?: string }) {
    const path = req.path ?? req.originalUrl ?? req.url ?? '';
    return /\/ragflow\/graph(?:\/|$|\?)/.test(path);
  }

  private isSharedWorkspaceRoute(req: { path?: string; url?: string; originalUrl?: string }) {
    const path = req.path ?? req.originalUrl ?? req.url ?? '';
    return /\/shared-workspace(?:\/|$|\?)/.test(path);
  }

  private isConsumerAccessRoute(req: {
    path?: string;
    url?: string;
    originalUrl?: string;
    headers?: Record<string, unknown>;
    query?: Record<string, unknown>;
    body?: Record<string, unknown>;
  }) {
    const path = req.path ?? req.originalUrl ?? req.url ?? '';
    if (/\/zclaw\/status(?:\/|$|\?)/.test(path)) {
      return !readEnterpriseId(req);
    }
    return /\/zclaw\/(?:access-request\/me|access-requests|provision)(?:\/|$|\?)/.test(path);
  }

  private isSharedWorkspaceRagflowRoute(req: {
    path?: string;
    url?: string;
    originalUrl?: string;
    query?: Record<string, unknown>;
    body?: Record<string, unknown>;
  }) {
    const path = req.path ?? req.originalUrl ?? req.url ?? '';
    if (!/\/ragflow(?:\/|$|\?)/.test(path)) {
      return false;
    }
    const source = this.readString(req.query?.source) ?? this.readString(req.body?.source);
    const scope = this.readString(req.query?.scope) ?? this.readString(req.body?.scope);
    return source === 'shared-workspace' || scope === 'enterprise';
  }

  private readString(value: unknown) {
    return typeof value === 'string' ? value : undefined;
  }

  private toObservable(stream: Observable<unknown>) {
    return stream;
  }

  private async toPromise(stream: Observable<unknown>) {
    return await new Promise<unknown>((resolve, reject) => {
      let latest: unknown;
      stream.subscribe({
        next: (value) => {
          latest = value;
        },
        error: reject,
        complete: () => resolve(latest),
      });
    });
  }

}
